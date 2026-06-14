"use client";

import { usePathname, useRouter } from "next/navigation";
import {
  Leaf, Home, Plus, ChefHat, MessageCircle, BarChart3,
  Droplets, Users, Scale, LogOut, PanelLeftClose, PanelLeft,
  ChevronRight, Edit3,
} from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";
import api from "@/lib/api";

const navGroups = [
  {
    label: null,
    items: [
      { icon: Home, label: "首页", href: "/" },
      { icon: Plus, label: "饮食记录", href: "/record" },
      { icon: ChefHat, label: "餐食计划", href: "/plan" },
      { icon: MessageCircle, label: "AI 对话", href: "/chat" },
      { icon: BarChart3, label: "健康报告", href: "/report" },
    ],
  },
  {
    label: "健康管理",
    items: [
      { icon: Droplets, label: "经期追踪", href: "/menstrual" },
      { icon: Users, label: "家庭共享", href: "/family" },
      { icon: Scale, label: "身体数据", href: "/body" },
    ],
  },
];

/* ── helpers ── */

function maskPhone(phone: string | null): string {
  if (!phone) return "";
  const p = phone.replace(/\D/g, "");
  if (p.length >= 7) return p.slice(0, 3) + "****" + p.slice(-4);
  return phone;
}

/** health_goals + diet_type → display tags */
function collectTags(user: Record<string, unknown> | null): string[] {
  const tags: string[] = [];
  if (!user) return tags;

  // 健康目标
  const goals = user.health_goals;
  if (Array.isArray(goals)) {
    const emojiMap: Record<string, string> = {
      lose_weight: "🔥",
      gain_muscle: "💪",
      maintain: "⚖️",
      improve_health: "❤️",
    };
    goals.forEach((g: { goal_type?: string }) => {
      if (g?.goal_type) {
        const emoji = emojiMap[g.goal_type] || "🎯";
        const labelMap: Record<string, string> = {
          lose_weight: "减脂减重",
          gain_muscle: "增肌塑形",
          maintain: "维持体重",
          improve_health: "改善健康",
        };
        tags.push(`${emoji} ${labelMap[g.goal_type] || g.goal_type}`);
      }
    });
  }

  // 饮食类型
  const dietType = user.diet_type as string | undefined;
  if (dietType && dietType !== "normal") {
    const dietMap: Record<string, string> = {
      low_carb: "低碳水",
      keto: "生酮",
      vegetarian: "素食",
      vegan: "纯素",
      mediterranean: "地中海",
    };
    if (dietMap[dietType]) tags.push(dietMap[dietType]);
  }

  return tags;
}

/* ── UserInfoCard (inline sub-component) ── */

