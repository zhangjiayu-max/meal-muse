"""AI 调用统一封装 — 通义千问 + fallback"""

import httpx
from app.config import get_settings

settings = get_settings()

API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DEFAULT_MODEL = "qwen-plus"
DEFAULT_MAX_TOKENS = 1500
DEFAULT_TEMPERATURE = 0.7


async def call_ai(
    messages: list[dict],
    *,
    model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    system_prompt: str | None = None,
) -> tuple[str, int]:
    """
    调用通义千问 API。

    Args:
        messages: 对话消息列表 [{"role": "user/assistant", "content": "..."}]
        model: 模型名称，默认 qwen-plus
        max_tokens: 最大输出 token
        temperature: 生成温度
        system_prompt: 系统提示词（会插入到 messages 最前面）

    Returns:
        (content, tokens_used) — tokens 为 0 表示使用了 fallback
    """
    api_key = settings.DASHSCOPE_API_KEY

    # 无 API Key → fallback
    if not api_key:
        last_msg = messages[-1]["content"] if messages else ""
        return _builtin_response(last_msg), 0

    # 组装完整消息
    full_messages: list[dict] = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model or DEFAULT_MODEL,
                    "messages": full_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", 0)
            return content, tokens
    except Exception:
        last_msg = messages[-1]["content"] if messages else ""
        return _builtin_response(last_msg), 0


async def call_ai_structured(
    prompt: str,
    system_prompt: str,
    *,
    model: str | None = None,
    temperature: float = 0.3,
) -> str:
    """
    调用 AI 并要求返回结构化 JSON。
    在 system_prompt 中明确要求 JSON 格式。
    """
    messages = [{"role": "user", "content": prompt}]
    return (await call_ai(messages, system_prompt=system_prompt, model=model, temperature=temperature))[0]


def _builtin_response(question: str) -> str:
    """内置回复（无 API Key 时使用）"""
    q = question.lower()
    if "备孕" in q:
        return (
            "备孕期间饮食建议：\n\n"
            "🥗 重点营养素：\n"
            "• 叶酸：每天 400μg（菠菜、芦笋、豆类）\n"
            "• 铁：每天 20mg（红肉、猪肝、黑木耳）\n"
            "• DHA：每周吃 2-3 次深海鱼\n\n"
            "🍎 推荐水果：牛油果、蓝莓、猕猴桃\n"
            "⚠️ 避免：酒精、咖啡因过量、生冷食物"
        )
    if "经期" in q or "生理期" in q:
        return (
            "经期饮食建议：\n\n"
            "🌡️ 月经期：温补驱寒（红糖姜茶、当归羊肉汤），补铁（猪肝、菠菜）\n"
            "🌱 卵泡期：高蛋白（鸡蛋、鱼），深色食物（黑芝麻、黑豆）\n"
            "🥚 排卵期：促排卵（黑豆豆浆、坚果）\n"
            "😌 黄体期：缓解PMS（香蕉、燕麦、坚果）"
        )
    if "减肥" in q or "减脂" in q:
        return (
            "减脂饮食建议：\n\n"
            "📊 热量控制：每日热量缺口 300-500kcal\n"
            "🥗 饮食原则：\n"
            "• 高蛋白：每餐保证优质蛋白\n"
            "• 低GI主食：糙米、燕麦、红薯\n"
            "• 多蔬菜：每天 500g 以上\n"
            "• 少油少盐：烹饪方式以蒸煮为主\n\n"
            "⏰ 进食时间：晚餐尽量在 19:00 前完成"
        )
    return (
        "你好！我是你的 AI 饮食助手 🌿\n\n"
        "我可以帮你：\n"
        "• 📝 分析你的饮食记录\n"
        "• 🍽️ 推荐适合你的餐食\n"
        "• 🎯 根据你的目标给出建议\n"
        "• 🌿 结合时令推荐食材\n\n"
        "有什么想问的吗？"
    )
