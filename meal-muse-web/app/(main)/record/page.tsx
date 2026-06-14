"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useDietStore } from "@/stores/diet";
import { QuickFoodGrid } from "@/components/ui/quick-food-grid";
import {
  Trash2,
  Pencil,
  X,
  Check,
  Coffee,
  Sun,
  Moon,
  Cookie,
  Send,
  Plus,
  Lightbulb,
  UtensilsCrossed,
} from "lucide-react";
import { toast } from "@/components/ui/toast";
import { confirm } from "@/components/ui/confirm";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/error-message";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const mealTabs = [
  { key: "breakfast", label: "早餐", icon: Coffee, emoji: "🌅" },
  { key: "lunch", label: "午餐", icon: Sun, emoji: "☀️" },
  { key: "dinner", label: "晚餐", icon: Moon, emoji: "🌙" },
  { key: "snack", label: "加餐", icon: Cookie, emoji: "🍪" },
];

export default function RecordPage() {
  const { todaySummary, fetchToday, updateRecord, deleteRecord } = useDietStore();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("lunch");
  const [foodText, setFoodText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [mealTime, setMealTime] = useState(
    () => new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", hour12: false })
  );

  // 编辑状态
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editFoodText, setEditFoodText] = useState("");
  const [editMealType, setEditMealType] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchToday();
  }, [fetchToday]);

  // 点击快捷食物标签，选中/取消切换
  const handleFoodSelect = (food: string) => {
    setFoodText((prev) => {
      const foods = prev.split(/[+＋、，,]/).map((f) => f.trim()).filter(Boolean);
      if (foods.includes(food)) {
        return foods.filter((f) => f !== food).join(" + ");
      }
      return prev ? prev + " + " + food : food;
    });
  };

  // 提交记录
  const handleSubmit = async () => {
    if (!foodText.trim()) return;
    setSubmitting(true);

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const res = await fetch(`${API_BASE}/diet/records`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          meal_type: activeTab,
          food_text: foodText.trim(),
          recorded_at: new Date(
            `${new Date().toISOString().slice(0, 10)}T${mealTime}:00+08:00`
          ).toISOString(),
        }),
      });

      if (res.ok) {
        // 记录成功后，添加到常用列表
        const foods = foodText
          .split(/[+＋、，,]/)
          .map((f) => f.trim())
          .filter(Boolean);
        for (const food of foods) {
          await fetch(`${API_BASE}/diet/favorites`, {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              food_name: food,
              meal_type: activeTab,
            }),
          }).catch(() => {});
        }

        setFoodText("");
        await fetchToday();
        toast("success", "记录成功 🎉");
      } else {
        const err = await res.json().catch(() => ({}));
        toast("error", err.error || "记录失败，请重试");
      }
    } catch {
      toast("error", "网络异常，请检查连接后重试");
    } finally {
      setSubmitting(false);
    }
  };

  // 删除记录
  const handleDelete = async (id: string) => {
    const ok = await confirm({
      title: "确定删除？",
      message: "删除后不可恢复",
      type: "danger",
    });
    if (!ok) return;
    try {
      await deleteRecord(id);
      await fetchToday();
      toast("success", "已删除");
    } catch {
      toast("error", "删除失败，请重试");
    }
  };

  // 开始编辑
  const handleStartEdit = (record: {
    id: string;
    food_text: string;
    meal_type: string;
  }) => {
    setEditingId(record.id);
    setEditFoodText(record.food_text);
    setEditMealType(record.meal_type);
  };

  // 取消编辑
  const handleCancelEdit = () => {
    setEditingId(null);
    setEditFoodText("");
    setEditMealType("");
  };

  // 保存编辑
  const handleSaveEdit = async (id: string) => {
    if (!editFoodText.trim()) return;
    setSaving(true);
    try {
      await updateRecord(id, {
        food_text: editFoodText.trim(),
        meal_type: editMealType,
      });
      setEditingId(null);
      await fetchToday();
      toast("success", "已更新");
    } catch {
      toast("error", "保存失败，请重试");
    } finally {
      setSaving(false);
    }
  };

  const records = todaySummary?.records || [];
  const todayStr = new Date().toLocaleDateString("zh-CN", {
    month: "long",
    day: "numeric",
    weekday: "long",
  });

  // 按餐次分组
  const recordsByMeal = mealTabs.reduce(
    (acc, tab) => {
      acc[tab.key] = records.filter((r) => r.meal_type === tab.key);
      return acc;
    },
    {} as Record<string, typeof records>,
  );

  // 计算当前餐次的营养小计
  const activeRecords = recordsByMeal[activeTab] || [];
  const activeNutrition = activeRecords.reduce(
    (sum, r) => ({
      cal: sum.cal + r.total_calories,
      protein: sum.protein + (r.total_protein || 0),
      carbs: sum.carbs + (r.total_carbs || 0),
      fat: sum.fat + (r.total_fat || 0),
    }),
    { cal: 0, protein: 0, carbs: 0, fat: 0 },
  );

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">📝 记录饮食</h1>
        <p className="text-sm text-gray-500 mt-0.5">{todayStr}</p>
      </div>

      {/* 餐次选择 */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {mealTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all whitespace-nowrap ${
              activeTab === tab.key
                ? "bg-green-500 text-white shadow-sm shadow-green-200"
                : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 hover:border-gray-300"
            }`}
          >
            <span>{tab.emoji}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* 吃饭时间选择 */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <span>⏰ 吃饭时间</span>
        <input
          type="time"
          value={mealTime}
          onChange={(e) => setMealTime(e.target.value)}
          className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
        />
      </div>

      {/* 输入区域 */}
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
        {/* 输入框 */}
        <div className="p-4">
          <textarea
            value={foodText}
            onChange={(e) => setFoodText(e.target.value)}
            placeholder={`记录${mealTabs.find((t) => t.key === activeTab)?.label}吃了什么...\n例如：米饭 + 红烧肉 + 青菜汤`}
            rows={3}
            className="w-full text-sm text-gray-800 placeholder-gray-400 resize-none focus:outline-none"
          />
        </div>

        {/* 快捷食物标签 */}
        <div className="border-t border-gray-100 px-4 py-3">
          <div className="flex items-center gap-1.5 mb-2">
            <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-xs font-medium text-gray-500">快捷添加</span>
          </div>
          <QuickFoodGrid
            mealType={activeTab}
            onSelect={handleFoodSelect}
            selectedFoods={foodText
              .split(/[+＋、，,]/)
              .map((f) => f.trim())
              .filter(Boolean)}
          />
        </div>

        {/* 提交按钮 */}
        <div className="border-t border-gray-100 px-4 py-3 flex items-center justify-between bg-gray-50/50">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <UtensilsCrossed className="w-3.5 h-3.5" />
            <span>
              {foodText.trim()
                ? `将记录：${foodText.slice(0, 30)}${foodText.length > 30 ? "..." : ""}`
                : "输入食物后点击记录"}
            </span>
          </div>
          <Button
            onClick={handleSubmit}
            loading={submitting}
            disabled={!foodText.trim()}
            size="md"
            icon={<Send className="w-4 h-4" />}
          >
            {submitting ? "AI 分析中..." : "记录"}
          </Button>
        </div>
      </div>

      {/* 当前餐次营养小计 */}
      {activeRecords.length > 0 && (
        <div className="flex gap-3 text-xs text-gray-500 bg-green-50/50 rounded-xl px-4 py-2.5 border border-green-100">
          <span className="font-medium text-gray-700">{mealTabs.find(t => t.key === activeTab)?.label}小计：</span>
          <span>🔥 {Math.round(activeNutrition.cal)} kcal</span>
          <span>💪 蛋白质 {Math.round(activeNutrition.protein)}g</span>
          <span>🌾 碳水 {Math.round(activeNutrition.carbs)}g</span>
          <span>🧈 脂肪 {Math.round(activeNutrition.fat)}g</span>
        </div>
      )}

      {/* 今日记录 */}
      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <span>📋 今日记录</span>
          <span className="text-xs font-normal text-gray-400">
            · {records.length} 条
          </span>
        </h2>

        {records.length === 0 ? (
          <EmptyState
            icon="🍽️"
            title="还没有记录"
            description="在上方输入你吃了什么，AI 会自动分析营养"
          />
        ) : (
          <div className="space-y-3">
            {mealTabs.map((tab) => {
              const mealRecords = recordsByMeal[tab.key];
              if (mealRecords.length === 0) return null;

              return (
                <div
                  key={tab.key}
                  className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm"
                >
                  {/* 餐次标题 */}
                  <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-50 border-b border-gray-100">
                    <span>{tab.emoji}</span>
                    <span className="text-sm font-medium text-gray-700">
                      {tab.label}
                    </span>
                    <span className="text-xs text-gray-400 ml-auto">
                      {mealRecords.reduce(
                        (sum, r) => sum + r.total_calories,
                        0,
                      )}{" "}
                      kcal
                    </span>
                  </div>

                  {/* 记录列表 */}
                  <div className="divide-y divide-gray-50">
                    {mealRecords.map((record) => {
                      const isEditing = editingId === record.id;

                      return (
                        <div key={record.id} className="px-4 py-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              {isEditing ? (
                                <div className="space-y-2">
                                  <textarea
                                    value={editFoodText}
                                    onChange={(e) =>
                                      setEditFoodText(e.target.value)
                                    }
                                    rows={2}
                                    className="w-full text-sm text-gray-800 border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-400 resize-none"
                                  />
                                  <select
                                    value={editMealType}
                                    onChange={(e) =>
                                      setEditMealType(e.target.value)
                                    }
                                    className="text-sm border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:border-green-400"
                                  >
                                    {mealTabs.map((t) => (
                                      <option key={t.key} value={t.key}>
                                        {t.label}
                                      </option>
                                    ))}
                                  </select>
                                </div>
                              ) : (
                                <>
                                  <p className="text-sm text-gray-800">
                                    {record.food_text}
                                  </p>
                                  <div className="flex gap-3 text-xs text-gray-400 mt-1">
                                    <span>
                                      🕐 {new Date(record.recorded_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", hour12: false })}
                                    </span>
                                    <span>
                                      🔥 {record.total_calories} kcal
                                    </span>
                                    <span>
                                      蛋白质{" "}
                                      {Math.round(record.total_protein)}g
                                    </span>
                                    <span>
                                      碳水 {Math.round(record.total_carbs)}g
                                    </span>
                                    <span>
                                      脂肪 {Math.round(record.total_fat)}g
                                    </span>
                                  </div>
                                </>
                              )}
                            </div>

                            {/* 操作按钮 */}
                            <div className="flex items-center gap-1 ml-2">
                              {isEditing ? (
                                <>
                                  <button
                                    onClick={() => handleSaveEdit(record.id)}
                                    disabled={saving}
                                    className="p-1.5 text-green-500 hover:bg-green-50 rounded-lg transition-colors"
                                  >
                                    <Check className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={handleCancelEdit}
                                    className="p-1.5 text-gray-400 hover:bg-gray-50 rounded-lg transition-colors"
                                  >
                                    <X className="w-4 h-4" />
                                  </button>
                                </>
                              ) : (
                                <>
                                  <button
                                    onClick={() => handleStartEdit(record)}
                                    className="p-1.5 text-gray-300 hover:text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"
                                  >
                                    <Pencil className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={() => handleDelete(record.id)}
                                    className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
