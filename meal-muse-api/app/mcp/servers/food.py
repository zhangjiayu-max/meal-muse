"""Food MCP Server — 封装 Spoonacular + Open Food Facts API"""
import logging
from app.mcp.client import MCPClient
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FoodMCPServer:
    """食物相关 MCP 工具集"""

    def __init__(self):
        # Spoonacular (需要 API key，有 150 次/天免费额度)
        self.spoonacular = MCPClient(
            base_url="https://api.spoonacular.com",
            api_key=getattr(settings, "SPOONACULAR_API_KEY", None),
            timeout=8.0,
        )
        # Open Food Facts (完全免费，无需 API key)
        self.openfoodfacts = MCPClient(
            base_url="https://world.openfoodfacts.org/api/v0",
            timeout=8.0,
        )

    async def search_recipes(
        self,
        query: str,
        diet: str | None = None,
        intolerances: list[str] | None = None,
        number: int = 5,
    ) -> list[dict]:
        """
        搜索菜谱 (Spoonacular)

        Args:
            query: 搜索关键词，如 "chicken breast"
            diet: 饮食类型 vegetarian/vegan/keto 等
            intolerances: 不耐受列表 [dairy, egg, gluten, peanut, seafood, shellfish, soy, tree nut, wheat]
            number: 返回数量 (1-10)
        """
        params = {
            "query": query,
            "number": min(number, 10),
            "addRecipeInformation": "true",
            "addRecipeNutrition": "true",
            "instructionsRequired": "true",
        }
        if diet:
            params["diet"] = diet
        if intolerances:
            params["intolerances"] = ",".join(intolerances)

        result = await self.spoonacular.get("/recipes/complexSearch", params=params)

        if "error" in result:
            return []

        recipes = result.get("results", [])
        return [
            {
                "id": r.get("id"),
                "title": r.get("title"),
                "image": r.get("image"),
                "ready_in_minutes": r.get("readyInMinutes"),
                "servings": r.get("servings"),
                "health_score": r.get("healthScore"),
                "calories": _extract_nutrient(r, "calories"),
                "protein": _extract_nutrient(r, "protein"),
                "fat": _extract_nutrient(r, "fat"),
                "carbs": _extract_nutrient(r, "carbs"),
                "diets": r.get("diets", []),
                "source_url": r.get("sourceUrl"),
            }
            for r in recipes[:number]
        ]

    async def lookup_nutrition(self, food_name: str) -> dict | None:
        """
        查询食物营养信息 (Open Food Facts 免费查询)
        优先用 Open Food Facts，fallback 到 Spoonacular

        Args:
            food_name: 食物名称，如 "organic milk"
        """
        # 先查 Open Food Facts
        result = await self.openfoodfacts.get(f"/product/{food_name}.json")

        if result and result.get("status") == 1 and result.get("product"):
            product = result["product"]
            nutrients = product.get("nutriments", {})
            return {
                "source": "Open Food Facts",
                "name": product.get("product_name", food_name),
                "brand": product.get("brands"),
                "calories_per_100g": nutrients.get("energy-kcal_100g"),
                "protein_per_100g": nutrients.get("proteins_100g"),
                "fat_per_100g": nutrients.get("fat_100g"),
                "carbs_per_100g": nutrients.get("carbohydrates_100g"),
                "fiber_per_100g": nutrients.get("fiber_100g"),
                "sugar_per_100g": nutrients.get("sugars_100g"),
                "sodium_per_100g": nutrients.get("sodium_100g"),
                "image_url": product.get("image_url"),
            }

        # Fallback: Spoonacular
        params = {"query": food_name, "number": 1}
        result = await self.spoonacular.get("/food/ingredients/search", params=params)

        if "error" in result or not result.get("results"):
            return None

        ingredient = result["results"][0]
        return {
            "source": "Spoonacular",
            "name": ingredient.get("name", food_name),
            "id": ingredient.get("id"),
            "image": ingredient.get("image"),
        }

    async def ingredient_substitute(self, ingredient: str) -> list[str]:
        """
        查找食材替代品 (Spoonacular)

        Args:
            ingredient: 食材名称，如 "butter"
        """
        # 先搜索获取 ID
        search_result = await self.spoonacular.get(
            "/food/ingredients/search",
            params={"query": ingredient, "number": 1, "metaInformation": "true"},
        )

        if "error" in search_result or not search_result.get("results"):
            return []

        ingredient_id = search_result["results"][0].get("id")
        if not ingredient_id:
            return []

        # 获取替代品
        sub_result = await self.spoonacular.get(
            f"/food/ingredients/{ingredient_id}/substitutes",
        )

        if "error" in sub_result:
            return []

        return sub_result.get("substitutes", [])

    async def close(self):
        await self.spoonacular.close()
        await self.openfoodfacts.close()


def _extract_nutrient(recipe: dict, nutrient_name: str) -> float | None:
    """从 Spoonacular recipe 中提取营养素"""
    nutrition = recipe.get("nutrition", {})
    nutrients = nutrition.get("nutrients", [])
    for n in nutrients:
        if n.get("name", "").lower() == nutrient_name:
            return n.get("amount")
    return None


# 全局实例
_food_server: FoodMCPServer | None = None


async def get_food_server() -> FoodMCPServer:
    global _food_server
    if _food_server is None:
        _food_server = FoodMCPServer()
    return _food_server
