"""食物解析服务 — 从 diet.py 迁入"""

import json
import re
import logging
from app.services.ai_service import call_ai_structured

logger = logging.getLogger(__name__)

# AI 食物解析 system prompt
FOOD_PARSE_SYSTEM = """你是一个营养分析助手。用户会输入他们吃过的食物，你需要：
1. 识别出所有食物及份量
2. 估算每种食物的热量、蛋白质、脂肪、碳水

返回严格的 JSON 格式：
{
  "foods": [
    {"name": "食物名", "amount": "份量描述", "calories": 数字, "protein": 数字, "fat": 数字, "carbs": 数字}
  ],
  "total_calories": 数字,
  "total_protein": 数字,
  "total_fat": 数字,
  "total_carbs": 数字
}

注意：
- 份量参考中国饮食习惯（1碗≈200g, 1份≈150g, 1个鸡蛋≈50g等）
- 如果用户没写份量，按标准份量估算
- 只返回 JSON，不要其他文字
- 热量单位为 kcal，蛋白质/脂肪/碳水单位为 g"""


def _simple_parse(food_text: str) -> dict:
    """简单兜底解析（AI 不可用时）"""
    foods = []
    total_cal = 0
    for item in food_text.replace("，", ",").replace("、", ",").split(","):
        item = item.strip()
        if item:
            foods.append({"name": item, "amount": "1份", "calories": 200})
            total_cal += 200
    return {
        "foods": foods,
        "total_calories": total_cal,
        "total_protein": round(total_cal * 0.15 / 4, 1),
        "total_fat": round(total_cal * 0.25 / 9, 1),
        "total_carbs": round(total_cal * 0.60 / 4, 1),
    }


async def parse_food_text(food_text: str) -> dict:
    """用 AI 解析食物文本，返回营养估算"""
    try:
        raw = await call_ai_structured(
            prompt=food_text,
            system_prompt=FOOD_PARSE_SYSTEM,
        )
        # 解析 JSON
        text = raw.strip()
        m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
        if m:
            text = m.group(1)
        else:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]

        result = json.loads(text)
        if "foods" in result and "total_calories" in result:
            logger.info(f"AI 食物解析成功: {len(result['foods'])} 种食物, {result['total_calories']} kcal")
            return result
    except Exception as e:
        logger.warning(f"AI 食物解析失败，使用兜底解析: {e}")

    return _simple_parse(food_text)
