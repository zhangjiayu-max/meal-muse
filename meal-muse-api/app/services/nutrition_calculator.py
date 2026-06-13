"""营养计算服务 — BMI / 热量需求 / 宏量营养素 / 运动消耗"""

import math

# MET值（ Metabolic Equivalent of Task ）用于运动热量估算
MET_TABLE: dict[str, dict] = {
    "running":        {"low": 7.0, "medium": 9.8, "high": 14.5},
    "walking":        {"low": 2.5, "medium": 3.5, "high": 5.0},
    "cycling":        {"low": 4.0, "medium": 7.5, "high": 11.0},
    "swimming":       {"low": 5.8, "medium": 7.0, "high": 9.8},
    "yoga":          {"low": 2.0, "medium": 3.0, "high": 4.0},
    "strength":      {"low": 3.5, "medium": 5.0, "high": 8.0},
    "hiit":          {"low": 8.0, "medium": 10.0, "high": 14.0},
    "dance":         {"low": 4.5, "medium": 6.0, "high": 9.0},
    "climbing":      {"low": 5.0, "medium": 7.5, "high": 11.0},
    "other":         {"low": 3.0, "medium": 4.0, "high": 6.0},
}


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """计算 BMI = 体重(kg) / 身高(m)^2"""
    if height_cm <= 0 or weight_kg <= 0:
        return 0.0
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def bmi_category(bmi: float) -> str:
    """BMI 分类"""
    if bmi <= 0:
        return "未知"
    if bmi < 18.5:
        return "偏瘦"
    if bmi < 24:
        return "正常"
    if bmi < 28:
        return "超重"
    return "肥胖"


def bmr_mifflin(height_cm: float, weight_kg: float, age: int, gender: str = "female") -> float:
    """
    使用 Mifflin-St Jeor 公式估算基础代谢率（BMR）。
    gender: "male" 或 "female"
    """
    if gender == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


def tdee(bmr: float, activity_level: str = "sedentary") -> float:
    """
    估算每日总消耗（TDEE）。
    activity_level: sedentary / light / moderate / active / very_active
    """
    multipliers = {
        "sedentary": 1.2,        # 几乎不运动
        "light": 1.375,           # 每周1-3次轻运动
        "moderate": 1.55,         # 每周3-5次中等运动
        "active": 1.725,          # 每周6-7次运动
        "very_active": 1.9,       # 运动员/体力劳动
    }
    return bmr * multipliers.get(activity_level, 1.2)


def calculate_daily_calorie_target(
    height_cm: float,
    weight_kg: float,
    age: int,
    gender: str = "female",
    activity_level: str = "sedentary",
    goal_type: str = "maintain",
) -> int:
    """
    根据目标计算每日热量目标。
    goal_type: maintain / weight_loss / muscle_gain / pregnancy
    """
    bmr = bmr_mifflin(height_cm, weight_kg, age, gender)
    tdee_val = tdee(bmr, activity_level)

    targets = {
        "maintain": tdee_val,
        "weight_loss": tdee_val - 400,    # 温和减脂：每日缺口 400kcal
        "muscle_gain": tdee_val + 300,    # 增肌：每日盈余 300kcal
        "pregnancy": tdee_val + 300,      # 备孕/孕期：每日+300kcal
    }
    return int(targets.get(goal_type, tdee_val))


# 宏量营养素推荐比例（克/kg体重/天，或卡路里占比）
# goal_type → (protein_pct, fat_pct, carbs_pct)
MACRO_SPLITS: dict[str, tuple[float, float, float]] = {
    "maintain":     (0.20, 0.30, 0.50),
    "weight_loss":  (0.30, 0.30, 0.40),  # 高蛋白减脂保肌肉
    "muscle_gain":  (0.30, 0.25, 0.45),
    "pregnancy":    (0.25, 0.30, 0.45),
}


def calculate_macros(calories: int, goal_type: str = "maintain") -> dict:
    """
    计算每日宏量营养素目标。
    Returns: {"protein_g": int, "fat_g": int, "carbs_g": int}
    """
    splits = MACRO_SPLITS.get(goal_type, (0.20, 0.30, 0.50))
    protein_pct, fat_pct, carbs_pct = splits

    protein_cal = calories * protein_pct
    fat_cal = calories * fat_pct
    carbs_cal = calories * carbs_pct

    return {
        "protein_g": int(protein_cal / 4),   # 蛋白质：4kcal/g
        "fat_g": int(fat_cal / 9),           # 脂肪：9kcal/g
        "carbs_g": int(carbs_cal / 4),       # 碳水：4kcal/g
        "protein_cal": int(protein_cal),
        "fat_cal": int(fat_cal),
        "carbs_cal": int(carbs_cal),
    }


def estimate_calories_from_exercise(
    weight_kg: float,
    exercise_type: str,
    duration_minutes: int,
    intensity: str = "medium",
) -> int:
    """
    使用 MET 公式估算运动消耗热量。
    公式：MET × 体重(kg) × 时间(h) = kcal

    Returns: 估算消耗的热量（千卡）
    """
    met_map = MET_TABLE.get(exercise_type, MET_TABLE["other"])
    met = met_map.get(intensity, met_map["medium"])

    calories = met * weight_kg * (duration_minutes / 60)
    return int(calories)


def adjust_calorie_target_for_exercise(
    base_target: int,
    exercise_calories: int,
    goal_type: str,
) -> int:
    """
    根据当日运动消耗调整热量目标。
    减脂用户：运动消耗可以弥补部分热量缺口
    增肌用户：运动消耗需要补偿，否则热量缺口过大
    """
    if goal_type == "weight_loss":
        # 运动消耗的 50% 可以加入当日热量（防止过度节食）
        return base_target + int(exercise_calories * 0.5)
    elif goal_type == "muscle_gain":
        # 增肌用户：运动消耗需全部补偿
        return base_target + exercise_calories
    return base_target  # 维持体重/备孕用户不调整
