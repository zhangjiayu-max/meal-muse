# 食灵（Shokling）角色体系 — Phase 1 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 MealMuse 前端实现食灵角色体系 Phase 1，包括角色组件、文案引擎、首页/记录页/AI对话页的集成。

**Architecture:** 纯前端改动，无后端依赖。使用 Zustand store 管理状态，useDietStore 中的 todaySummary 驱动表情和文案选择。组件采用 emoji + CSS 视觉方案，后续可替换为设计稿。

**Tech Stack:** Next.js 16 / React 19 / Zustand / TypeScript / Tailwind CSS 4

---

## File Structure

```
components/ui/shokling/
├── shokling.tsx          # 角色展示组件（emoji 表情 + 形态）
├── shokling-bubble.tsx   # 角色气泡对话框
├── evolution.ts          # 进化阶段数据定义
└── index.ts              # 统一导出

lib/shokling/
├── messages.ts           # 场景化文案模板
├── score.ts              # 营养评分 + 进化判定
└── index.ts

stores/shokling.ts        # 食灵状态管理（mood + stage + message）

Modified:
- app/(main)/page.tsx         # 首页：问候区 + 空状态
- app/(main)/record/page.tsx  # 记录页：提交后反馈
- app/(main)/chat/page.tsx    # 对话页：AI 头像
```

---

### Task 1: 创建进化阶段数据定义

**Files:**
- Create: `components/ui/shokling/evolution.ts`

- [ ] **Step 1: Write `evolution.ts`**

```ts
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
```

- [ ] **Step 2: Verify TypeScript**

Run: `npx tsc --noEmit 2>&1 | grep -c "shokling/evolution"` — expect 0 errors.

- [ ] **Step 3: Commit**

```bash
git add meal-muse-web/components/ui/shokling/evolution.ts
git commit -m "feat: add shokling evolution data definitions"
```

---

### Task 2: 创建场景化文案模板引擎

**Files:**
- Create: `lib/shokling/messages.ts`

- [ ] **Step 1: Write `messages.ts`**

```ts
/** 食灵场景化文案模板 */

type TimePeriod = "morning" | "noon" | "afternoon" | "evening" | "night";

function getTimePeriod(): TimePeriod {
  const h = new Date().getHours();
  if (h < 9) return "morning";
  if (h < 12) return "noon";
  if (h < 14) return "afternoon";
  if (h < 19) return "evening";
  return "night";
}

/** 随机取一条文案 */
function pick(messages: string[]): string {
  return messages[Math.floor(Math.random() * messages.length)];
}

/** 首页问候文案 */
export function getGreeting(nickname: string, hasRecord: boolean, streakDays: number, stageEmoji: string): string {
  const period = getTimePeriod();
  const timeGreetings: Record<TimePeriod, string[]> = {
    morning: ["早呀！新的一天从好吃的开始 ☀️", "早安！今天想吃什么呢？", "早上好呀，你的食灵已经醒了～"],
    noon: ["上午好！别忘了吃午餐哦 🍱", "记得按时吃饭！你的食灵在等你～"],
    afternoon: ["下午好！来点健康的下午茶吧 🫖", "加油！一天还没有记录饮食哦"],
    evening: ["晚上了！今天吃得怎么样呀 🌆", "晚餐时间到～今天有好好吃饭吗？"],
    night: ["这么晚了还没睡呀 🌙", "深夜了…你的食灵在打哈欠 😴", "记得早点休息，明天也要好好吃饭哦"],
  };

  if (hasRecord) {
    return `${pick(timeGreetings[period])} ${nickname}！今天已经记录了 ${streakDays > 0 ? `${streakDays} 天啦` : "很棒哦"} ${stageEmoji}`;
  }
  return `${pick(timeGreetings[period])} ${nickname}～今天还没记录呢，我等了一整天了😢`;
}

/** 记录后的反馈文案（基于营养分析） */
export function getRecordFeedback(
  calories: number,
  protein: number,
  carbs: number,
  fat: number,
  hasVegetable: boolean,
): { mood: "happy" | "embarrassed" | "fire" | "celebrate"; message: string } {
  const proteinOk = protein >= 20;
  const hasVeg = hasVegetable;

  if (proteinOk && hasVeg) {
    return {
      mood: "fire",
      message: pick([
        `💪 蛋白质 ${Math.round(protein)}g！你是懂营养的！`,
        `这搭配也太健康了吧！蛋白质在跳舞 💃`,
        `优质蛋白 + 蔬菜，完美搭配！继续保持 👏`,
      ]),
    };
  }
  if (calories > 800) {
    return {
      mood: "embarrassed",
      message: pick([
        `🔥 ${calories}kcal！这一餐热量有点高哦 😅`,
        `哇这一顿够猛的…偶尔放纵一下也可以啦～`,
        `热量炸弹 💣 不过开心最重要！明天吃清淡点就好`,
      ]),
    };
  }
  if (!proteinOk) {
    return {
      mood: "happy",
      message: pick([
        `记下来就好！下次可以加个蛋白质来源哦 💪`,
        `🍽️ 已记录！如果能再加点肉/蛋/豆腐就更均衡啦`,
        `收到！这一餐蛋白质不太够，建议补充一下～`,
      ]),
    };
  }
  return {
    mood: "happy",
    message: pick([
      `📝 记录成功！今天也在好好吃饭呢 🎉`,
      `收到收到！你的食灵记在小本本上了 ✍️`,
      `${calories}kcal！继续加油，保持好节奏 🌟`,
    ]),
  };
}

/** 空状态引导文案 */
export function getEmptyStateMessage(stageEmoji: string): { mood: "sad" | "happy"; message: string } {
  return {
    mood: "sad",
    message: pick([
      `${stageEmoji} "我等了一整天都没等到你…😢"`,
      `${stageEmoji} "好寂寞…今天还没人给我喂数据呢"`,
      `${stageEmoji} "今天还没记录！快告诉我你吃了什么！"`,
    ]),
  };
}

/** 连续记录里程碑文案 */
export function getStreakMessage(days: number): string | null {
  const milestones: Record<number, string[]> = {
    3: ["连续 3 天！习惯正在养成 💪", "3 天打卡！你已经超过了 50% 的人"],
    7: ["一周了！你打败了 90% 的人 🏆", "连续 7 天！食灵感受到了你的诚意 🥟"],
    14: ["两周！你已经是饮食达人了 🌿", "14 天！你的食灵正在茁壮成长"],
    30: ["一个月！你就是饮食管理大师 👑", "30 天不间断！太强了！🔥"],
  };
  const msgs = milestones[days];
  if (!msgs) return null;
  return pick(msgs);
}
```

