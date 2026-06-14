"""天气 MCP Server — 查询天气并推荐应季饮食"""

import logging
from app.mcp.client import MCPClient
from app.config import get_settings

logger = logging.getLogger(__name__)

# 天气 → 饮食建议映射
WEATHER_FOOD_MAP = {
    "hot": {"label": "高温", "suggestion": "宜清凉解暑：绿豆汤、凉拌黄瓜、西瓜、苦瓜、酸梅汤"},
    "cold": {"label": "低温", "suggestion": "宜温补暖身：羊肉汤、生姜红枣茶、桂圆、炖牛肉"},
    "humid": {"label": "潮湿", "suggestion": "宜祛湿健脾：薏仁粥、冬瓜汤、山药、白扁豆"},
    "rainy": {"label": "雨天", "suggestion": "宜暖胃汤粥：鸡汤、小米粥、姜丝热面"},
    "dry": {"label": "干燥", "suggestion": "宜润燥滋阴：银耳羹、百合莲子、雪梨、蜂蜜水"},
    "windy": {"label": "大风", "suggestion": "宜防风保暖：热汤、姜茶、温热粥品"},
}


def _classify_weather(temp: float, humidity: float, description: str) -> str:
    """根据温度、湿度和天气描述分类"""
    desc_lower = description.lower()
    if any(w in desc_lower for w in ["rain", "雨", "drizzle", "shower"]):
        return "rainy"
    if any(w in desc_lower for w in ["snow", "雪", "ice"]):
        return "cold"
    if temp >= 32:
        return "hot"
    if temp <= 5:
        return "cold"
    if humidity >= 80:
        return "humid"
    if any(w in desc_lower for w in ["dry", "干燥", "沙尘"]):
        return "dry"
    if any(w in desc_lower for w in ["wind", "风", "gust"]):
        return "windy"
    return "hot" if temp >= 28 else "cold" if temp <= 10 else "humid"


class WeatherMCPServer:
    """天气查询服务 — 默认用 wttr.in (免费)，可选和风天气"""

    def __init__(self):
        settings = get_settings()
        self._weather_key = settings.WEATHER_API_KEY
        # wttr.in 免费服务
        self._wttr = MCPClient(base_url="https://wttr.in", timeout=8.0)

    async def get_weather(self, city: str = "auto") -> dict:
        """
        查询天气并返回饮食建议。
        city: 城市名或 "auto"（自动定位）
        返回: {city, temp, humidity, description, food_suggestion, category}
        """
        try:
            if self._weather_key:
                return await self._get_weather_qweather(city)
        except Exception as e:
            logger.warning("和风天气查询失败，回退 wttr.in: %s", e)

        return await self._get_weather_wttr(city)

    async def _get_weather_wttr(self, city: str) -> dict:
        """通过 wttr.in 查询天气（免费，无需 key）"""
        query_city = city if city != "auto" else ""
        data = await self._wttr.get(
            f"/{query_city}",
            params={"format": "j1"},
        )
        if "error" in data:
            return {"error": data["error"]}

        try:
            current = data.get("current_condition", [{}])[0]
            temp = float(current.get("temp_C", 0))
            humidity = float(current.get("humidity", 0))
            desc_cn = current.get("lang_zh", [{}])
            description = desc_cn[0].get("value", "") if desc_cn else current.get("weatherDesc", [{}])[0].get("value", "")
            area = data.get("nearest_area", [{}])[0]
            city_name = area.get("areaName", [{}])[0].get("value", city)

            category = _classify_weather(temp, humidity, description)
            suggestion = WEATHER_FOOD_MAP.get(category, {})

            return {
                "city": city_name,
                "temp": temp,
                "humidity": humidity,
                "description": description,
                "category": category,
                "food_suggestion": suggestion.get("suggestion", ""),
            }
        except (KeyError, IndexError, ValueError) as e:
            logger.warning("wttr.in 数据解析失败: %s", e)
            return {"error": f"天气数据解析失败: {e}"}

    async def _get_weather_qweather(self, city: str) -> dict:
        """通过和风天气查询（需要 API key）"""
        # 和风天气实时天气接口
        qweather = MCPClient(
            base_url="https://devapi.qweather.com",
            api_key=self._weather_key,
            timeout=8.0,
        )
        try:
            # 先查城市 ID
            geo_data = await qweather.get("/v2/city/lookup", params={"location": city})
            if "error" in geo_data or not geo_data.get("location"):
                return await self._get_weather_wttr(city)

            location_id = geo_data["location"][0]["id"]
            city_name = geo_data["location"][0].get("name", city)

            # 查实时天气
            data = await qweather.get("/v7/weather/now", params={"location": location_id})
            if "error" in data:
                return await self._get_weather_wttr(city)

            now = data.get("now", {})
            temp = float(now.get("temp", 0))
            humidity = float(now.get("humidity", 0))
            description = now.get("text", "")

            category = _classify_weather(temp, humidity, description)
            suggestion = WEATHER_FOOD_MAP.get(category, {})

            return {
                "city": city_name,
                "temp": temp,
                "humidity": humidity,
                "description": description,
                "category": category,
                "food_suggestion": suggestion.get("suggestion", ""),
            }
        finally:
            await qweather.close()

    async def close(self):
        await self._wttr.close()


# ——— 全局单例 ———

_weather_server: WeatherMCPServer | None = None


def get_weather_server() -> WeatherMCPServer:
    global _weather_server
    if _weather_server is None:
        _weather_server = WeatherMCPServer()
    return _weather_server
