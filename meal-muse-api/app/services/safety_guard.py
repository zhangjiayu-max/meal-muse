"""安全/禁忌检查服务 — 食物安全验证 + 菜单过滤 + 疾病-食物禁忌映射"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.allergy_tag import AllergyTag
from app.models.health_condition import HealthCondition
from sqlalchemy import select

# 疾病 → 禁忌食物类别
CONDITION_FOOD_RESTRICTIONS: dict[str, dict[str, list[str]]] = {
    "diabetes": {
        "restricted": [
            "含糖饮料", "果汁", "甜点", "蛋糕", "糖果", "巧克力",
            "白米饭（过量）", "白面包", "精制面条", "糯米",
            "蜜饯", "果酱", "蜂蜜（过量）", "冰淇淋",
        ],
        "preferred": ["全谷物", "糙米", "燕麦", "荞麦", "蔬菜", "豆类"],
    },
    "hypertension": {
        "restricted": [
            "腌制品", "咸菜", "腊肉", "腊肠", "咸鱼", "咸蛋",
            "方便面", "薯片", "加工肉制品", "酱油（过量）",
            "味精", "鸡精", "高盐调味料",
        ],
        "preferred": ["新鲜蔬果", "钾丰富食物", "低钠盐", "清蒸烹饪"],
    },
    "hyperlipidemia": {
        "restricted": [
            "肥肉", "动物内脏", "油炸食品", "黄油", "奶油",
            "蛋黄（过量）", "鱿鱼", "鱼籽", "虾头",
        ],
        "preferred": ["鱼肉", "去皮禽肉", "橄榄油", "坚果（适量）"],
    },
    "gout": {
        "restricted": [
            "动物内脏", "海鲜（贝类/虾蟹）", "红肉",
            "啤酒", "白酒", "浓汤", "火锅汤底",
            "豆制品（过量）", "菠菜（过量）", "芦笋",
        ],
        "preferred": ["低嘌呤蔬菜", "鸡蛋", "奶制品", "多饮水"],
    },
    "ulcer": {
        "restricted": [
            "辣椒", "花椒", "芥末", "大蒜（过量）",
            "咖啡", "浓茶", "酒精", "酸性水果（过量）",
            "油炸食品", "过硬食物",
        ],
        "preferred": ["温和食物", "粥类", "蒸蛋", "熟香蕉"],
    },
    "kidney": {
        "restricted": [
            "高盐食物", "高蛋白（过量）", "香蕉（高钾）",
            "橙子", "土豆", "浓汤", "加工食品",
        ],
        "preferred": ["低蛋白适量", "低盐低钾", "新鲜清淡"],
    },
}


async def check_food_safety(
    db: AsyncSession, user_id: str, food_name: str
) -> dict:
    """
    检查食物对用户是否安全。

    Returns:
        {
            "safe": bool,
            "warnings": [str, ...],   # 不安全的原因列表
            "suggestions": [str, ...], # 替代建议
        }
    """
    warnings: list[str] = []
    suggestions: list[str] = []

    # 1. 过敏原检查
    allergies = await _get_user_allergies(db, user_id)
    for allergy in allergies:
        allergen = allergy.allergen
        allergen_name = allergy.custom_name if allergen == "custom" else allergen
        if _matches_allergen(food_name, allergen, allergen_name):
            level_label = _reaction_label(allergy.reaction_level)
            warnings.append(f"⛔ 食物「{food_name}」含过敏原「{allergen_name}」（{level_label}）")
            suggestions.append("请从菜单中移除该食物")

    # 2. 疾病禁忌检查
    conditions = await _get_user_conditions(db, user_id)
    for condition in conditions:
        c_type = condition.condition_type
        if c_type in CONDITION_FOOD_RESTRICTIONS:
            rules = CONDITION_FOOD_RESTRICTIONS[c_type]
            for restricted in rules["restricted"]:
                if restricted in food_name:
                    warnings.append(f"⚠️ 食物「{food_name}」不适合{c_type}患者（含「{restricted}」）")
                    if rules.get("preferred"):
                        suggestions.append(f"建议替换为：{'/'.join(rules['preferred'][:3])}")
                    break

    return {
        "safe": len(warnings) == 0,
        "warnings": warnings,
        "suggestions": suggestions,
    }


async def filter_menu_plan(
    db: AsyncSession, user_id: str, menu: dict
) -> dict:
    """
    过滤餐食计划中的禁忌食物。
    遍历 breakfast/lunch/dinner 的 foods，标记不安全项并给出替换建议。

    返回：
        {
            ...原菜单结构,
            "safety_alerts": [{"meal": "breakfast", "food": "虾", "warning": "..."}],
        }
    """
    alerts: list[dict] = []
    filtered_menu = {**menu}

    for meal_key in ("breakfast", "lunch", "dinner"):
        meal = filtered_menu.get(meal_key)
        if not meal or not isinstance(meal, dict):
            continue
        foods = meal.get("foods", [])
        safe_foods = []
        for food in foods:
            food_name = food.get("name", "")
            result = await check_food_safety(db, user_id, food_name)
            if result["safe"]:
                safe_foods.append(food)
            else:
                for w in result["warnings"]:
                    alerts.append({"meal": meal_key, "food": food_name, "warning": w})
                food["unsafe"] = True
                food["warning"] = result["warnings"][0] if result["warnings"] else ""
                safe_foods.append(food)  # 保留但标记
        meal["foods"] = safe_foods

    filtered_menu["safety_alerts"] = alerts
    return filtered_menu


async def get_safety_rules(db: AsyncSession, user_id: str) -> dict:
    """
    获取用户完整的安全规则，供 AI prompt 使用。
    """
    allergies = await _get_user_allergies(db, user_id)
    conditions = await _get_user_conditions(db, user_id)

    allergy_list = []
    for a in allergies:
        name = a.custom_name if a.allergen == "custom" else a.allergen
        allergy_list.append(name)

    condition_rules = []
    for c in conditions:
        if c.condition_type in CONDITION_FOOD_RESTRICTIONS:
            rules = CONDITION_FOOD_RESTRICTIONS[c.condition_type]
            condition_rules.append({
                "condition": c.condition_type,
                "severity": c.severity,
                "restricted": rules["restricted"][:10],
            })

    return {
        "allergies": allergy_list,
        "condition_rules": condition_rules,
    }


# ——— 内部辅助 ———


async def _get_user_allergies(db: AsyncSession, user_id: str) -> list:
    result = await db.execute(
        select(AllergyTag).where(AllergyTag.user_id == user_id)
    )
    return list(result.scalars().all())


async def _get_user_conditions(db: AsyncSession, user_id: str) -> list:
    result = await db.execute(
        select(HealthCondition).where(HealthCondition.user_id == user_id)
    )
    return list(result.scalars().all())


def _matches_allergen(food_name: str, allergen_type: str, allergen_name: str) -> bool:
    """检查食物名是否匹配过敏原"""
    allergen_map = {
        "seafood": ["虾", "蟹", "贝", "鱿鱼", "鱼", "海", "三文", "金枪", "鳕", "鲈"],
        "peanut": ["花生"],
        "dairy": ["奶", "乳", "芝士", "黄油", "奶酪", "酸奶"],
        "egg": ["蛋"],
        "gluten": ["面", "麦", "面包", "饼", "馒头"],
        "soy": ["豆", "豆腐", "豆浆"],
    }
    if allergen_type == "custom":
        return allergen_name in food_name
    keywords = allergen_map.get(allergen_type, [])
    return any(kw in food_name for kw in keywords)


def _reaction_label(level: str) -> str:
    labels = {
        "mild": "轻度反应",
        "moderate": "中度反应",
        "severe": "严重反应",
        "anaphylaxis": "过敏性休克风险",
    }
    return labels.get(level, level)