function UserInfoCard({
  nickname: initialNickname,
  phone,
  tags,
  onClose,
}: {
  nickname: string;
  phone: string | null;
  tags: string[];
  onClose: () => void;
}) {
  const router = useRouter();

  /* nickname inline-edit */
  const [editing, setEditing] = useState(false);
  const [nickname, setNickname] = useState(initialNickname);
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  /* completeness */
  const [completeness, setCompleteness] = useState<number | null>(null);

  useEffect(() => {
    api
      .get("/users/profile/completeness")
      .then((res: { data?: { score?: number; completeness?: number } }) => setCompleteness(res.data?.score ?? res.data?.completeness ?? 0))
      .catch(() => setCompleteness(null));
  }, []);

  useEffect(() => {
    if (editing && inputRef.current) inputRef.current.focus();
  }, [editing]);

  const saveNickname = useCallback(async () => {
    const trimmed = nickname.trim();
    if (!trimmed || trimmed === initialNickname) {
      setNickname(initialNickname);
      setEditing(false);
      return;
    }
    setSaving(true);
    try {
      await api.put("/users/profile", { nickname: trimmed });
      // update localStorage
      const userStr = localStorage.getItem("user");
      if (userStr) {
        const user = JSON.parse(userStr);
        user.nickname = trimmed;
        localStorage.setItem("user", JSON.stringify(user));
      }
      setEditing(false);
    } catch {
      setNickname(initialNickname);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }, [nickname, initialNickname]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  };

  /* progress bar color */
  let barColor = "#f97316"; // orange < 60
  if (completeness !== null) {
    if (completeness >= 80) barColor = "#15803d"; // dark green
    else if (completeness >= 60) barColor = "#22c55e"; // green
  }

  return (
    <div className="w-[280px] bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
      {/* header: avatar + nickname + phone */}
      <div className="px-4 pt-4 pb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center shrink-0">
            <span className="text-lg">👤</span>
          </div>
          <div className="flex-1 min-w-0">
            {editing ? (
              <input
                ref={inputRef}
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                onBlur={saveNickname}
                onKeyDown={(e) => {
                  if (e.key === "Enter") saveNickname();
                  if (e.key === "Escape") {
                    setNickname(initialNickname);
                    setEditing(false);
                  }
                }}
                disabled={saving}
                className="w-full text-sm font-semibold text-gray-900 border border-green-300 rounded px-2 py-0.5 outline-none focus:ring-1 focus:ring-green-400"
              />
            ) : (
              <button
                onClick={() => setEditing(true)}
                className="flex items-center gap-1 group"
              >
                <span className="text-sm font-semibold text-gray-900 truncate max-w-[160px]">
                  {nickname}
                </span>
                <Edit3 className="w-3 h-3 text-gray-300 group-hover:text-green-500 transition-colors" />
              </button>
            )}
            {phone && (
              <p className="text-xs text-gray-400 mt-0.5">📱 {maskPhone(phone)}</p>
            )}
          </div>
        </div>
      </div>

      {/* tags */}
      {tags.length > 0 && (
        <div className="px-4 pb-2 flex flex-wrap gap-1.5">
          {tags.map((t) => (
            <span
              key={t}
              className="text-[11px] px-2.5 py-0.5 rounded-full font-medium"
              style={{
                background: "var(--bg-subtle, #f0fdf4)",
                color: "var(--primary, #22c55e)",
                border: "1px solid var(--border-default, #e5e7eb)",
              }}
            >
              {t}
            </span>
          ))}
        </div>
      )}

      {/* completeness */}
      {completeness !== null && (
        <div className="px-4 pb-3">
          <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
            <span>画像完整度</span>
            <span className="font-medium" style={{ color: barColor }}>
              {completeness}%
            </span>
          </div>
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${completeness}%`, background: barColor }}
            />
          </div>
        </div>
      )}

      {/* CTA: onboarding */}
      {completeness !== null && completeness < 100 && (
        <button
          onClick={() => {
            onClose();
            router.push("/onboarding");
          }}
          className="w-full px-4 pb-3 text-left"
        >
          <span
            className="text-xs font-medium flex items-center gap-1"
            style={{ color: "var(--primary, #22c55e)" }}
          >
            完善画像，让 AI 更懂你
            <ChevronRight className="w-3 h-3" />
          </span>
        </button>
      )}

      {/* divider */}
      <div className="h-px bg-gray-100" />

      {/* actions */}
      <div className="p-2">
        <button
          onClick={() => {
            onClose();
            router.push("/profile");
          }}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors"
        >
          <Edit3 className="w-[16px] h-[16px] text-gray-400" />
          <span>编辑资料</span>
        </button>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-red-50 hover:text-red-600 transition-colors"
        >
          <LogOut className="w-[16px] h-[16px]" />
          <span>退出登录</span>
        </button>
      </div>
    </div>
  );
}

/* ── Main Sidebar ── */

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [showCard, setShowCard] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // read user info from localStorage
  const [userInfo, setUserInfo] = useState<{
    nickname: string;
    phone: string | null;
    tags: string[];
  }>({ nickname: "用户", phone: null, tags: [] });

  useEffect(() => {
    try {
      const userStr = localStorage.getItem("user");
      if (userStr) {
        const user = JSON.parse(userStr);
        setUserInfo({
          nickname: user.nickname || "用户",
          phone: user.phone || null,
          tags: collectTags(user),
        });
      }
    } catch {}
  }, []);

  // click outside to close popover
  useEffect(() => {
    if (!showCard) return;
    const handler = (e: MouseEvent) => {
      if (
        cardRef.current &&
        !cardRef.current.contains(e.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node)
      ) {
        setShowCard(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [showCard]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  };

  return (
    <aside
      className={`flex flex-col h-screen bg-[#fafafa] border-r border-gray-200 transition-all duration-200 shrink-0 ${
        collapsed ? "w-[68px]" : "w-[240px]"
      }`}
    >
      {/* Logo + Toggle */}
      <div className="flex items-center justify-between px-4 h-14 border-b border-gray-100 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center shrink-0">
            <Leaf className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <span className="text-base font-bold text-gray-900">MealMuse</span>
          )}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
        >
          {collapsed ? (
            <PanelLeft className="w-4 h-4" />
          ) : (
            <PanelLeftClose className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
        {navGroups.map((group, gi) => (
          <div key={gi}>
            {group.label && !collapsed && (
              <p className="text-[11px] font-medium text-gray-400 uppercase tracking-wider px-3 py-2">
                {group.label}
              </p>
            )}
            {group.items.map((item) => {
              const active = pathname === item.href;
              return (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    active
                      ? "bg-green-50 text-green-700 font-medium"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                  title={collapsed ? item.label : undefined}
                >
                  <item.icon
                    className={`w-[18px] h-[18px] shrink-0 ${
                      active ? "text-green-600" : "text-gray-400"
                    }`}
                  />
                  {!collapsed && <span>{item.label}</span>}
                </button>
              );
            })}
            {gi < navGroups.length - 1 && (
              <div className="h-px bg-gray-100 mx-3 my-2" />
            )}
          </div>
        ))}
      </nav>

      {/* User Section */}
      <div className="border-t border-gray-100 p-2 shrink-0 relative">
        {/* Popover */}
        {showCard && !collapsed && (
          <div
            ref={cardRef}
            className="absolute bottom-full left-0 mb-2 ml-0 z-50"
          >
            <UserInfoCard
              nickname={userInfo.nickname}
              phone={userInfo.phone}
              tags={userInfo.tags}
              onClose={() => setShowCard(false)}
            />
          </div>
        )}

        {/* User trigger button */}
        <button
          ref={triggerRef}
          onClick={() => {
            if (collapsed) {
              router.push("/profile");
            } else {
              setShowCard((v) => !v);
            }
          }}
          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
            showCard
              ? "bg-green-50 text-green-700"
              : "text-gray-600 hover:bg-gray-100"
          }`}
        >
          <div className="w-7 h-7 bg-green-100 rounded-full flex items-center justify-center shrink-0">
            <span className="text-xs">👤</span>
          </div>
          {!collapsed && (
            <span className="truncate">{userInfo.nickname}</span>
          )}
        </button>

        {/* Collapsed mode: show logout separately */}
        {collapsed && (
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-red-50 hover:text-red-600 transition-colors mt-1"
            title="退出登录"
          >
            <LogOut className="w-[18px] h-[18px] shrink-0" />
          </button>
        )}
      </div>
    </aside>
  );
}
