"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { toast } from "@/components/ui/toast";
import {
  User, Target, Scale, Heart, Users, Settings, LogOut, ChevronRight, Edit3, Check, Droplets, Utensils,
} from "lucide-react";

interface CycleInfo {
  current_phase: string;
  phase_diet_tip: { phase_name: string; diet_focus: string; recommended: string[] };
}

interface FamilyMember {
  name: string;
  relation: string;
  age_group: string;
  diet_note: string[];
}

interface ProfileData {
  diet_type: string;
  taste_preference: string;
  cuisine_preference: string[] | null;
  disliked_foods: string[] | null;
  cooking_method: string;
  meal_pattern: string;
  budget_level: string;
  // 新增字段
  constitution_types: string[] | null;
  health_sub_goals: string[] | null;
  preferred_ingredients: string[] | null;
  cooking_frequency: string | null;
  takeout_preference: string | null;
  family_cooking: boolean;
  family_members: FamilyMember[] | null;
  onboarding_version: number;
}

interface CompletenessData {
  score: number;
  missing: string[];
  hint: string;
}

const goalLabels: Record<string, string> = {
  weight_loss: "🎯 减脂减重",
  pregnancy: "🤰 备孕调理",
  health: "🧘 养生保健",
  muscle_gain: "💪 增肌塑形",
};

const dietTypeLabels: Record<string, string> = {
  normal: "普通饮食",
  vegetarian: "素食",
  vegan: "纯素",
  keto: "生酮饮食",
  lowcarb: "低碳水",
  mediterranean: "地中海饮食",
};

const constitutionLabels: Record<string, { label: string; emoji: string }> = {
  yang_deficiency: { label: "阳虚质", emoji: "☀️" },
  yin_deficiency: { label: "阴虚质", emoji: "🔥" },
  qi_deficiency: { label: "气虚质", emoji: "💨" },
  blood_stasis: { label: "血瘀质", emoji: "🩸" },
  phlegm_dampness: { label: "痰湿质", emoji: "🌊" },
  damp_heat: { label: "湿热质", emoji: "🌿" },
  qi_stagnation: { label: "气郁质", emoji: "😰" },
  special_diathesis: { label: "特禀质", emoji: "❄️" },
  neutral: { label: "平和质", emoji: "⚖️" },
};

const relationLabels: Record<string, string> = {
  self: "本人",
  spouse: "配偶",
  child: "子女",
  parent: "父母",
  grandparent: "祖辈",
  other: "其他",
};

