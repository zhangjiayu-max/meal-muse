"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import api from "@/lib/api";
import { RefreshCw, Coffee, Sun, Moon, Sparkles, ChefHat } from "lucide-react";

interface FoodItem {
  name: string;
  amount: string;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
}

interface MealDetail {
  name: string;
  foods: FoodItem[];
  total_calories: number;
  total_protein: number;
  total_fat: number;
  total_carbs: number;
}

interface MealPlan {
  id: string;
  plan_date: string;
  breakfast: MealDetail | null;
  lunch: MealDetail | null;
  dinner: MealDetail | null;
  total_calories: number;
  ai_note: string | null;
  status: string;
  version: number;
}

const mealConfig = {
  breakfast: { label: "早餐", icon: Coffee, color: "text-orange-400", bg: "bg-orange-50" },
  lunch: { label: "午餐", icon: Sun, color: "text-yellow-500", bg: "bg-yellow-50" },
  dinner: { label: "晚餐", icon: Moon, color: "text-indigo-400", bg: "bg-indigo-50" },
};

export default function PlanPage() {
  const router = useRouter();

  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [adopting, setAdopting] = useState(false);

  const fetchPlan = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/meals/plan");
      setPlan(data);
    } catch { /* no plan yet */ }
    setLoading(false);
  };

  const generatePlan = async () => {
    setGenerating(true);
    try {
      const { data } = await api.post("/meals/generate", {});
      setPlan(data);
    } catch { alert("生成失败"); }
    setGenerating(false);
  };

  const replaceMeal = async (mealType: string) => {
    if (!plan) return;
    try {
      const { data } = await api.post(`/meals/${plan.id}/replace?meal_type=${mealType}`);
      setPlan(data);
    } catch { alert("替换失败"); }
  };

  const handleAdoptPlan = async () => {
    if (!plan) return;
    setAdopting(true);
    try {
      const { data } = await api.post(`/meals/${plan.id}/adopt`);
      alert(`已采纳 ${data.record_count} 餐到今日记录`);
    } catch {
      alert("采纳失败，请重试");
    } finally {
      setAdopting(false);
    }
  };

  useEffect(() => {
    fetchPlan();
  }, []);

  return (
    <div className="flex flex-col  ">
      <header className="flex items-center justify-between">
        
        <h1 className="text-lg font-bold text-gray-900">餐食计划</h1>
      </header>

      <main className="flex-1 px-4 py-4 space-y-4 pb-20">
        {!plan && !loading && (
          <div className="text-center py-16">
            <ChefHat className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">还没有今日餐食计划</p>
            <button
              onClick={generatePlan}
              disabled={generating}
              className="px-6 py-3 bg-green-500 text-white rounded-xl font-medium hover:bg-green-600 transition-colors disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4 inline mr-2" />
              {generating ? "生成中..." : "AI 生成今日三餐"}
            </button>
          </div>
        )}

        {plan && (
          <>
            {/* Summary */}
            <div className="bg-green-50 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <h2 className="font-semibold text-green-800">🎯 今日总热量</h2>
                <button onClick={generatePlan} disabled={generating} className="text-xs text-green-600 flex items-center gap-1">
                  <RefreshCw className={`w-3 h-3 ${generating ? "animate-spin" : ""}`} />
                  重新生成
                </button>
              </div>
              <p className="text-2xl font-bold text-green-700">{plan.total_calories} kcal</p>
              {plan.ai_note && <p className="text-xs text-green-600 mt-2">{plan.ai_note}</p>}
            </div>

            {/* Meals */}
            {(Object.keys(mealConfig) as Array<"breakfast" | "lunch" | "dinner">).map((type) => {
              const meal = plan[type];
              const config = mealConfig[type];
              const Icon = config.icon;
              return (
                <div key={type} className="border border-gray-100 rounded-xl overflow-hidden">
                  <div className={`${config.bg} px-4 py-3 flex items-center justify-between`}>
                    <div className="flex items-center gap-2">
                      <Icon className={`w-5 h-5 ${config.color}`} />
                      <span className="font-semibold text-gray-900">{config.label}</span>
                      {meal && <span className="text-xs text-gray-500">{meal.total_calories} kcal</span>}
                    </div>
                    <button onClick={() => replaceMeal(type)} className="text-xs text-gray-500 flex items-center gap-1 hover:text-green-600">
                      <RefreshCw className="w-3 h-3" /> 换一个
                    </button>
                  </div>
                  {meal && (
                    <div className="px-4 py-3 space-y-2">
                      <p className="text-sm font-medium text-gray-700 mb-2">{meal.name}</p>
                      {meal.foods.map((food, i) => (
                        <div key={i} className="flex items-center justify-between text-sm">
                          <span className="text-gray-700">· {food.name} <span className="text-gray-400">{food.amount}</span></span>
                          <span className="text-gray-400 text-xs">{food.calories} kcal</span>
                        </div>
                      ))}
                      <div className="flex gap-2 text-xs text-gray-400 pt-1 border-t border-gray-50">
                        <span>蛋白质 {meal.total_protein}g</span>
                        <span>脂肪 {meal.total_fat}g</span>
                        <span>碳水 {meal.total_carbs}g</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Adopt button */}
            <div className="flex gap-3 mt-4">
              <button
                onClick={handleAdoptPlan}
                disabled={adopting}
                className="flex-1 py-3 bg-green-500 text-white rounded-lg font-medium
                           hover:bg-green-600 disabled:opacity-50 transition-colors"
              >
                {adopting ? "采纳中..." : "采纳全部为今日记录"}
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
