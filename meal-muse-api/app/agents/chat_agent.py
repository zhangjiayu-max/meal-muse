"""对话 Agent — AI 营养师对话"""

import re
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.agents.base import BaseAgent, AgentResponse, PromptTemplate, PromptRegistry
from app.models.ai_chat_message import AiChatMessage
from app.models.user import User

# ===== Prompt 注册 =====

CHAT_SYSTEM_PROMPT = """你是 MealMuse，一个专业的 AI 饮食健康助手。

你的职责：
1. 基于用户的饮食记录，提供个性化的饮食建议
2. 回答健康饮食相关问题（减肥/备孕/养生/经期饮食等）
3. 帮助用户达成健康目标
4. 结合中医食疗和现代营养学知识回答问题

重要规则：
1. 只提供饮食和营养相关建议，不提供医疗诊断
2. 如果用户询问医疗问题，建议咨询专业医生
3. 建议要具体、可执行，避免空泛
4. 语气友好、鼓励，像一个贴心的健康伙伴
5. 回复用中文，简洁明了，适当使用 emoji
6. 如果用户有过敏原或疾病禁忌，必须提醒并避免推荐相关食物
7. 回答中医相关问题时，可以引用食疗知识，但要说明这是食疗建议而非医疗诊断
8. 你可以在回复中触发以下 Action（用特殊标记包裹）：
   - 记录饮食：[ACTION:DIET_RECORD]早餐：牛奶250ml+全麦面包2片+鸡蛋1个[/ACTION]
   - 关联餐食计划：[ACTION:MEAL_LINK]2026-06-14 早餐[/ACTION]
   - 更新用户画像：[ACTION:PROFILE_UPDATE]constitution_types=阳虚质,yin_deficiency[/ACTION]
   注意：Action 标记只在你的回复中出现，前端会解析并执行。不要解释 Action 标记本身。

{knowledge_context}

{user_context}"""

CHAT_USER_TEMPLATE = """用户问题：{user_message}

请基于用户信息和知识库内容，给出专业、个性化的回答。"""

# 注册 Prompt
PromptRegistry.register(
    "chat",
    PromptTemplate(
        system=CHAT_SYSTEM_PROMPT,
        user_template=CHAT_USER_TEMPLATE,
        description="AI 营养师对话 Prompt",
        version="2.0",
        tags=["chat", "nutrition", "tcm"],
    ),
)


class ChatAgent(BaseAgent):
    """对话 Agent"""

    MAX_HISTORY_MESSAGES = 20

    def __init__(self):
        super().__init__("chat")

    def get_prompt_name(self) -> str:
        return "chat"

    async def generate_summary(self, messages: list[dict]) -> str:
        """将旧消息生成为紧凑摘要"""
        from app.services.ai_service import call_ai

        conversation_text = "\n".join(
            f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
            for m in messages
        )

        summary_prompt = f"""请将以下对话历史压缩为一段紧凑摘要(100-150字)，保留关键信息：
- 用户的核心需求和问题
- AI 给出的关键建议
- 用户画像相关信息(饮食偏好、健康目标等)
- 未解决的问题

对话历史：
{conversation_text}

摘要："""

        summary, _ = await call_ai(
            [{"role": "user", "content": summary_prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        return summary.strip()

    async def load_history(
        self,
        db: AsyncSession,
        user_id: str,
        session_id: uuid.UUID,
    ) -> list[dict]:
        """加载历史对话消息"""
        result = await db.execute(
            select(AiChatMessage)
            .where(
                AiChatMessage.user_id == user_id,
                AiChatMessage.session_id == session_id,
            )
            .order_by(desc(AiChatMessage.created_at))
            .limit(200)
        )
        messages = list(reversed(result.scalars().all()))
        return [{"role": m.role, "content": m.content} for m in messages]

    async def chat(
        self,
        db: AsyncSession,
        user: User,
        user_message: str,
        session_id: uuid.UUID | None = None,
        user_context: str = "",
        profile_data: dict | None = None,
    ) -> dict:
        """执行对话"""
        session_id = session_id or uuid.uuid4()

        # 1. 检索知识库
        knowledge_context, knowledge_used = await self.get_knowledge_context(
            user_message, top_k=3
        )

        # 2. 格式化 Prompt
        system, _ = self.format_prompt(
            user_context=user_context,
            knowledge_context=knowledge_context,
            user_message=user_message,
        )

        # 3. 加载历史对话
        history = await self.load_history(db, user.id, session_id)

        # 如果历史超过 MAX_HISTORY_MESSAGES 条，生成前情摘要
        if len(history) > self.MAX_HISTORY_MESSAGES:
            old_messages = history[:-self.MAX_HISTORY_MESSAGES]
            recent_messages = history[-self.MAX_HISTORY_MESSAGES:]

            # 生成摘要
            summary = await self.generate_summary(old_messages)

            # 将摘要作为 system 消息注入
            history = [
                {"role": "system", "content": f"[前情摘要] {summary}"}
            ] + recent_messages

        # 4. 组装消息
        messages = [{"role": "system", "content": system}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        # MCP 意图检测
        from app.mcp.router import get_mcp_router
        mcp_router = get_mcp_router()
        mcp_results = await mcp_router.route(user_message, context={
            "diet_type": profile_data.get("diet_type") if profile_data else None,
            "allergies": profile_data.get("allergies") if profile_data else None,
        })

        if mcp_results:
            # 将 MCP 结果作为额外上下文注入
            mcp_context = "\n\n外部知识库查询结果：\n"
            for r in mcp_results:
                mcp_context += f"- {r['tool']}: {r['query']} → {r['results']}\n"
            # 添加到 messages 中
            messages.append({"role": "system", "content": mcp_context})

        # 5. 调用 LLM
        from app.services.ai_service import call_ai
        response, tokens = await call_ai(messages)

        # 6. 解析 AI 回复中的 Action
        actions = []
        action_pattern = r'\[ACTION:(\w+)\](.*?)\[/ACTION\]'
        action_matches = re.findall(action_pattern, response)

        for action_type, action_data in action_matches:
            actions.append({"type": action_type, "data": action_data.strip()})

        # 从回复中移除 Action 标记（用户不需要看到）
        clean_response = re.sub(action_pattern, '', response).strip()

        # 7. 保存消息
        user_msg = AiChatMessage(
            user_id=user.id,
            session_id=session_id,
            role="user",
            content=user_message,
        )
        db.add(user_msg)

        from app.config import get_settings
        settings = get_settings()
        cfg = settings.AI_PROVIDERS.get(settings.AI_PROVIDER, {})
        model_used = f"{settings.AI_PROVIDER}:{cfg.get('default_model', 'builtin')}" if cfg.get("api_key") else "builtin"

        ai_msg = AiChatMessage(
            user_id=user.id,
            session_id=session_id,
            role="assistant",
            content=response,  # 保存原始内容（含 Action 标记）
            model_used=model_used,
            tokens_used=tokens,
        )
        db.add(ai_msg)
        await db.commit()

        self.logger.info(
            f"Chat session={session_id}: user_msg saved, "
            f"AI response saved ({tokens} tokens), "
            f"knowledge={len(knowledge_used)} items"
        )

        return {
            "id": ai_msg.id,
            "role": "assistant",
            "content": clean_response,
            "actions": actions,
            "session_id": session_id,
            "model_used": model_used,
            "tokens_used": tokens,
            "created_at": ai_msg.created_at,
        }