const ageGroupLabels: Record<string, string> = {
  baby: "婴幼儿",
  toddler: "幼儿",
  child: "儿童",
  teen: "青少年",
  adult: "成人",
  senior: "老年",
};

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, logout, updateUser } = useAuthStore();
  const [cycle, setCycle] = useState<CycleInfo | null>(null);
  const [editingWeight, setEditingWeight] = useState(false);
  const [weightInput, setWeightInput] = useState("");
  const [familyInfo, setFamilyInfo] = useState<{ name: string; invite_code: string; member_count: number } | null>(null);
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [completeness, setCompleteness] = useState<CompletenessData | null>(null);
  const [editingNickname, setEditingNickname] = useState(false);
  const [nicknameInput, setNicknameInput] = useState("");

  useEffect(() => {
    if (isAuthenticated) {
      api.get("/family/my").then(({ data }) => setFamilyInfo(data)).catch(() => {});
      api.get("/menstrual/current").then(({ data }) => setCycle(data)).catch(() => {});
      api.get("/users/profile/full").then(({ data }) => {
        if (data.profile) {
          setProfileData(data.profile);
        }
      }).catch(() => {});
      api.get("/users/profile/completeness").then(({ data }) => setCompleteness(data)).catch(() => {});
    }
  }, [isAuthenticated]);

  const handleSaveWeight = async () => {
    const w = parseFloat(weightInput);
    if (isNaN(w) || w <= 0) return;
    try {
      await api.post("/body/metrics", { weight: w });
      const { data } = await api.put("/users/profile", { current_weight: w });
      updateUser(data);
      setEditingWeight(false);
    } catch { toast("error", "保存失败"); }
  };

  const handleSaveNickname = async () => {
    const trimmed = nicknameInput.trim();
    if (!trimmed) return;
    try {
      const { data } = await api.put("/users/profile", { nickname: trimmed });
      updateUser(data);
      setEditingNickname(false);
    } catch { toast("error", "昵称保存失败"); }
  };

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  const getCompletenessColor = (score: number) => {
    if (score < 60) return "var(--warning)";
    if (score <= 80) return "var(--success)";
    return "#15803d"; // 深绿色
  };

  const getCompletenessBg = (score: number) => {
    if (score < 60) return "rgba(234, 179, 8, 0.12)";
    if (score <= 80) return "rgba(34, 197, 94, 0.12)";
    return "rgba(21, 128, 61, 0.12)";
  };

  if (!user) return null;

  const phaseNames: Record<string, string> = {
    menstrual: "🔴 月经期", follicular: "🌱 卵泡期", ovulation: "🥚 排卵期", luteal: "😌 黄体期",
  };

  return (
    <div className="flex flex-col">
      <header className="flex items-center justify-between">
        <h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>个人中心</h1>
      </header>

      <main className="flex-1 px-4 py-4 space-y-4 pb-20">
        {/* User Info */}
        <div className="flex items-center gap-4 p-4 rounded-xl" style={{ background: "var(--bg-subtle)" }}>
          <div className="w-14 h-14 rounded-full flex items-center justify-center" style={{ background: "var(--primary-light)" }}>
            <User className="w-7 h-7" style={{ color: "var(--primary)" }} />
          </div>
          <div className="flex-1">
            {editingNickname ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={nicknameInput}
                  onChange={(e) => setNicknameInput(e.target.value)}
                  className="text-lg font-bold px-2 py-0.5 rounded flex-1"
                  style={{ color: "var(--text-primary)", border: "1px solid var(--border-default)", background: "var(--bg-card)" }}
                  maxLength={20}
                  autoFocus
                  onKeyDown={(e) => { if (e.key === "Enter") handleSaveNickname(); if (e.key === "Escape") setEditingNickname(false); }}
                />
                <button onClick={handleSaveNickname} style={{ color: "var(--primary)" }}><Check className="w-4 h-4" /></button>
              </div>
            ) : (
              <button
                onClick={() => { setNicknameInput(user.nickname || ""); setEditingNickname(true); }}
                className="flex items-center gap-1.5 group"
              >
                <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{user.nickname}</h2>
                <Edit3 className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: "var(--text-tertiary)" }} />
              </button>
            )}
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {user.phone?.replace(/(\d{3})\d{4}(\d{4})/, "$1****$2")}
            </p>
          </div>
        </div>

        {/* Completeness */}
        {completeness && (
          <button
            onClick={() => router.push("/onboarding")}
            className="w-full rounded-xl p-4 text-left transition-colors"
            style={{ background: getCompletenessBg(completeness.score), border: `1px solid ${getCompletenessColor(completeness.score)}33` }}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold" style={{ color: getCompletenessColor(completeness.score) }}>
                画像完整度
              </span>
              <span className="text-sm font-bold" style={{ color: getCompletenessColor(completeness.score) }}>
                {completeness.score}分
              </span>
            </div>
            <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: "var(--bg-subtle)" }}>
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${completeness.score}%`, background: getCompletenessColor(completeness.score) }}
              />
            </div>
            {completeness.hint && (
              <p className="text-xs mt-2" style={{ color: "var(--text-secondary)" }}>
                {completeness.hint} · 点击完善 →
              </p>
            )}
          </button>
        )}

        {/* Health Data */}
        <div className="space-y-1">
          <h3 className="text-sm font-semibold px-1" style={{ color: "var(--text-secondary)" }}>健康数据</h3>
          <div className="rounded-xl divide-y overflow-hidden" style={{ border: "1px solid var(--border-default)", borderColor: "var(--border-default)" }}>
            <div className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <Target className="w-4 h-4" style={{ color: "var(--primary)" }} />
                <span className="text-sm" style={{ color: "var(--text-primary)" }}>健康目标</span>
              </div>
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {goalLabels[user.preferences?.goal_type as string] || "未设置"}
              </span>
            </div>
            <div className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <Scale className="w-4 h-4" style={{ color: "var(--info)" }} />
                <span className="text-sm" style={{ color: "var(--text-primary)" }}>当前体重</span>
              </div>
              {editingWeight ? (
                <div className="flex items-center gap-2">
                  <input type="number" value={weightInput} onChange={(e) => setWeightInput(e.target.value)}
                    className="w-16 px-2 py-1 rounded text-sm text-right" style={{ border: "1px solid var(--border-default)" }} step="0.1" />
                  <button onClick={handleSaveWeight} style={{ color: "var(--primary)" }}><Check className="w-4 h-4" /></button>
                </div>
              ) : (
                <button onClick={() => { setWeightInput(String(user.current_weight || "")); setEditingWeight(true); }}
                  className="flex items-center gap-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                  {user.current_weight ? `${user.current_weight} kg` : "未填写"} <Edit3 className="w-3 h-3" />
                </button>
              )}
            </div>
            <div className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <Scale className="w-4 h-4" style={{ color: "var(--warning)" }} />
                <span className="text-sm" style={{ color: "var(--text-primary)" }}>目标体重</span>
              </div>
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {user.target_weight ? `${user.target_weight} kg` : "未设置"}
              </span>
            </div>
            <div className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <Droplets className="w-4 h-4" style={{ color: "var(--error)" }} />
                <span className="text-sm" style={{ color: "var(--text-primary)" }}>每日热量目标</span>
              </div>
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {user.daily_calorie_target ? `${user.daily_calorie_target} kcal` : "未设置"}
              </span>
            </div>
          </div>
        </div>

        {/* Diet Preferences Summary */}
        {profileData && (
          <div className="space-y-1">
            <div className="flex items-center justify-between px-1">
              <h3 className="text-sm font-semibold" style={{ color: "var(--text-secondary)" }}>饮食偏好</h3>
              <button
                onClick={() => router.push("/onboarding?step=3")}
                className="flex items-center gap-1 text-xs"
                style={{ color: "var(--primary)" }}
              >
                <Edit3 className="w-3 h-3" />
                修改偏好
              </button>
            </div>
            <div className="rounded-xl p-4 space-y-2" style={{ border: "1px solid var(--border-default)" }}>
              <div className="flex items-center justify-between">
                <span className="text-sm" style={{ color: "var(--text-secondary)" }}>饮食类型</span>
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                  {dietTypeLabels[profileData.diet_type] || profileData.diet_type}
                </span>
              </div>
              {profileData.cuisine_preference && profileData.cuisine_preference.length > 0 && (
                <div className="flex items-center justify-between">
                  <span className="text-sm" style={{ color: "var(--text-secondary)" }}>偏好菜系</span>
                  <div className="flex flex-wrap gap-1 justify-end">
                    {profileData.cuisine_preference.slice(0, 3).map((c) => (
                      <span key={c} className="text-xs px-2 py-0.5 rounded-full" style={{ background: "var(--primary-light)", color: "var(--primary)" }}>
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {profileData.disliked_foods && profileData.disliked_foods.length > 0 && (
                <div className="flex items-center justify-between">
                  <span className="text-sm" style={{ color: "var(--text-secondary)" }}>忌口食物</span>
                  <span className="text-sm" style={{ color: "var(--text-primary)" }}>
                    {profileData.disliked_foods.slice(0, 3).join("、")}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Constitution Types */}
        {profileData?.constitution_types && profileData.constitution_types.length > 0 && (
          <div className="space-y-1">
            <h3 className="text-sm font-semibold px-1" style={{ color: "var(--text-secondary)" }}>体质辨识</h3>
            <button
              onClick={() => router.push("/onboarding")}
              className="w-full rounded-xl p-4 text-left transition-colors"
              style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-default)" }}
            >
              <div className="flex flex-wrap gap-2 mb-2">
                {profileData.constitution_types.map((ct) => {
                  const info = constitutionLabels[ct];
                  return (
                    <span
                      key={ct}
                      className="text-xs px-2.5 py-1 rounded-full font-medium"
                      style={{ background: "var(--primary-light)", color: "var(--primary)" }}
                    >
                      {info ? `${info.emoji} ${info.label}` : ct}
                    </span>
                  );
                })}
              </div>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                点击重新测评 →
              </p>
            </button>
          </div>
        )}

        {/* Preferred Ingredients */}
        {profileData?.preferred_ingredients && profileData.preferred_ingredients.length > 0 && (
          <div className="space-y-1">
            <h3 className="text-sm font-semibold px-1" style={{ color: "var(--text-secondary)" }}>偏好食材</h3>
            <div className="rounded-xl p-4" style={{ border: "1px solid var(--border-default)" }}>
              <div className="flex flex-wrap gap-1.5">
                {profileData.preferred_ingredients.map((ing) => (
                  <span
                    key={ing}
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{ background: "var(--primary-light)", color: "var(--primary)" }}
                  >
                    {ing}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Family Members */}
        {profileData?.family_cooking && (
          <div className="space-y-1">
            <h3 className="text-sm font-semibold px-1" style={{ color: "var(--text-secondary)" }}>家庭成员</h3>
            <button
              onClick={() => router.push("/onboarding")}
              className="w-full rounded-xl p-4 text-left transition-colors"
              style={{ border: "1px solid var(--border-default)" }}
            >
              {profileData.family_members && profileData.family_members.length > 0 ? (
                <div className="space-y-2">
                  {profileData.family_members.map((member, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                        style={{ background: "var(--primary-light)" }}
                      >
                        <User className="w-4 h-4" style={{ color: "var(--primary)" }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                            {member.name}
                          </span>
                          <span className="text-xs px-1.5 py-0.5 rounded" style={{ background: "var(--bg-subtle)", color: "var(--text-secondary)" }}>
                            {relationLabels[member.relation] || member.relation}
                          </span>
                          {member.age_group && (
                            <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                              {ageGroupLabels[member.age_group] || member.age_group}
                            </span>
                          )}
                        </div>
                        {member.diet_note && member.diet_note.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {member.diet_note.map((note, ni) => (
                              <span
                                key={ni}
                                className="text-[10px] px-1.5 py-0.5 rounded-full"
                                style={{ background: "var(--bg-subtle)", color: "var(--text-secondary)" }}
                              >
                                {note}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  暂未添加家庭成员
                </p>
              )}
              <p className="text-xs mt-3" style={{ color: "var(--text-tertiary)" }}>
                点击管理家庭成员 →
              </p>
            </button>
          </div>
        )}

        {/* Menstrual Cycle */}
        {cycle && cycle.phase_diet_tip && (
          <div className="space-y-1">
            <h3 className="text-sm font-semibold px-1" style={{ color: "var(--text-secondary)" }}>生理周期</h3>
            <div className="rounded-xl p-4" style={{ background: "var(--primary-light)", border: "1px solid var(--primary)" }}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium" style={{ color: "var(--primary)" }}>
                  {phaseNames[cycle.current_phase] || cycle.current_phase}
                </span>
                <button onClick={() => router.push("/menstrual")} className="text-xs" style={{ color: "var(--primary)" }}>详情 →</button>
              </div>
              <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{cycle.phase_diet_tip.diet_focus}</p>
              <div className="flex flex-wrap gap-1 mt-2">
                {cycle.phase_diet_tip.recommended?.slice(0, 4).map((f) => (
                  <span key={f} className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: "var(--bg-card)", color: "var(--primary)" }}>
                    {f}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Family Sharing */}
        <div className="space-y-1">
          <h3 className="text-sm font-semibold px-1" style={{ color: "var(--text-secondary)" }}>家庭共享</h3>
          <button onClick={() => router.push("/family")}
            className="w-full flex items-center justify-between px-4 py-3 rounded-xl transition-colors"
            style={{ border: "1px solid var(--border-default)" }}>
            <div className="flex items-center gap-3">
              <Users className="w-4 h-4" style={{ color: "var(--primary)" }} />
              <span className="text-sm" style={{ color: "var(--text-primary)" }}>
                {familyInfo ? familyInfo.name : "创建/加入家庭"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {familyInfo && <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{familyInfo.member_count}人</span>}
              <ChevronRight className="w-4 h-4" style={{ color: "var(--text-tertiary)" }} />
            </div>
          </button>
        </div>

        {/* Quick Links */}
        <div className="space-y-1">
          <h3 className="text-sm font-semibold px-1" style={{ color: "var(--text-secondary)" }}>更多</h3>
          <div className="rounded-xl divide-y overflow-hidden" style={{ border: "1px solid var(--border-default)" }}>
            {[
              { icon: Heart, label: "健康报告", href: "/report", color: "var(--error)" },
              { icon: Scale, label: "身体数据", href: "/body", color: "var(--info)" },
              { icon: Droplets, label: "经期追踪", href: "/menstrual", color: "var(--primary)" },
              { icon: Settings, label: "偏好设置", href: "/settings", color: "var(--text-secondary)" },
            ].map((item) => (
              <button key={item.href} onClick={() => router.push(item.href)}
                className="w-full flex items-center justify-between px-4 py-3 transition-colors"
                style={{ borderColor: "var(--border-default)" }}>
                <div className="flex items-center gap-3">
                  <item.icon className="w-4 h-4" style={{ color: item.color }} />
                  <span className="text-sm" style={{ color: "var(--text-primary)" }}>{item.label}</span>
                </div>
                <ChevronRight className="w-4 h-4" style={{ color: "var(--text-tertiary)" }} />
              </button>
            ))}
          </div>
        </div>

        {/* Logout */}
        <button onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-xl transition-colors"
          style={{ color: "var(--error)", border: "1px solid var(--error)" }}>
          <LogOut className="w-4 h-4" />
          <span className="text-sm font-medium">退出登录</span>
        </button>
      </main>
    </div>
  );
}
