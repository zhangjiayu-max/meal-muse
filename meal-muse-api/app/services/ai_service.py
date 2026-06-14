"""AI 调用统一封装 — 多模型支持 + 重试 + fallback

默认使用通义千问 (DashScope)，可在 .env 中切换为小米/OpenAI/自定义。
所有提供商需支持 OpenAI 兼容的 /v1/chat/completions 接口。
"""

import asyncio
import time
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 1500
DEFAULT_TEMPERATURE = 0.7
MAX_RETRIES = 2
RETRY_DELAYS = [1, 3]


def _get_provider_config(provider: str | None = None) -> dict | None:
    """获取指定提供商的配置，如果未指定则使用当前默认提供商"""
    settings = get_settings()
    provider = provider or settings.AI_PROVIDER
    providers = settings.AI_PROVIDERS
    cfg = providers.get(provider)
    if not cfg:
        logger.warning(f"未知 AI 提供商 '{provider}'，回退到 dashscope")
        cfg = providers.get("dashscope")
    return cfg


async def call_ai(
    messages: list[dict],
    *,
    model: str | None = None,
    provider: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    system_prompt: str | None = None,
) -> tuple[str, int]:
    """
    调用 AI API（支持多模型，含重试机制）。

    Args:
        messages: 对话消息 [{"role": "user/assistant", "content": "..."}]
        model: 模型名称，默认自动选择
        provider: AI 提供商（dashscope/xiaomi/openai/custom），默认使用 AI_PROVIDER
        max_tokens: 最大输出 token
        temperature: 生成温度
        system_prompt: 系统提示词

    Returns:
        (content, tokens_used) — tokens 为 0 表示使用了 fallback
    """
    cfg = _get_provider_config(provider)
    if not cfg:
        raise ValueError(f"未找到可用的 AI 提供商配置")

    api_key = cfg["api_key"]
    api_url = cfg["api_url"]

    # 无 API Key → fallback
    if not api_key:
        logger.warning(f"AI 提供商 '{cfg['name']}' 未配置 API Key，使用内置回复")
        last_msg = messages[-1]["content"] if messages else ""
        return _builtin_response(last_msg), 0

    # 自动选模型
    if model is None:
        model = _select_model(messages, provider)

    # 组装完整消息
    full_messages: list[dict] = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            start = time.time()
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": full_messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )
            elapsed_ms = (time.time() - start) * 1000

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "5"))
                logger.warning(
                    f"AI API 限流 (429)，等待 {retry_after}s 后重试"
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(retry_after)
                    continue
                raise Exception("AI API 限流")

            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", 0)

            logger.info(
                f"AI call success: provider={cfg['name']}, model={model}, "
                f"tokens={tokens}, time={elapsed_ms:.0f}ms, attempt={attempt + 1}"
            )
            return content, tokens

        except Exception as e:
            last_error = e
            logger.warning(
                f"AI call failed (attempt {attempt + 1}/{MAX_RETRIES + 1}): {e}"
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAYS[attempt])

    logger.error(
        f"AI call exhausted retries: provider={cfg['name']}, model={model}, error={last_error}"
    )
    last_msg = messages[-1]["content"] if messages else ""
    return _builtin_response(last_msg), 0


async def call_ai_structured(
    prompt: str,
    system_prompt: str,
    *,
    model: str | None = None,
    provider: str | None = None,
    temperature: float = 0.3,
) -> str:
    """调用 AI 并要求返回结构化 JSON"""
    messages = [{"role": "user", "content": prompt}]
    return (
        await call_ai(
            messages,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            temperature=temperature,
        )
    )[0]


def _select_model(messages: list[dict], provider: str | None = None) -> str:
    """根据场景自动选择模型"""
    settings = get_settings()
    provider = provider or settings.AI_PROVIDER
    cfg = _get_provider_config(provider)
    default_model = cfg["default_model"] if cfg else "qwen-plus"

    last_msg = messages[-1]["content"] if messages else ""

    # 如果配置了场景别名优先使用
    if len(last_msg) < 100 and any(
        k in last_msg for k in ["吃了", "食物", "解析"]
    ):
        return settings.AI_FOOD_PARSE_MODEL or default_model

    if any(k in last_msg for k in ["生成", "计划", "推荐"]):
        return settings.AI_MEAL_PLAN_MODEL or default_model

    return default_model


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
