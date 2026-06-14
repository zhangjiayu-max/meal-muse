/** 食灵进化阶段定义 */

export interface EvolutionStage {
  id: string;
  emoji: string;
  name: string;
  description: string;
  /** 最低累计记录天数 */
  requiredDays: number;
  /** 最低营养均分（moving avg），0 表示不要求 */
  requiredScore: number;
  /** 解锁提示文案 */
  unlockedMessage: string;
}

/** 8 种表情 mood */
export type ShoklingMood =
  | "happy"
  | "celebrate"
  | "thinking"
  | "sleepy"
  | "embarrassed"
  | "fire"
  | "sad"
  | "evolve";

/** 表情 → emoji 映射 */
export const MOOD_EMOJI: Record<ShoklingMood, string> = {
  happy: "😊",
  celebrate: "🎉",
  thinking: "🤔",
  sleepy: "😴",
  embarrassed: "😅",
  fire: "🔥",
  sad: "😢",
  evolve: "✨",
};

/** 表情 → 显示文案 */
export const MOOD_LABEL: Record<ShoklingMood, string> = {
  happy: "开心",
  celebrate: "庆祝",
  thinking: "思考中",
  sleepy: "困了",
  embarrassed: "有点尴尬",
  fire: "干劲满满",
  sad: "沮丧",
  evolve: "进化！",
};

/** 完整进化树 */
export const EVOLUTION_STAGES: EvolutionStage[] = [
  {
    id: "egg",
    emoji: "🥚",
    name: "食灵蛋",
    description: "刚刚降临的食灵，还在蛋里",
    requiredDays: 0,
    requiredScore: 0,
    unlockedMessage: "🥚 一颗蛋出现在你的手机里…食灵降生了！",
  },
  {
    id: "xiaolongbao",
    emoji: "🥟",
    name: "小笼包",
    description: "圆滚滚的小笼包，充满好奇心",
    requiredDays: 3,
    requiredScore: 0,
    unlockedMessage: "🥟 蛋壳裂开，钻出来一只小笼包！",
  },
  {
    id: "sprout",
    emoji: "🌱",
    name: "嫩芽灵",
    description: "刚冒出头的小嫩芽，充满生机",
    requiredDays: 7,
    requiredScore: 0,
    unlockedMessage: "🌱 小笼包长出了嫩芽！它在努力长大～",
  },
  {
    id: "leaf",
    emoji: "🌿",
    name: "绿叶灵",
    description: "茂盛的绿叶精灵，健康的象征",
    requiredDays: 14,
    requiredScore: 60,
    unlockedMessage: "🌿 哇！绿叶灵诞生了！你最近的饮食很健康哦！",
  },
  {
    id: "fire",
    emoji: "🔥",
    name: "火花灵",
    description: "燃烧的火花，充满能量",
    requiredDays: 30,
    requiredScore: 70,
    unlockedMessage: "🔥 火花灵！你的坚持在闪闪发光！",
  },
  {
    id: "star",
    emoji: "⭐",
    name: "星辰灵",
    description: "像星星一样闪耀的食灵",
    requiredDays: 60,
    requiredScore: 80,
    unlockedMessage: "⭐ 你是星辰！食灵与你一同闪耀！",
  },
  {
    id: "rainbow",
    emoji: "🌈",
    name: "彩虹灵",
    description: "终极形态，彩虹般的完美食灵",
    requiredDays: 100,
    requiredScore: 85,
    unlockedMessage: "🌈 彩虹灵！你已经是饮食管理的大师了！",
  },
];

/** 根据累计天数和营养均分获取当前形态 */
export function getCurrentStage(days: number, score: number): EvolutionStage {
  let current = EVOLUTION_STAGES[0];
  for (const stage of EVOLUTION_STAGES) {
    if (days >= stage.requiredDays && score >= stage.requiredScore) {
      current = stage;
    }
  }
  return current;
}

/** 获取下一形态（可能为 null） */
export function getNextStage(days: number, score: number): EvolutionStage | null {
  const currentId = getCurrentStage(days, score).id;
  const currentIndex = EVOLUTION_STAGES.findIndex((s) => s.id === currentId);
  if (currentIndex < EVOLUTION_STAGES.length - 1) {
    return EVOLUTION_STAGES[currentIndex + 1];
  }
  return null;
}

/** 计算进化进度 0~1（基于天数比例） */
export function getEvolutionProgress(days: number, score: number): number {
  const next = getNextStage(days, score);
  if (!next) return 1;
  const current = getCurrentStage(days, score);
  const currentReq = current.requiredDays;
  const nextReq = next.requiredDays;
  if (nextReq <= currentReq) return 1;
  return Math.min(1, (days - currentReq) / (nextReq - currentReq));
}
