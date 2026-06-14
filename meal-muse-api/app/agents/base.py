"""Agent 基类 — 所有 LLM 交互必须通过 Agent"""

import uuid
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import call_ai, call_ai_structured
from app.services.knowledge_service import search_knowledge

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Agent 响应"""
    content: str
    model_used: str = ""
    tokens_used: int = 0
    knowledge_used: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class PromptTemplate:
    """Prompt 模板 — 集中管理所有 Prompt"""
    system: str
    user_template: str  # 支持 {variable} 占位符
    description: str = ""
    version: str = "1.0"
    tags: list[str] = field(default_factory=list)


class PromptRegistry:
    """Prompt 注册表 — 集中管理所有 Agent 的 Prompt"""

    _prompts: dict[str, PromptTemplate] = {}

    @classmethod
    def register(cls, name: str, template: PromptTemplate):
        """注册 Prompt 模板"""
        cls._prompts[name] = template
        logger.info(f"Registered prompt: {name} (v{template.version})")

    @classmethod
    def get(cls, name: str) -> PromptTemplate | None:
        """获取 Prompt 模板"""
        return cls._prompts.get(name)

    @classmethod
    def list_all(cls) -> dict[str, PromptTemplate]:
        """列出所有注册的 Prompt"""
        return cls._prompts.copy()


class BaseAgent(ABC):
    """Agent 基类 — 所有 LLM 交互必须继承此类"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")

    @abstractmethod
    def get_prompt_name(self) -> str:
        """返回使用的 Prompt 名称"""
        pass

    async def get_knowledge_context(
        self,
        query: str,
        top_k: int = 3,
    ) -> tuple[str, list[dict]]:
        """检索知识库，返回上下文和命中的知识列表"""
        try:
            knowledge = await search_knowledge(query, top_k=top_k)
            if not knowledge:
                return "", []

            context_parts = ["【参考知识】"]
            for k in knowledge:
                source = k.get("source", "未知来源")
                content = k.get("content", "")
                context_parts.append(f"- {content}（来源：{source}）")

            return "\n".join(context_parts), knowledge
        except Exception as e:
            self.logger.warning(f"知识库检索失败: {e}")
            return "", []

    def format_prompt(self, **kwargs) -> tuple[str, str]:
        """格式化 Prompt 模板，返回 (system, user)"""
        template = PromptRegistry.get(self.get_prompt_name())
        if not template:
            raise ValueError(f"Prompt '{self.get_prompt_name()}' not registered")

        system = template.system
        user = template.user_template.format(**kwargs)
        return system, user

    async def run(
        self,
        db: AsyncSession,
        user_context: str = "",
        knowledge_query: str = "",
        **kwargs,
    ) -> AgentResponse:
        """执行 Agent"""
        # 1. 获取知识库上下文
        knowledge_context, knowledge_used = "", []
        if knowledge_query:
            knowledge_context, knowledge_used = await self.get_knowledge_context(knowledge_query)

        # 2. 格式化 Prompt
        system, user = self.format_prompt(
            user_context=user_context,
            knowledge_context=knowledge_context,
            **kwargs,
        )

        # 3. 调用 LLM
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        response, tokens = await call_ai(messages)

        # 4. 记录日志
        self.logger.info(
            f"Agent {self.agent_name}: tokens={tokens}, "
            f"knowledge={len(knowledge_used)} items"
        )

        return AgentResponse(
            content=response,
            model_used="qwen-plus",
            tokens_used=tokens,
            knowledge_used=knowledge_used,
            metadata={"agent": self.agent_name},
        )

    async def run_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs,
    ) -> str:
        """调用结构化输出（用于 JSON 解析等场景）"""
        return await call_ai_structured(
            prompt=prompt,
            system_prompt=system_prompt or f"你是 {self.agent_name} 专家。",
        )
