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
import { calculateDailyScore } from "@/lib/shokling";
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

    set({
      stage,
      totalDays,
      streakDays,
      score,
      nextStage,
      progress,
      greeting,
      mood: hasRecord ? "happy" : "sad",
      lastFeedback: null,
    });
  },

  onRecord: (summary, foodText) => {
    const { stage: oldStage } = get();
    const { streakDays: s } = getStreakFromStorage();
    const newStreak = s + 1;
    const newTotalDays = s + 1;

    saveStreakToStorage(newTotalDays, newStreak);

    const score = calculateDailyScore(summary);
    const newStage = getCurrentStage(newTotalDays, score);

    // 从摘要中取第一条记录的热量
    const firstRecord = summary.records?.[0];
    const hasVeg = ["菜", "蔬菜", "沙拉", "青菜", "菠菜", "西兰花"].some((k) => foodText.includes(k));

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
    const result: FeedbackMessage = evolved
      ? { mood: "evolve", message: newStage.unlockedMessage }
      : feedback;

    set({
      mood,
      stage: newStage,
      score,
      totalDays: newTotalDays,
      streakDays: newStreak,
      nextStage: getNextStage(newTotalDays, score),
      progress: getEvolutionProgress(newTotalDays, score),
      lastFeedback: result,
    });

    return result;
  },

  getEmptyMessage: () => {
    const { stage } = get();
    return getEmptyStateMessage(stage.emoji);
  },

  setMood: (mood) => set({ mood }),
}));