- [ ] **Step 2: Commit**

```bash
git add meal-muse-web/lib/shokling/messages.ts
git commit -m "feat: add shokling scene message templates"
```

---

### Task 3: 创建营养评分计算模块

**Files:**
- Create: `lib/shokling/score.ts`
- Create: `lib/shokling/index.ts`

- [ ] **Step 1: Write `score.ts`**

```ts
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
```

- [ ] **Step 2: Write `lib/shokling/index.ts`**

```ts
export { calculateDailyScore, hasVegetable } from "./score";
export { getGreeting, getRecordFeedback, getEmptyStateMessage, getStreakMessage } from "./messages";
```

- [ ] **Step 3: Commit**

```bash
git add meal-muse-web/lib/shokling/
git commit -m "feat: add nutrition score calculator"
```

---

### Task 4: 创建食灵 Zustand Store

**Files:**
- Create: `stores/shokling.ts`

- [ ] **Step 1: Write `stores/shokling.ts`**

```ts
import { create } from "zustand";
import type { DailyDietSummary } from "@/types";
import {
  getCurrentStage,
  getNextStage,
  getEvolutionProgress,
  type ShoklingMood,
  type EvolutionStage,
  EVOLUTION_STAGES,
} from "@/components/ui/shokling/evolution";
import { calculateDailyScore, getStreakMessage } from "@/lib/shokling";
import { getGreeting, getEmptyStateMessage, getRecordFeedback } from "@/lib/shokling";

interface FeedbackMessage {
  mood: ShoklingMood;
  message: string;
}

interface ShoklingState {
  /** 当前 mood（由场景触发更新） */
  mood: ShoklingMood;
  /** 当前进化形态 */
  stage: EvolutionStage;
  /** 累计记录天数 */
  totalDays: number;
  /** 连续记录天数 */
  streakDays: number;
  /** 最近营养评分 */
  score: number;
  /** 下一形态 */
  nextStage: EvolutionStage | null;
  /** 进化进度 0-1 */
  progress: number;
  /** 最近生成的反馈 */
  lastFeedback: FeedbackMessage | null;
  /** 首页问候语 */
  greeting: string;

  /** 每天首次加载时初始化状态 */
  initFromSummary: (summary: DailyDietSummary, nickname: string) => void;
  /** 记录后更新状态并生成反馈 */
  onRecord: (summary: DailyDietSummary, foodText: string) => FeedbackMessage;
  /** 获取空状态文案 */
  getEmptyMessage: () => FeedbackMessage;
  /** 手动设置 mood（用于进化等场景） */
  setMood: (mood: ShoklingMood) => void;
}

/** 从 localStorage 读取 streak 天数，Phase 1 mock */
function getStreakFromStorage(): { totalDays: number; streakDays: number } {
  if (typeof window === "undefined") return { totalDays: 0, streakDays: 0 };
  try {
    const raw = localStorage.getItem("shokling_streak");
    if (raw) return JSON.parse(raw);
  } catch {}
  return { totalDays: 0, streakDays: 0 };
}

function saveStreakToStorage(totalDays: number, streakDays: number) {
  try {
    localStorage.setItem("shokling_streak", JSON.stringify({ totalDays, streakDays }));
  } catch {}
}

export const useShoklingStore = create<ShoklingState>((set, get) => ({
  mood: "happy",
  stage: EVOLUTION_STAGES[0],
  totalDays: 0,
  streakDays: 0,
  score: 0,
  nextStage: null,
  progress: 0,
  lastFeedback: null,
  greeting: "",

  initFromSummary: (summary, nickname) => {
    const { totalDays, streakDays } = getStreakFromStorage();
    const score = calculateDailyScore(summary);
    const stage = getCurrentStage(totalDays, score);
    const nextStage = getNextStage(totalDays, score);
    const progress = getEvolutionProgress(totalDays, score);
    const hasRecord = summary.meal_count > 0;
    const greeting = getGreeting(nickname, hasRecord, streakDays, stage.emoji);

    // 检查里程碑
    const streakMsg = getStreakMessage(streakDays);

    set({
      stage,
      totalDays,
      streakDays,
      score,
      nextStage,
      progress,
      greeting,
      mood: hasRecord ? "happy" : "sad",
      lastFeedback: streakMsg
        ? { mood: "celebrate", message: streakMsg }
        : null,
    });
  },

  onRecord: (summary, foodText) => {
    const { totalDays, streakDays: oldStreak, stage: oldStage } = get();
    const { totalDays: _, streakDays: s } = getStreakFromStorage();
    const newTotalDays = Math.max(totalDays, s + 1);
    const newStreak = oldStreak + 1;

    saveStreakToStorage(newTotalDays, newStreak);

    const score = calculateDailyScore(summary);
    const newStage = getCurrentStage(newTotalDays, score);
    const hasVeg = foodText.includes("菜") || ["蔬菜", "沙拉", "青菜"].some((k) => foodText.includes(k));

    // 从摘要中取第一条记录的热量
    const firstRecord = summary.records?.[0];
    const feedback = getRecordFeedback(
      firstRecord?.total_calories || 0,
      firstRecord?.total_protein || 0,
      firstRecord?.total_carbs || 0,
      firstRecord?.total_fat || 0,
      hasVeg,
    );

    // 检查是否进化
    const evolved = newStage.id !== oldStage.id;
    const mood = evolved ? "evolve" : feedback.mood;

    set({
      mood,
      stage: newStage,
      score,
      totalDays: newTotalDays,
      streakDays: newStreak,
      nextStage: getNextStage(newTotalDays, score),
      progress: getEvolutionProgress(newTotalDays, score),
      lastFeedback: evolved
        ? { mood: "evolve", message: newStage.unlockedMessage }
        : feedback,
    });

    return evolved ? { mood: "evolve", message: newStage.unlockedMessage } : feedback;
  },

  getEmptyMessage: () => {
    const { stage } = get();
    return getEmptyStateMessage(stage.emoji);
  },

  setMood: (mood) => set({ mood }),
}));
```

