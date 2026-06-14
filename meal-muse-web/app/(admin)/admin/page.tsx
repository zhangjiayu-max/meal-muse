"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import {
  Users,
  Utensils,
  MessageSquare,
  CalendarDays,
  TrendingUp,
  Activity,
} from "lucide-react";

interface SystemStats {
  users: {
    total: number;
    new_this_week: number;
    active_this_week: number;
  };
  diet_records: {
    total: number;
    today: number;
    this_week: number;
  };
  ai_chats: {
    total: number;
    today: number;
  };
  meal_plans: {
    total: number;
    today: number;
  };
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const { data } = await api.get("/admin/stats");
      setStats(data);
    } catch (err) {
      console.error("加载统计数据失败:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-10 text-gray-400">加载中...</div>;
  }

  if (!stats) {
    return <div className="text-center py-10 text-red-400">加载失败</div>;
  }

  const statCards = [
    {
      label: "总用户数",
      value: stats.users.total,
      sub: `本周新增 ${stats.users.new_this_week}`,
      icon: Users,
      color: "bg-blue-500",
    },
    {
      label: "活跃用户（7天）",
      value: stats.users.active_this_week,
      sub: "最近7天登录",
      icon: Activity,
      color: "bg-green-500",
    },
    {
      label: "饮食记录",
      value: stats.diet_records.total,
      sub: `今日 ${stats.diet_records.today} / 本周 ${stats.diet_records.this_week}`,
      icon: Utensils,
      color: "bg-orange-500",
    },
    {
      label: "AI 对话",
      value: stats.ai_chats.total,
      sub: `今日 ${stats.ai_chats.today} 条`,
      icon: MessageSquare,
      color: "bg-purple-500",
    },
    {
      label: "餐食计划",
      value: stats.meal_plans.total,
      sub: `今日 ${stats.meal_plans.today} 份`,
      icon: CalendarDays,
      color: "bg-pink-500",
    },
  ];

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-6">系统概览</h2>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.label}
              className="bg-white rounded-xl border border-gray-200 p-5"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-gray-500">{card.label}</span>
                <div className={`${card.color} p-2 rounded-lg`}>
                  <Icon className="w-4 h-4 text-white" />
                </div>
              </div>
              <p className="text-3xl font-bold text-gray-900">{card.value}</p>
              <p className="text-xs text-gray-400 mt-1">{card.sub}</p>
            </div>
          );
        })}
      </div>

      {/* 快捷操作 */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">快捷操作</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <a
            href="/admin/users"
            className="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors"
          >
            <Users className="w-6 h-6 text-blue-500" />
            <span className="text-sm text-gray-700">用户管理</span>
          </a>
          <a
            href="/admin/knowledge"
            className="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors"
          >
            <TrendingUp className="w-6 h-6 text-green-500" />
            <span className="text-sm text-gray-700">知识库</span>
          </a>
        </div>
      </div>
    </div>
  );
}
