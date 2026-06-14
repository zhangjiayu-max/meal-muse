"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useDietStore } from "@/stores/diet";
import api from "@/lib/api";
import { CalorieRing } from "@/components/ui/calorie-ring";
import { NutritionRadarChart } from "@/components/ui/nutrition-radar";
import { CardSkeleton, MealCardSkeleton } from "@/components/ui/skeleton";
import {
  Coffee, Sun, Moon, Plus, TrendingUp, Target,
  Droplets, MessageCircle, ChefHat, ArrowRight, Activity, Utensils,
} from "lucide-react";

interface UserInfo {
  nickname: string;
  daily_calorie_target: number | null;
  current_weight: number | null;
  target_weight: number | null;
}

interface WeeklyReport {
  avg_daily_calories: number;
  days_recorded: number;
  ai_summary: string;
}

interface NutritionRadar {
  protein_score: number;
  fat_score: number;
  carbs_score: number;
  fiber_score: number;
  calorie_score: number;
  summary: string;
}

interface CycleInfo {
  current_phase: string;
  phase_diet_tip: { phase_name: string; diet_focus: string; recommended: string[] };
}

const mealConfig = {
  breakfast: { label: "早餐", icon: Coffee, time: "08:00", color: "text-orange-500", bg: "bg-orange-50", border: "border-orange-100" },
  lunch: { label: "午餐", icon: Sun, time: "12:00", color: "text-yellow-500", bg: "bg-yellow-50", border: "border-yellow-100" },
  dinner: { label: "晚餐", icon: Moon, time: "18:00", color: "text-indigo-400", bg: "bg-indigo-50", border: "border-indigo-100" },
};