- [ ] **Step 2: Commit**

```bash
git add meal-muse-web/stores/shokling.ts
git commit -m "feat: add shokling zustand store"
```

---

### Task 5: 创建角色展示组件（Shokling + ShoklingBubble）

**Files:**
- Create: `components/ui/shokling/shokling.tsx`
- Create: `components/ui/shokling/shokling-bubble.tsx`
- Create: `components/ui/shokling/index.ts`

- [ ] **Step 1: Write `shokling.tsx`**

```tsx
"use client";

import { type ShoklingMood, MOOD_EMOJI, MOOD_LABEL } from "./evolution";

interface ShoklingProps {
  mood?: ShoklingMood;
  emoji?: string; // 进化形态 emoji，覆盖 mood
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
  /** 点击回调 */
  onClick?: () => void;
}

const sizeMap = {
  sm: { container: "w-8 h-8 text-lg", label: "text-[10px]" },
  md: { container: "w-12 h-12 text-2xl", label: "text-xs" },
  lg: { container: "w-16 h-16 text-4xl", label: "text-sm" },
};

export function Shokling({
  mood = "happy",
  emoji,
  size = "md",
  showLabel = false,
  className = "",
  onClick,
}: ShoklingProps) {
  const sz = sizeMap[size];
  const displayEmoji = emoji || MOOD_EMOJI[mood];

  return (
    <div
      className={`flex flex-col items-center gap-1 ${onClick ? "cursor-pointer" : ""} ${className}`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div
        className={`
          ${sz.container} rounded-full flex items-center justify-center
          transition-all duration-300 select-none
          ${mood === "happy" ? "bg-green-100" : ""}
          ${mood === "celebrate" ? "bg-yellow-100 scale-110" : ""}
          ${mood === "thinking" ? "bg-blue-100" : ""}
          ${mood === "sleepy" ? "bg-indigo-100" : ""}
          ${mood === "embarrassed" ? "bg-red-100" : ""}
          ${mood === "fire" ? "bg-orange-100" : ""}
          ${mood === "sad" ? "bg-gray-100" : ""}
          ${mood === "evolve" ? "bg-purple-100 animate-pulse" : ""}
        `}
      >
        {displayEmoji}
      </div>
      {showLabel && (
        <span className={`${sz.label} text-gray-400`}>
          {MOOD_LABEL[mood]}
        </span>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Write `shokling-bubble.tsx`**

```tsx
"use client";

