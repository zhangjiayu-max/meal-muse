"""MCP Router — 根据 AI 对话意图路由到对应的 MCP Server"""
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MCPRouter:
    """MCP 意图路由器"""

    # 意图 → 工具映射
    INTENT_PATTERNS = {
        "recipe_search": [
            r"怎么做(.+)", r"(.+)怎么做", r"(.+)的做法", r"(.+)食谱",
            r"推荐(.+)菜", r"有什么(.+)菜", r"搜索(.+)",
            r"想吃(.+)", r"做(.+)吃",
        ],
        "nutrition_lookup": [
            r"(.+)热量", r"(.+)营养", r"(.+)卡路里", r"(.+)含多少",
            r"(.+)碳水", r"(.+)蛋白质", r"(.+)脂肪含量",
        ],
        "ingredient_substitute": [
            r"(.+)替代", r"没有(.+)用什么", r"(.+)替换", r"用(.+)代替(.+)",
        ],
        "weather_food": [
            r"(?:今天|明天|现在)(?:天气|气温|温度)", r"外面(热|冷|下雨|刮风)",
            r"天(热|冷|下雨)吃(什么|啥)", r"(热|冷)天吃(什么|啥)",
            r"天气.*推荐.*吃", r"(?:下雨|高温|降温)吃(什么|啥)",
        ],
        "nearby_restaurant": [
            r"附近.*(?:餐厅|饭店|吃饭|吃的)", r"(?:去|在哪)(?:哪里|哪)(?:吃|吃饭)",
            r"推荐.*(?:餐厅|饭店)", r"(?:附近|周围).*(?:吃|饭)",
        ],
    }

    def detect_intent(self, message: str) -> list[dict[str, Any]]:
        """
        检测消息中的 MCP 意图

        Returns:
            [{"intent": "recipe_search", "query": "番茄炒蛋"}, ...]
        """
        detected = []
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, message)
                if match:
                    query = match.group(1) if match.groups() else message
                    detected.append({"intent": intent, "query": query.strip()})
                    break
        return detected

    async def route(self, message: str, context: dict | None = None) -> list[dict[str, Any]]:
        """
        路由消息到对应 MCP Server

        Args:
            message: 用户消息
            context: 额外上下文 (如饮食类型、过敏原、经纬度等)

        Returns:
            MCP 工具结果列表
        """
        intents = self.detect_intent(message)
        if not intents:
            return []

        # 分离需要不同 server 的 intents
        food_intents = [i for i in intents if i["intent"] in ("recipe_search", "nutrition_lookup", "ingredient_substitute")]
        weather_intents = [i for i in intents if i["intent"] == "weather_food"]
        location_intents = [i for i in intents if i["intent"] == "nearby_restaurant"]

        results = []

        # 食物相关意图
        if food_intents:
            from app.mcp.servers.food import get_food_server
            food_server = await get_food_server()
            try:
                for item in food_intents:
                    intent = item["intent"]
                    query = item["query"]

                    if intent == "recipe_search":
                        diet = context.get("diet_type") if context else None
                        intolerances = context.get("allergies") if context else None
                        recipes = await food_server.search_recipes(
                            query=query, diet=diet, intolerances=intolerances, number=3,
                        )
                        results.append({"tool": "recipe_search", "query": query, "results": recipes})

                    elif intent == "nutrition_lookup":
                        nutrition = await food_server.lookup_nutrition(query)
                        results.append({"tool": "nutrition_lookup", "query": query, "results": nutrition})

                    elif intent == "ingredient_substitute":
                        substitutes = await food_server.ingredient_substitute(query)
                        results.append({"tool": "ingredient_substitute", "query": query, "results": substitutes})
            except Exception as e:
                logger.warning("MCP food routing error: %s", e)
            finally:
                await food_server.close()

        # 天气意图
        if weather_intents:
            from app.mcp.servers.weather import get_weather_server
            weather_server = get_weather_server()
            try:
                city = context.get("city", "auto") if context else "auto"
                weather = await weather_server.get_weather(city)
                results.append({"tool": "weather_food", "query": city, "results": weather})
            except Exception as e:
                logger.warning("MCP weather routing error: %s", e)
            finally:
                await weather_server.close()

        # 附近餐厅意图
        if location_intents:
            from app.mcp.servers.location import get_location_server
            location_server = get_location_server()
            try:
                lat = context.get("lat") if context else None
                lng = context.get("lng") if context else None
                if lat and lng:
                    query = location_intents[0]["query"]
                    healthy_only = any(kw in message for kw in ["健康", "轻食", "减脂", "低卡"])
                    restaurants = await location_server.nearby_restaurants(
                        lat=float(lat), lng=float(lng), healthy_only=healthy_only,
                    )
                    results.append({"tool": "nearby_restaurant", "query": query, "results": restaurants})
                else:
                    results.append({
                        "tool": "nearby_restaurant",
                        "query": location_intents[0]["query"],
                        "results": {"error": "需要提供位置信息（经纬度）才能搜索附近餐厅"},
                    })
            except Exception as e:
                logger.warning("MCP location routing error: %s", e)
            finally:
                await location_server.close()

        return results


# 全局实例
_router: MCPRouter | None = None


def get_mcp_router() -> MCPRouter:
    global _router
    if _router is None:
        _router = MCPRouter()
    return _router
