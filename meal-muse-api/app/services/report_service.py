"""报告服务 — 从 reports.py 迁入"""

import logging

logger = logging.getLogger(__name__)


def generate_weekly_summary(avg_cal: float, target: int, days: int) -> str:
    """生成周报 AI 摘要"""
    if avg_cal > target + 100:
        return f"本周日均热量 {avg_cal}kcal，超出目标 {avg_cal - target}kcal。建议适当减少高热量食物，增加蔬菜摄入。"
    elif avg_cal < target - 200:
        return f"本周日均热量 {avg_cal}kcal，低于目标 {target - avg_cal}kcal。注意不要过度节食，保证营养均衡。"
    else:
        return f"本周日均热量 {avg_cal}kcal，控制良好！继续保持均衡饮食。"


def calculate_nutrition_scores(
    avg_calories: float,
    avg_protein: float,
    avg_fat: float,
    avg_carbs: float,
    avg_fiber: float,
    calorie_target: int = 1580,
) -> dict:
    """计算营养评分（0-100）"""
    cal_score = min(100, round(avg_calories / calorie_target * 100))
    protein_score = min(100, round(avg_protein / 60 * 100))   # 目标 60g
    fat_score = min(100, round(avg_fat / 55 * 100))           # 目标 55g
    carbs_score = min(100, round(avg_carbs / 200 * 100))      # 目标 200g
    fiber_score = min(100, round(avg_fiber / 25 * 100))       # 目标 25g

    return {
        "protein_score": protein_score,
        "fat_score": fat_score,
        "carbs_score": carbs_score,
        "fiber_score": fiber_score,
        "calorie_score": cal_score,
    }


def generate_nutrition_summary(scores: dict) -> str:
    """生成营养雷达摘要"""
    issues = []
    if scores["protein_score"] < 70:
        issues.append("蛋白质偏低")
    if scores["fiber_score"] < 70:
        issues.append("膳食纤维不足")
    if scores["calorie_score"] > 110:
        issues.append("热量超标")

    return "本周营养状况良好！" if not issues else f"需要注意：{'、'.join(issues)}。"