import { motion } from "framer-motion";
import { Shokling } from "./shokling";
import type { ShoklingMood } from "./evolution";

interface ShoklingBubbleProps {
  mood?: ShoklingMood;
  emoji?: string;
  message: string;
  /** bubble 位置：left = 食灵在左，right = 食灵在右 */
  side?: "left" | "right";
  size?: "sm" | "md" | "lg";
  className?: string;
  /** 是否显示入场动画 */
  animate?: boolean;
  /** 点击食灵 */
  onShoklingClick?: () => void;
}

export function ShoklingBubble({
  mood = "happy",
  emoji,
  message,
  side = "left",
  size = "md",
  className = "",
  animate = true,
  onShoklingClick,
}: ShoklingBubbleProps) {
  const content = (
    <div
      className={`flex items-start gap-3 ${side === "right" ? "flex-row-reverse" : ""} ${className}`}
    >
      <Shokling mood={mood} emoji={emoji} size={size} onClick={onShoklingClick} />
      <div
        className={`
          relative flex-1 px-4 py-3 rounded-2xl text-sm leading-relaxed
          ${side === "left" ? "bg-gray-100 text-gray-800 rounded-tl-sm" : "bg-green-500 text-white rounded-tr-sm"}
        `}
      >
        {message}
      </div>
    </div>
  );

  if (animate) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {content}
      </motion.div>
    );
  }

  return content;
}
```

- [ ] **Step 3: Write `components/ui/shokling/index.ts`**

```ts
export { Shokling } from "./shokling";
export { ShoklingBubble } from "./shokling-bubble";
export {
  EVOLUTION_STAGES,
  MOOD_EMOJI,
  type ShoklingMood,
  type EvolutionStage,
  getCurrentStage,
  getNextStage,
  getEvolutionProgress,
} from "./evolution";
```

- [ ] **Step 4: Verify compilation**

Run: `npx tsc --noEmit 2>&1 | grep -c "shokling"` — expect 0 errors.

- [ ] **Step 5: Commit**

```bash
git add meal-muse-web/components/ui/shokling/
git commit -m "feat: create shokling avatar and bubble components"
```

---

### Task 6: 首页集成 — 替换问候区 + 空状态

**Files:**
- Modify: `app/(main)/page.tsx`

- [ ] **Step 1: 添加 import**

在 `page.tsx` 文件顶部，把目前的：

```tsx
import { Coffee, Sun, Moon, Plus, TrendingUp, Target,
  Droplets, MessageCircle, ChefHat, ArrowRight, Activity, Utensils,
} from "lucide-react";
```

改为：

```tsx
import {
  Coffee, Sun, Moon, Plus, TrendingUp, Target,
  Droplets, MessageCircle, ChefHat, ArrowRight, Activity, Utensils,
} from "lucide-react";
import { useShoklingStore } from "@/stores/shokling";
import { Shokling, ShoklingBubble } from "@/components/ui/shokling";
```

- [ ] **Step 2: 在组件内初始化食灵状态**

在 `HomePage` 组件函数体内，`fetchToday()` 调用之后，添加：

```tsx
const {
  greeting, stage, nextStage, progress,
  lastFeedback, initFromSummary, getEmptyMessage,
} = useShoklingStore();

