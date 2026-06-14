"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import api from "@/lib/api";
import { TrendingUp, Target, Activity } from "lucide-react";

interface DailyReport {
  date: string;
  total_calories: number;
  total_protein: number;
  total_fat: number;
  total_carbs: number;
  total_fiber: number;
  meal_count: number;
  calorie_target: number | null;
  calorie_diff: number | null;
  status: string;
}

interface WeeklyReport {
  week_start: string;
  week_end: string;
  avg_daily_calories: number;
  avg_daily_protein: number;
  avg_daily_fat: number;
  avg_daily_carbs: number;
  days_recorded: number;
  total_meals: number;
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

export default function ReportPage() {
  const router = useRouter();

  const [tab, setTab] = useState<"daily" | "weekly">("daily");
  const [daily, setDaily] = useState<DailyReport | null>(null);
  const [weekly, setWeekly] = useState<WeeklyReport | null>(null);
  const [radar, setRadar] = useState<NutritionRadar | null>(null);

  useEffect(() => {
    api.get("/reports/daily").then(({ data }) => setDaily(data)).catch(() => {});
    api.get("/reports/weekly").then(({ data }) => setWeekly(data)).catch(() => {});
    api.get("/reports/nutrition-radar").then(({ data }) => setRadar(data)).catch(() => {});
  }, []);

  const nutrients = radar ? [
    { label: "蛋白质", score: radar.protein_score, color: "#22c55e" },
    { label: "脂肪", score: radar.fat_score, color: "#f59e0b" },
    { label: "碳水", score: radar.carbs_score, color: "#3b82f6" },
    { label: "膳食纤维", score: radar.fiber_score, color: "#8b5cf6" },
  ] : [];

  return (
    <div className="flex flex-col  ">
      <header className="flex items-center justify-between">
        
        <h1 className="text-lg font-bold text-gray-900">健康报告</h1>
      </header>

      {/* Tabs */}
      <div className="flex gap-2 px-4 py-3">
        {(["daily", "weekly"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${tab === t ? "bg-green-500 text-white" : "bg-gray-100 text-gray-600"}`}>
            {t === "daily" ? "今日" : "本周"}
          </button>
        ))}
      </div>

      <main className="flex-1 px-4 py-2 space-y-4 pb-20">
        {tab === "daily" && daily && (
          <>
            <div className="bg-gray-50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-5 h-5 text-green-500" />
                <h2 className="font-semibold text-gray-900">热量达标情况</h2>
              </div>
              <div className="flex items-end gap-2 mb-2">
                <span className="text-3xl font-bold text-gray-900">{daily.total_calories}</span>
                <span className="text-sm text-gray-400 mb-1">/ {daily.calorie_target} kcal</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div className="bg-green-500 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, Math.round(daily.total_calories / (daily.calorie_target || 1580) * 100))}%` }} />
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${daily.status === "达标" ? "bg-green-100 text-green-700" : daily.status === "超标" ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700"}`}>
                {daily.status}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "蛋白质", value: `${Math.round(daily.total_protein)}g`, color: "text-green-600" },
                { label: "碳水", value: `${Math.round(daily.total_carbs)}g`, color: "text-blue-600" },
                { label: "脂肪", value: `${Math.round(daily.total_fat)}g`, color: "text-orange-600" },
                { label: "膳食纤维", value: `${Math.round(daily.total_fiber)}g`, color: "text-purple-600" },
              ].map((n) => (
                <div key={n.label} className="bg-gray-50 rounded-xl p-3 text-center">
                  <p className={`text-xl font-bold ${n.color}`}>{n.value}</p>
                  <p className="text-xs text-gray-500">{n.label}</p>
                </div>
              ))}
            </div>

            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-sm text-gray-600">今日记录 {daily.meal_count} 餐</p>
            </div>
          </>
        )}

        {tab === "weekly" && weekly && (
          <>
            <div className="bg-green-50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                <h2 className="font-semibold text-green-800">本周概览</h2>
              </div>
              <p className="text-xs text-green-600 mb-3">{weekly.week_start} ~ {weekly.week_end}</p>
              <div className="grid grid-cols-2 gap-3 text-center">
                <div>
                  <p className="text-2xl font-bold text-green-700">{Math.round(weekly.avg_daily_calories)}</p>
                  <p className="text-xs text-green-600">日均热量 kcal</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-700">{weekly.days_recorded}</p>
                  <p className="text-xs text-green-600">记录天数</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "日均蛋白质", value: `${Math.round(weekly.avg_daily_protein)}g` },
                { label: "日均碳水", value: `${Math.round(weekly.avg_daily_carbs)}g` },
                { label: "日均脂肪", value: `${Math.round(weekly.avg_daily_fat)}g` },
              ].map((n) => (
                <div key={n.label} className="bg-gray-50 rounded-xl p-3 text-center">
                  <p className="text-lg font-bold text-gray-900">{n.value}</p>
                  <p className="text-xs text-gray-500">{n.label}</p>
                </div>
              ))}
            </div>

            {radar && (
              <div className="border border-gray-100 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Activity className="w-5 h-5 text-indigo-500" />
                  <h3 className="font-semibold text-gray-900">营养评分</h3>
                </div>
                <div className="space-y-2">
                  {nutrients.map((n) => (
                    <div key={n.label} className="flex items-center gap-2">
                      <span className="text-xs text-gray-500 w-16">{n.label}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-2">
                        <div className="h-2 rounded-full transition-all" style={{ width: `${n.score}%`, backgroundColor: n.color }} />
                      </div>
                      <span className="text-xs text-gray-400 w-8 text-right">{n.score}%</span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-3">{radar.summary}</p>
              </div>
            )}

            <div className="bg-blue-50 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-blue-800 mb-2">💡 AI 周报</h3>
              <p className="text-sm text-blue-700">{weekly.ai_summary}</p>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