export default function HomePage() {
  const router = useRouter();
  const { todaySummary, fetchToday } = useDietStore();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [weekly, setWeekly] = useState<WeeklyReport | null>(null);
  const [radar, setRadar] = useState<NutritionRadar | null>(null);
  const [cycle, setCycle] = useState<CycleInfo | null>(null);

  useEffect(() => {
    // 从 localStorage 读取用户信息
    try {
      const userStr = localStorage.getItem("user");
      if (userStr) {
        setUser(JSON.parse(userStr));
      }
    } catch {}

    fetchToday();
    api.get("/users/profile").then(({ data }) => setUser(data)).catch(() => {});
    api.get("/reports/weekly").then(({ data }) => setWeekly(data)).catch(() => {});
    api.get("/reports/nutrition-radar").then(({ data }) => setRadar(data)).catch(() => {});
    api.get("/menstrual/current").then(({ data }) => setCycle(data)).catch(() => {});
  }, [fetchToday]);

  const calorieTarget = user?.daily_calorie_target || 1580;
  const currentCal = todaySummary?.total_calories || 0;
  const now = new Date().getHours();
  const greeting = now < 9 ? "早上好 ☀️" : now < 12 ? "上午好" : now < 14 ? "中午好 🌞" : now < 18 ? "下午好 🌤️" : now < 21 ? "晚上好 🌆" : "夜深了 🌙";

  if (!user) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-7 w-40 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 w-28 bg-gray-100 rounded animate-pulse mt-2" />
          </div>
        </div>
        <CardSkeleton />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MealCardSkeleton />
          <MealCardSkeleton />
          <MealCardSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{greeting}，{user.nickname} 👋</h1>
          <p className="text-sm text-gray-500 mt-1">今天也要好好吃饭哦</p>
        </div>
        <button
          onClick={() => router.push("/record")}
          className="flex items-center gap-2 px-4 py-2.5 bg-green-500 text-white rounded-xl font-medium hover:bg-green-600 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" /> 快速记录
        </button>
      </div>

      {/* Empty State — no records today */}
      {todaySummary && todaySummary.meal_count === 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
          <div className="text-6xl mb-4">🍽️</div>
          <h2 className="text-lg font-bold text-gray-900 mb-2">今天还没记录</h2>
          <p className="text-sm text-gray-500 mb-6">试试告诉 AI 你吃了什么</p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => router.push("/record")}
              className="px-5 py-2.5 bg-green-500 text-white rounded-xl text-sm font-medium hover:bg-green-600 transition-colors"
            >
              开始记录
            </button>
            <button
              onClick={() => router.push("/plan")}
              className="px-5 py-2.5 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors"
            >
              生成计划
            </button>
          </div>
          <div className="mt-6 bg-amber-50 rounded-xl p-3 inline-block">
            <p className="text-xs text-amber-700">💡 每天记录饮食，AI 会越来越懂你</p>
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-4">
          {/* Calorie Overview */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-gray-900">📊 今日营养</h2>
              <span className="text-sm text-gray-400">{todaySummary?.meal_count || 0} 餐已记录</span>
            </div>
            <div className="flex items-center gap-8">
              {/* Calorie Ring */}
              <CalorieRing consumed={currentCal} target={calorieTarget} />
              {/* Macros */}
              <div className="flex-1 grid grid-cols-3 gap-4">
                {[
                  { label: "蛋白质", value: Math.round(todaySummary?.total_protein || 0), target: 60, unit: "g", color: "text-green-600" },
                  { label: "碳水", value: Math.round(todaySummary?.total_carbs || 0), target: 200, unit: "g", color: "text-blue-600" },
                  { label: "脂肪", value: Math.round(todaySummary?.total_fat || 0), target: 55, unit: "g", color: "text-orange-500" },
                ].map((n) => (
                  <div key={n.label}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-500">{n.label}</span>
                      <span className={`text-xs font-medium ${n.color}`}>{n.value}{n.unit}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div className="bg-green-500 h-1.5 rounded-full transition-all"
                        style={{ width: `${Math.min(100, Math.round(n.value / n.target * 100))}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Meal Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(["breakfast", "lunch", "dinner"] as const).map((type) => {
              const meal = todaySummary?.records?.find((r) => r.meal_type === type);
              const config = mealConfig[type];
              const Icon = config.icon;
              return (
                <div key={type} className={`bg-white rounded-2xl border ${config.border} p-4 hover:shadow-md transition-shadow cursor-pointer`}
                  onClick={() => router.push("/record")}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className={`w-8 h-8 ${config.bg} rounded-lg flex items-center justify-center`}>
                        <Icon className={`w-4 h-4 ${config.color}`} />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900">{config.label}</p>
                        <p className="text-[10px] text-gray-400">{config.time}</p>
                      </div>
                    </div>
                    {meal && <span className="text-[10px] bg-green-50 text-green-600 px-2 py-0.5 rounded-full">已记录</span>}
                  </div>
                  {meal ? (
                    <div>
                      <p className="text-sm text-gray-700 line-clamp-2 mb-1">{meal.food_text}</p>
                      <p className="text-xs text-gray-400">🔥 {meal.total_calories} kcal</p>
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <p className="text-xs text-gray-400 mb-2">未记录</p>
                      <span className="text-xs text-green-600 flex items-center gap-1 justify-center">
                        <Plus className="w-3 h-3" /> 记录{config.label}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-2 gap-4">
            <button onClick={() => router.push("/plan")}
              className="bg-white rounded-2xl border border-gray-100 p-4 flex items-center gap-3 hover:shadow-md transition-shadow text-left group">
              <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center">
                <ChefHat className="w-5 h-5 text-green-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-900">餐食计划</p>
                <p className="text-xs text-gray-400">AI 生成今日三餐</p>
              </div>
              <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-green-500 transition-colors" />
            </button>
            <button onClick={() => router.push("/chat")}
              className="bg-white rounded-2xl border border-gray-100 p-4 flex items-center gap-3 hover:shadow-md transition-shadow text-left group">
              <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                <MessageCircle className="w-5 h-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-900">AI 健康助手</p>
                <p className="text-xs text-gray-400">个性化饮食建议</p>
              </div>
              <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-blue-500 transition-colors" />
            </button>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-4">
          {/* Weekly Summary */}
          {weekly && (
            <div className="bg-white rounded-2xl border border-gray-100 p-5">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-4 h-4 text-green-500" />
                <h3 className="text-sm font-semibold text-gray-900">本周概览</h3>
              </div>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-green-50 rounded-xl p-3 text-center">
                  <p className="text-xl font-bold text-green-700">{Math.round(weekly.avg_daily_calories)}</p>
                  <p className="text-[10px] text-green-600">日均热量 kcal</p>
                </div>
                <div className="bg-blue-50 rounded-xl p-3 text-center">
                  <p className="text-xl font-bold text-blue-700">{weekly.days_recorded}</p>
                  <p className="text-[10px] text-blue-600">记录天数</p>
                </div>
              </div>
              <p className="text-xs text-gray-500 bg-gray-50 rounded-lg p-3">{weekly.ai_summary}</p>
            </div>
          )}

          {/* Nutrition Radar */}
          {radar && (
            <div className="bg-white rounded-2xl border border-gray-100 p-5">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 text-purple-500" />
                <h3 className="text-sm font-semibold text-gray-900">营养评分</h3>
              </div>
              <NutritionRadarChart scores={radar} />
              <p className="text-xs text-gray-500 mt-2 bg-gray-50 rounded-lg p-2">{radar.summary}</p>
            </div>
          )}

          {/* Cycle Phase */}
          {cycle && (
            <div className="bg-pink-50 rounded-2xl border border-pink-100 p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Droplets className="w-4 h-4 text-pink-500" />
                  <h3 className="text-sm font-semibold text-pink-800">{cycle.phase_diet_tip.phase_name}</h3>
                </div>
                <button onClick={() => router.push("/menstrual")} className="text-xs text-pink-600 hover:underline">
                  详情 →
                </button>
              </div>
              <p className="text-xs text-pink-700 mb-2">{cycle.phase_diet_tip.diet_focus}</p>
              <div className="flex flex-wrap gap-1">
                {cycle.phase_diet_tip.recommended?.slice(0, 5).map((f) => (
                  <span key={f} className="text-[10px] bg-pink-100 text-pink-700 px-2 py-0.5 rounded-full">{f}</span>
                ))}
              </div>
            </div>
          )}

          {/* Target Progress */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-4 h-4 text-gray-500" />
              <h3 className="text-sm font-semibold text-gray-900">目标进度</h3>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">当前体重</span>
                <span className="font-medium">{user.current_weight || "未填写"} kg</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">目标体重</span>
                <span className="font-medium">{user.target_weight || "未设置"} kg</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">每日热量</span>
                <span className="font-medium">{calorieTarget} kcal</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