// 在 fetchToday 成功后初始化食灵
useEffect(() => {
  if (todaySummary) {
    initFromSummary(todaySummary, user?.nickname || "用户");
  }
}, [todaySummary, user?.nickname, initFromSummary]);
```

- [ ] **Step 3: 替换问候区（约 98-110 行）**

将原来的：

```tsx
{/* Greeting */}
<div className="flex items-center justify-between">
  <div>
    <h1 className="text-2xl font-bold text-gray-900">{greeting}，{user.nickname} 👋</h1>
    <p className="text-sm text-gray-500 mt-1">今天也要好好吃饭哦</p>
  </div>
  <button onClick={() => router.push("/record")}
    className="flex items-center gap-2 px-4 py-2.5 bg-green-500 text-white rounded-xl font-medium hover:bg-green-600 transition-colors shadow-sm"
  >
    <Plus className="w-4 h-4" /> 快速记录
  </button>
</div>
```

替换为：

```tsx
{/* Greeting — 食灵问候 */}
<div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
  <div className="flex items-start justify-between">
    <div className="flex-1 min-w-0">
      <ShoklingBubble
        mood={todaySummary?.meal_count ? "happy" : "sad"}
        emoji={stage.emoji}
        message={greeting}
        size="md"
        animate
      />
      {/* 进化进度条 */}
      {nextStage && (
        <div className="mt-3 ml-14">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-400">
              {stage.name} → {nextStage.name}
            </span>
            <span className="text-xs text-gray-400">
              {Math.round(progress * 100)}%
            </span>
          </div>
          <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-400 to-green-500 rounded-full transition-all duration-700"
              style={{ width: `${progress * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
    <button onClick={() => router.push("/record")}
      className="shrink-0 ml-4 px-4 py-2.5 bg-green-500 text-white rounded-xl font-medium hover:bg-green-600 transition-colors shadow-sm"
    >
      <Plus className="w-4 h-4" /> 快速记录
    </button>
  </div>
</div>
```

- [ ] **Step 4: 替换空状态（约 112-136 行）**

将原来的：

```tsx
{/* Empty State — no records today */}
{todaySummary && todaySummary.meal_count === 0 && (
  <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
    <div className="text-6xl mb-4">🍽️</div>
    <h2 className="text-lg font-bold text-gray-900 mb-2">今天还没记录</h2>
    <p className="text-sm text-gray-500 mb-6">试试告诉 AI 你吃了什么</p>
    ...
  </div>
)}
```

替换为：

```tsx
{/* Empty State — 食灵引导 */}
{todaySummary && todaySummary.meal_count === 0 && (
  <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
    <ShoklingBubble
      mood="sad"
      emoji={stage.emoji}
      message={`"我等了一整天都没等到你…😢"`}
      side="left"
      size="lg"
      animate
      className="justify-center mb-4"
    />
    <p className="text-xs text-gray-400 mt-2 mb-6">"现在记录还来得及！我给你准备了小惊喜哦 ✨"</p>
    <div className="flex items-center justify-center gap-3">
      <button onClick={() => router.push("/record")}
        className="px-5 py-2.5 bg-green-500 text-white rounded-xl text-sm font-medium hover:bg-green-600 transition-colors"
      >
        开始记录
      </button>
      <button onClick={() => router.push("/plan")}
        className="px-5 py-2.5 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors"
      >
        生成计划
      </button>
    </div>
  </div>
)}
```

- [ ] **Step 5: 验证首页编译**

Run: `npx tsc --noEmit 2>&1 | grep -c "page.tsx"` — expect same count as before (pre-existing errors only).

- [ ] **Step 6: Commit**

```bash
git add meal-muse-web/app/\(main\)/page.tsx
git commit -m "feat: integrate shokling into homepage greeting and empty state"
```

---

### Task 7: 记录页集成 — 提交后反馈

**Files:**
- Modify: `app/(main)/record/page.tsx`

- [ ] **Step 1: 添加 import**

```tsx
import { useShoklingStore } from "@/stores/shokling";
import { ShoklingBubble } from "@/components/ui/shokling";
```

- [ ] **Step 2: 添加 store 引用和反馈状态**

在组件函数体内，`const [saving, setSaving] = useState(false);` 之后添加：

```tsx
const { onRecord } = useShoklingStore();
const [recordFeedback, setRecordFeedback] = useState<{ mood: "happy" | "embarrassed" | "fire" | "celebrate"; message: string } | null>(null);
```

- [ ] **Step 3: 在提交成功后添加反馈（替换原来的 toast）**

在 `handleSubmit` 函数中，将 `await fetchToday()` 之后的：

```tsx
setFoodText("");
await fetchToday();
toast("success", "记录成功 🎉");
```

改为：

```tsx
setFoodText("");
await fetchToday();
// 触发食灵反馈
if (todaySummary) {
  const feedback = onRecord(todaySummary, foodText.trim());
  setRecordFeedback(feedback);
}
toast("success", "记录成功 🎉");
```

- [ ] **Step 4: 在提交按钮下方添加反馈展示**

在提交卡片 `</div>` 关闭标签之后、当前餐次营养小计之前，添加：

```tsx
{/* 食灵反馈 */}
{recordFeedback && (
  <ShoklingBubble
    mood={recordFeedback.mood}
    message={recordFeedback.message}
    size="sm"
    className="mb-2"
    animate
  />
)}
```

- [ ] **Step 5: Commit**

```bash
git add meal-muse-web/app/\(main\)/record/page.tsx
git commit -m "feat: add shokling post-record feedback on record page"
```

---

### Task 8: AI 对话页 — 替换头像

**Files:**
- Modify: `app/(main)/chat/page.tsx`

- [ ] **Step 1: 添加 import**

```tsx
import { Shokling } from "@/components/ui/shokling";
```

- [ ] **Step 2: 替换 AI 消息的头像图标**

找到约 213-216 行：

```tsx
{msg.role === "assistant" && (
  <div className="w-7 h-7 bg-green-100 rounded-full flex items-center justify-center shrink-0">
    <Bot className="w-4 h-4 text-green-600" />
  </div>
)}
```

替换为：

```tsx
{msg.role === "assistant" && (
  <Shokling mood={sending && i === messages.length - 1 ? "thinking" : "happy"} size="sm" />
)}
```

- [ ] **Step 3: 替换 loading 状态的头像**

找到约 238-239 行：

```tsx
<div className="w-8 h-8 rounded-full bg-[var(--ai)] flex items-center justify-center text-white text-sm">
  🤖
</div>
```

替换为：

```tsx
<Shokling mood="thinking" size="md" />
```

- [ ] **Step 4: 替换初始 AI 问候语第一条消息的 mood**

在 `handleNewChat` 函数里：

目前的：
```tsx
role: "assistant",
content: "你好！我是你的 AI 饮食健康助手 🌿\n\n..."
```

改为：
```tsx
role: "assistant",
content: "你好呀！我是你的食灵 🥟\n\n我会根据你的饮食记录，为你提供个性化的健康建议。有什么想问的吗？"
```

同样更新 `useState` 初始值中的第一条消息。

- [ ] **Step 5: Commit**

```bash
git add meal-muse-web/app/\(main\)/chat/page.tsx
git commit -m "feat: integrate shokling avatar into AI chat page"
```

---

## Verification

1. Run `npx tsc --noEmit` — only pre-existing errors, no new errors from our changes
2. Run `npm run dev` — app starts without crash
3. Open homepage — see shokling greeting bubble with progress bar
4. If no records today — see sad shokling with encouragement
5. Navigate to record page, submit a meal — see shokling feedback bubble
6. Navigate to chat page — see shokling avatar instead of Bot icon
7. Test building: `npm run build` — successful build
