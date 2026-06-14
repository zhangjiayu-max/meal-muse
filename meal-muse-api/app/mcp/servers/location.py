"""位置 MCP Server — 附近健康餐厅搜索（高德地图）"""

import logging
from app.mcp.client import MCPClient
from app.config import get_settings

logger = logging.getLogger(__name__)

# 健康餐厅关键词过滤
HEALTHY_KEYWORDS = ["轻食", "沙拉", "健康", "素食", "有机", "低卡", "减脂", "营养餐", "养生"]


class LocationMCPServer:
    """附近餐厅搜索 — 基于高德地图 POI"""

    def __init__(self):
        settings = get_settings()
        self._amap_key = settings.AMAP_API_KEY
        self._client = MCPClient(base_url="https://restapi.amap.com", timeout=10.0)

    async def nearby_restaurants(
        self,
        lat: float,
        lng: float,
        keyword: str = "餐厅",
        radius: int = 1000,
        healthy_only: bool = False,
    ) -> dict:
        """
        搜索附近餐厅。
        lat/lng: 用户坐标
        keyword: 搜索关键词
        radius: 搜索半径（米，默认 1000）
        healthy_only: 是否只返回健康餐厅
        返回: {count, restaurants: [{name, address, distance, rating, tel, type}]}
        """
        if not self._amap_key:
            return {"error": "未配置高德地图 API Key", "count": 0, "restaurants": []}

        location = f"{lng},{lat}"  # 高德格式: 经度,纬度
        params = {
            "key": self._amap_key,
            "location": location,
            "keywords": keyword,
            "radius": radius,
            "types": "050000",  # 餐饮服务
            "offset": 20,
            "extensions": "all",
        }

        data = await self._client.get("/v3/place/around", params=params)

        if "error" in data:
            return {"error": data["error"], "count": 0, "restaurants": []}

        if data.get("status") != "1":
            return {"error": data.get("info", "查询失败"), "count": 0, "restaurants": []}

        pois = data.get("pois", [])
        restaurants = []

        for poi in pois:
            name = poi.get("name", "")
            poi_type = poi.get("type", "")

            # 健康餐厅过滤
            if healthy_only:
                is_healthy = any(kw in name or kw in poi_type for kw in HEALTHY_KEYWORDS)
                # 如果没有明确的健康关键词，跳过普通餐厅
                if not is_healthy and keyword in ["餐厅", "吃饭", "饭店"]:
                    continue

            distance = poi.get("distance", "")
            restaurants.append({
                "name": name,
                "address": poi.get("address", ""),
                "distance": f"{distance}m" if distance else "",
                "rating": poi.get("biz_ext", {}).get("rating", ""),
                "tel": poi.get("tel", ""),
                "type": poi_type,
                "cost": poi.get("biz_ext", {}).get("cost", ""),
            })

        # 按距离排序
        restaurants.sort(key=lambda r: int(r["distance"].replace("m", "") or "99999"))

        return {
            "count": len(restaurants),
            "restaurants": restaurants[:10],
        }

    async def close(self):
        await self._client.close()


# ——— 全局单例 ———

_location_server: LocationMCPServer | None = None


def get_location_server() -> LocationMCPServer:
    global _location_server
    if _location_server is None:
        _location_server = LocationMCPServer()
    return _location_server
