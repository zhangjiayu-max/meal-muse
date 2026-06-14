"""餐食计划 Agent — 生成个性化三餐方案"""

from app.agents.base import BaseAgent, AgentResponse, PromptTemplate, PromptRegistry

# ===== Prompt 注册 =====

MEAL_PLAN_SYSTEM_PROMPT = """你是专业的营养师和厨师，负责为用户生成个性化的每日三餐计划。

生成原则：
1. 根据用户的健康目标（减脂/增肌/备孕/养生）定制餐单
2. 考虑用户的饮食偏好、过敏原、忌口食物
3. 确保营养均衡：蛋白质、碳水、脂肪、维生素、矿物质
4. 菜品要实用、易操作，适合家庭烹饪
5. 结合时令季节推荐食材
6. 中医食疗理念融入（如经期不同阶段的饮食调理）

{knowledge_context}

{user_context}"""

MEAL_PLAN_USER_TEMPLATE = """请为用户生成今日三餐计划。

用户要求：{user_request}

返回格式（JSON）：
{{
  "breakfast": {{
    "name": "早餐名称",
    "foods": [
      {{"name": "食物", "amount": "份量", "calories": 100, "protein": 5, "fat": 2, "carbs": 15}}
    ],
    "total_calories": 300,
    "total_protein": 20,
    "total_fat": 10,
    "total_carbs": 40
  }},
  "lunch": {{ ... }},
  "dinner": {{ ... }},
  "total_calories": 1500,
  "ai_note": "今日饮食建议（50字内）"
}}

只返回 JSON，无其他文字。"""

# 注册 Prompt
PromptRegistry.register(
    "meal_plan",
    PromptTemplate(
        system=MEAL_PLAN_SYSTEM_PROMPT,
        user_template=MEAL_PLAN_USER_TEMPLATE,
        description="餐食计划生成 Prompt",
        version="2.0",
        tags=["meal", "plan", "nutrition"],
    ),
)


class MealPlanAgent(BaseAgent):
    """餐食计划 Agent"""

    def __init__(self):
        super().__init__("meal_plan")

    def get_prompt_name(self) -> str:
        return "meal_plan"

    async def generate(
        self,
        user_context: str = "",
        user_request: str = "请生成今日三餐计划",
    ) -> dict:
        """生成餐食计划"""
        import json

        # 1. 格式化 Prompt
        system, user = self.format_prompt(
            user_context=user_context,
            user_request=user_request,
        )

        # 2. 调用 LLM
        from app.services.ai_service import call_ai_structured
        response = await call_ai_structured(
            prompt=user,
            system_prompt=system,
        )

        # 3. 解析 JSON
        try:
            content = response.strip()
            if content.startswith("```"):
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()

            plan = json.loads(content)
            return plan
        except Exception as e:
            self.logger.error(f"餐食计划生成失败: {e}")

            # Fallback: 返回默认计划
            return {
                "breakfast": {
                    "name": "元气早餐",
                    "foods": [
                        {"name": "小米粥", "amount": "1碗", "calories": 120, "protein": 3, "fat": 1, "carbs": 25},
                        {"name": "水煮蛋", "amount": "2个", "calories": 140, "protein": 12, "fat": 10, "carbs": 1},
                    ],
                    "total_calories": 260,
                    "total_protein": 15,
                    "total_fat": 11,
                    "total_carbs": 26,
                },
                "lunch": {
                    "name": "均衡午餐",
                    "foods": [
                        {"name": "清蒸鲈鱼", "amount": "1份", "calories": 180, "protein": 28, "fat": 6, "carbs": 0},
                        {"name": "糙米饭", "amount": "1碗", "calories": 220, "protein": 5, "fat": 2, "carbs": 44},
                    ],
                    "total_calories": 400,
                    "total_protein": 33,
                    "total_fat": 8,
                    "total_carbs": 44,
                },
                "dinner": {
                    "name": "轻食晚餐",
                    "foods": [
                        {"name": "番茄豆腐汤", "amount": "1碗", "calories": 80, "protein": 6, "fat": 3, "carbs": 8},
                        {"name": "鸡胸肉沙拉", "amount": "1份", "calories": 250, "protein": 30, "fat": 8, "carbs": 12},
                    ],
                    "total_calories": 330,
                    "total_protein": 36,
                    "total_fat": 11,
                    "total_carbs": 20,
                },
                "total_calories": 990,
                "ai_note": "今日推荐清淡均衡饮食，蛋白质充足。",
            }

    async def replace_meal(
        self,
        meal_type: str,
        user_context: str = "",
    ) -> dict:
        """替换某一餐"""
        meal_names = {
            "breakfast": "早餐",
            "lunch": "午餐",
            "dinner": "晚餐",
        }
        meal_name = meal_names.get(meal_type, "餐食")

        return await self.generate(
            user_context=user_context,
            user_request=f"请只生成一个新的{meal_name}方案，其他餐不需要",
        )
