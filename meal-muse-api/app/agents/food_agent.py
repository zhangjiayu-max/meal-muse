"""食物解析 Agent — 从自然语言中解析食物营养信息"""

from app.agents.base import BaseAgent, AgentResponse, PromptTemplate, PromptRegistry

# ===== Prompt 注册 =====

FOOD_PARSE_SYSTEM_PROMPT = """你是专业的营养师和食物数据库专家。你的任务是从用户的自然语言描述中解析出食物及其营养成分。

重要规则：
1. 必须返回 JSON 格式，不要返回其他内容
2. 每种食物都要估算重量（克）和营养成分
3. 如果用户没有明确数量，按照常见份量估算
4. 营养成分要尽量准确，参考中国食物成分表
5. 如果无法识别某种食物，标记为 "unknown"

{knowledge_context}

{user_context}"""

FOOD_PARSE_USER_TEMPLATE = """请解析以下食物描述，返回 JSON 格式：

用户输入："{food_text}"

返回格式（JSON 数组）：
[
  {{
    "name": "食物名称",
    "amount": "份量描述（如：1个、100g、1碗）",
    "weight_g": 100,
    "calories": 52,
    "protein": 0.3,
    "fat": 0.2,
    "carbs": 13.8,
    "fiber": 2.4
  }}
]

只返回 JSON 数组，无其他文字。"""

# 注册 Prompt
PromptRegistry.register(
    "food_parse",
    PromptTemplate(
        system=FOOD_PARSE_SYSTEM_PROMPT,
        user_template=FOOD_PARSE_USER_TEMPLATE,
        description="食物营养解析 Prompt",
        version="2.0",
        tags=["food", "nutrition", "parsing"],
    ),
)


class FoodParseAgent(BaseAgent):
    """食物解析 Agent"""

    def __init__(self):
        super().__init__("food_parse")

    def get_prompt_name(self) -> str:
        return "food_parse"

    async def parse(self, food_text: str, user_context: str = "") -> dict:
        """解析食物文本"""
        import json
        import re

        # 1. 格式化 Prompt
        system, user = self.format_prompt(
            food_text=food_text,
            user_context=user_context,
        )

        # 2. 调用 LLM
        from app.services.ai_service import call_ai_structured
        response = await call_ai_structured(
            prompt=user,
            system_prompt=system,
        )

        # 3. 解析 JSON
        try:
            # 清理响应
            content = response.strip()
            if content.startswith("```"):
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()

            foods = json.loads(content)

            # 验证格式
            if not isinstance(foods, list):
                foods = [foods]

            # 计算总量
            total_calories = sum(f.get("calories", 0) for f in foods)
            total_protein = sum(f.get("protein", 0) for f in foods)
            total_fat = sum(f.get("fat", 0) for f in foods)
            total_carbs = sum(f.get("carbs", 0) for f in foods)
            total_fiber = sum(f.get("fiber", 0) for f in foods)

            return {
                "foods": foods,
                "total_calories": round(total_calories, 1),
                "total_protein": round(total_protein, 1),
                "total_fat": round(total_fat, 1),
                "total_carbs": round(total_carbs, 1),
                "total_fiber": round(total_fiber, 1),
            }
        except Exception as e:
            self.logger.error(f"食物解析失败: {e}")

            # Fallback: 简单解析
            foods = []
            for item in food_text.replace("，", ",").replace("、", ",").split(","):
                item = item.strip()
                if item:
                    foods.append({
                        "name": item,
                        "amount": "1份",
                        "weight_g": 100,
                        "calories": 200,
                        "protein": 10,
                        "fat": 5,
                        "carbs": 30,
                        "fiber": 2,
                    })

            return {
                "foods": foods,
                "total_calories": sum(f["calories"] for f in foods),
                "total_protein": sum(f["protein"] for f in foods),
                "total_fat": sum(f["fat"] for f in foods),
                "total_carbs": sum(f["carbs"] for f in foods),
                "total_fiber": sum(f["fiber"] for f in foods),
            }
