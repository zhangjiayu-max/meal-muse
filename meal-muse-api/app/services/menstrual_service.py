"""经期服务 — 统一的经期阶段计算与饮食建议

抽取自 api/v1/menstrual.py 和 services/context_builder.py，
消除两处阶段计算逻辑不一致的问题。
"""

from datetime import date, timedelta


# 经期阶段饮食建议（备孕/经期营养强化）
PHASE_DIET_TIPS: dict[str, dict] = {
    "menstrual": {
        "phase_name": "月经期",
        "diet_focus": "温补驱寒，补充铁质",
        "recommended": ["红糖姜茶", "当归羊肉汤", "猪肝", "菠菜", "红枣", "桂圆"],
        "avoid": ["冰淇淋", "冷饮", "西瓜", "螃蟹"],
        "recommended_fruits": ["樱桃", "红枣", "桂圆", "榴莲"],
        "avoid_fruits": ["西瓜", "梨", "柚子"],
    },
    "follicular": {
        "phase_name": "卵泡期",
        "diet_focus": "补充优质蛋白，为排卵做准备",
        "recommended": ["鸡蛋", "鱼", "豆腐", "黑芝麻", "黑豆", "西兰花"],
        "avoid": ["油炸食品", "高糖食物"],
        "recommended_fruits": ["蓝莓", "草莓", "苹果", "牛油果"],
        "avoid_fruits": [],
    },
    "ovulation": {
        "phase_name": "排卵期",
        "diet_focus": "补充叶酸和锌，促进卵子质量",
        "recommended": ["黑豆", "豆浆", "坚果", "深海鱼", "芦笋", "菠菜"],
        "avoid": ["酒精", "咖啡过量"],
        "recommended_fruits": ["牛油果", "蓝莓", "石榴", "猕猴桃"],
        "avoid_fruits": ["冰镇水果"],
    },
    "luteal": {
        "phase_name": "黄体期",
        "diet_focus": "补充B族维生素，缓解PMS",
        "recommended": ["香蕉", "燕麦", "坚果", "菠菜", "全谷物", "红薯"],
        "avoid": ["高盐食物", "咖啡因过量", "辛辣刺激"],
        "recommended_fruits": ["香蕉", "苹果", "橙子", "樱桃"],
        "avoid_fruits": [],
    },
}


# 阶段对应的 AI 上下文描述（供 context_builder 注入）
PHASE_CONTEXT_DESC: dict[str, str] = {
    "menstrual": "月经期（需温补驱寒、补铁）",
    "follicular": "卵泡期（推荐高蛋白、深色食物）",
    "ovulation": "排卵期（推荐促排卵食物，补充叶酸和锌）",
    "luteal": "黄体期（缓解PMS，推荐高蛋白、深色食物）",
}


def calculate_menstrual_phase(
    period_start: date,
    cycle_length: int = 28,
    ovulation_day: date | None = None,
    period_end: date | None = None,
    today: date | None = None,
) -> tuple[str, date | None]:
    """
    统一计算当前经期阶段。

    优先用存储的 ovulation_day 做日期区间判断（更准确），
    未提供时按周期天数推算排卵日（period_start + cycle_length - 14）。

    Returns: (phase_key, ovulation_day)
    phase_key: menstrual / follicular / ovulation / luteal / unknown
    """
    today = today or date.today()
    day_in_cycle = (today - period_start).days + 1
    if day_in_cycle < 1:
        return "unknown", None

    # 排卵日：优先用存储值，否则按周期长度推算
    ov_day = ovulation_day or (period_start + timedelta(days=max(cycle_length - 14, 10)))

    # 月经期：period_start ~ period_end（未填则默认前 5 天）
    period_end_eff = period_end or (period_start + timedelta(days=4))
    if period_start <= today <= period_end_eff:
        return "menstrual", ov_day

    # 排卵期：排卵日及前后 2 天（共 5 天易孕窗口）
    days_from_ov = (today - ov_day).days
    if -2 <= days_from_ov <= 2:
        return "ovulation", ov_day

    # 卵泡期：月经期结束后 ~ 排卵前
    if day_in_cycle <= 12:
        return "follicular", ov_day

    # 黄体期：排卵后 ~ 下次月经前
    return "luteal", ov_day


def get_phase_diet_tip(phase_key: str) -> dict:
    """获取阶段饮食建议"""
    return PHASE_DIET_TIPS.get(phase_key, {})


def get_phase_context_desc(phase_key: str) -> str | None:
    """获取阶段对应的 AI 上下文描述"""
    return PHASE_CONTEXT_DESC.get(phase_key)
