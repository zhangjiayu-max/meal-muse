"use client";

import { useState, useEffect } from "react";
import { Star, History, Zap, Check, ChevronDown, ChevronUp } from "lucide-react";
import api from "@/lib/api";

interface FoodSuggestion {
  food: string;
  source: "favorite" | "history" | "default";
  count: number;
}

// 每个分类最多显示的数量
const MAX_ITEMS_PER_GROUP = 6;

export interface QuickFoodGridProps {
  /** 当前餐次，由外部传入 */
  mealType: string;
  /** 选中食物的回调，返回食物名称 */
  onSelect: (food: string) => void;
  /** 已选中的食物列表 */
  selectedFoods?: string[];
}

export function QuickFoodGrid({ mealType, onSelect, selectedFoods = [] }: QuickFoodGridProps) {
  const [suggestions, setSuggestions] = useState<FoodSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .get("/diet/smart-suggestions", { params: { meal_type: mealType, limit: 20 } })
      .then(({ data }) => {
        if (!cancelled && data.suggestions) {
          setSuggestions(data.suggestions);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [mealType]);

  // 按来源分组
  const groupedSuggestions = suggestions.reduce((acc, s) => {
    if (!acc[s.source]) acc[s.source] = [];
    acc[s.source].push(s);
    return acc;
  }, {} as Record<string, FoodSuggestion[]>);

  const toggleExpand = (source: string) => {
    setExpanded((prev) => ({ ...prev, [source]: !prev[source] }));
  };

  const renderFoodGroup = (
    source: string,
    label: string,
    icon: React.ReactNode,
    foods: FoodSuggestion[],
    bgColor: string,
    textColor: string,
    borderColor: string,
  ) => {
    const isExpanded = expanded[source];
    const displayFoods = isExpanded ? foods : foods.slice(0, MAX_ITEMS_PER_GROUP);
    const hasMore = foods.length > MAX_ITEMS_PER_GROUP;

    return (
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          {icon}
          <span className="text-xs font-medium text-gray-500">{label}</span>
          <span className="text-xs text-gray-400">({foods.length})</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {displayFoods.map((s) => {
            const isSelected = selectedFoods.includes(s.food);
            return (
              <button
                key={s.food}
                onClick={() => onSelect(s.food)}
                className={`px-2.5 py-1 rounded-full text-xs transition-all flex items-center gap-1 ${
                  isSelected
                    ? "bg-green-500 text-white border border-green-500"
                    : `${bgColor} ${textColor} ${borderColor} hover:opacity-80`
                }`}
              >
                {isSelected && <Check className="w-3 h-3" />}
                {s.food}
              </button>
            );
          })}
          {hasMore && (
            <button
              onClick={() => toggleExpand(source)}
              className="px-2.5 py-1 rounded-full text-xs text-gray-500 bg-gray-50 border border-gray-200 flex items-center gap-0.5 hover:bg-gray-100"
            >
              {isExpanded ? (
                <>
                  收起 <ChevronUp className="w-3 h-3" />
                </>
              ) : (
                <>
                  更多 <ChevronDown className="w-3 h-3" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return <div className="text-center py-3 text-sm text-gray-400">加载推荐中...</div>;
  }

  return (
    <div className="space-y-3">
      {/* 常用食物 - 最多显示 6 个 */}
      {groupedSuggestions["favorite"] &&
        renderFoodGroup(
          "favorite",
          "我的常用",
          <Star className="w-3.5 h-3.5 text-yellow-500" />,
          groupedSuggestions["favorite"],
          "bg-yellow-50",
          "text-yellow-700",
          "border border-yellow-200",
        )}

      {/* 最近吃过 - 最多显示 6 个 */}
      {groupedSuggestions["history"] &&
        renderFoodGroup(
          "history",
          "最近吃过",
          <History className="w-3.5 h-3.5 text-blue-500" />,
          groupedSuggestions["history"],
          "bg-blue-50",
          "text-blue-700",
          "border border-blue-200",
        )}

      {/* 推荐搭配 - 最多显示 8 个 */}
      {groupedSuggestions["default"] &&
        renderFoodGroup(
          "default",
          "推荐搭配",
          <Zap className="w-3.5 h-3.5 text-green-500" />,
          groupedSuggestions["default"],
          "bg-gray-50",
          "text-gray-700",
          "border border-gray-200",
        )}
    </div>
  );
}
