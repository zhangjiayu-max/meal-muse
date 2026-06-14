import type { DailyDietSummary } from "@/types";

/** 计算单日营养评分 0-100 */
export function calculateDailyScore(summary: DailyDietSummary): number {
  const proteinScore = Math.min(1, summary.total_protein / 60);
  const fiberScore = Math.min(1, summary.total_fiber / 25);
  const varietyScore = Math.min(1, (summary.records?.length || 0) / 8);
  const mealTypes = new Set(summary.records?.map((r) => r.meal_type) || []);
  const regularityScore = mealTypes.size >= 3 ? 1 : mealTypes.size === 2 ? 0.7 : mealTypes.size === 1 ? 0.4 : 0;

  const score = (proteinScore * 0.3 + fiberScore * 0.2 + varietyScore * 0.2 + regularityScore * 0.3) * 100;
  return Math.round(Math.min(100, score));
}

/** 粗略判断食物文本中是否包含蔬菜 */
export function hasVegetable(foodText: string): boolean {
  const vegKeywords = [
    "菜", "蔬", "叶", "瓜", "番茄", "西红柿", "黄瓜", "生菜",
    "青椒", "彩椒", "菠菜", "西兰花", "花菜", "豆角", "茄子",
    "莴笋", "芹菜", "韭菜", "白菜", "青菜", "空心菜",
    "沙拉", "菌", "菇", "木耳", "海带", "紫菜",
  ];
  return vegKeywords.some((kw) => foodText.includes(kw));
}
