"use client";

import { useState, useEffect, KeyboardEvent } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { toast } from "@/components/ui/toast";
import {
  ArrowLeft, User, Target, Utensils, ChefHat, Heart, Moon, Save, Loader2,
  Users, Plus, X,
} from "lucide-react";

interface ProfileOptions {
  diet_types: { key: string; label: string }[];
  taste_preferences: { key: string; label: string }[];
  cuisine_options: string[];
  allergy_options: { key: string; label: string }[];
  health_goal_types: { key: string; label: string; emoji: string }[];
  health_condition_types: { key: string; label: string }[];
  cooking_methods: { key: string; label: string }[];
  cooking_facilities: { key: string; label: string }[];
  meal_prep_times: { key: string; label: string }[];
  meal_patterns: { key: string; label: string }[];
  sleep_patterns: { key: string; label: string }[];
  budget_levels: { key: string; label: string }[];
  activity_levels: { key: string; label: string }[];
}

interface FullProfile {
  user: {
    nickname: string;
    gender: string | null;
    age: number | null;
    height_cm: number | null;
    current_weight: number | null;
    target_weight: number | null;
    activity_level: string;
  };
  profile: {
    taste_preference: string;
    diet_type: string;
    cuisine_preference: string[] | null;
    disliked_foods: string[] | null;
    cooking_method: string;
    cooking_facility: string;
    meal_pattern: string;
    sleep_pattern: string;
    care_targets: string[] | null;
    budget_level: string;
    meal_prep_time: string;
    water_intake_goal: number | null;
    constitution_types?: string[];
    health_sub_goals?: string[];
    preferred_ingredients?: string[];
    cooking_frequency?: string;
    takeout_preference?: string;
    family_cooking?: boolean;
    family_members?: FamilyMember[];
  } | null;
  health_goals: {
    id: string;
    goal_type: string;
    target_weight: number | null;
    daily_calorie_target: number | null;
  }[];
  allergies: {
    id: string;
    allergen: string;
    custom_name: string | null;
  }[];
  health_conditions: {
    id: string;
    condition_type: string;
    severity: string;
  }[];
}

interface FamilyMember {
  name: string;
  relation: string;
  age_group: string;
  diet_note: string;
}

// Constitution type mapping
const CONSTITUTION_OPTIONS = [
  { key: "yang_deficiency", label: "☀️ 阳虚质(怕冷/手脚凉)" },
  { key: "yin_deficiency", label: "🔥 阴虚质(口干/易上火)" },
  { key: "qi_deficiency", label: "💨 气虚质(乏力/气短)" },
  { key: "blood_stasis", label: "🩸 血瘀质(皮肤暗沉/易瘀青)" },
  { key: "phlegm_dampness", label: "🌊 痰湿质(体胖/痰多)" },
  { key: "damp_heat", label: "🌿 湿热质(面垢油光/口苦)" },
  { key: "qi_stagnation", label: "😰 气郁质(情绪低落/胸闷)" },
  { key: "special_diathesis", label: "❄️ 特禀质(过敏体质)" },
  { key: "neutral", label: "⚖️ 平和质(正常)" },
];

// Health sub-goal mapping
const HEALTH_SUB_GOALS: Record<string, { key: string; label: string }[]> = {
  weight_loss: [
    { key: "rapid_loss", label: "速减" },
    { key: "slow_loss", label: "慢减" },
    { key: "body_shape", label: "塑形" },
  ],
  pregnancy: [
    { key: "pregnancy_preparing", label: "备孕中" },
    { key: "early_pregnancy", label: "孕早期" },
    { key: "mid_pregnancy", label: "孕中期" },
    { key: "late_pregnancy", label: "孕晚期" },
    { key: "breastfeeding", label: "哺乳期" },
  ],
  health: [
    { key: "qi_blood", label: "气血不足" },
    { key: "spleen_stomach", label: "脾胃调理" },
    { key: "kidney", label: "补肾" },
    { key: "liver", label: "护肝" },
    { key: "sleep", label: "安神助眠" },
  ],
  muscle_gain: [
    { key: "muscle_gain", label: "增肌" },
    { key: "body_recomp", label: "减脂塑形" },
    { key: "recovery", label: "运动恢复" },
  ],
};

// Cooking frequency options
const COOKING_FREQUENCY_OPTIONS = [
  { key: "often", label: "天天做" },
  { key: "sometimes", label: "3-5次/周" },
  { key: "rarely", label: "偶尔" },
  { key: "never", label: "从不" },
];

// Takeout preference options
const TAKEOUT_PREFERENCE_OPTIONS = [
  { key: "healthy_light", label: "营养轻食" },
  { key: "home_style", label: "家常菜" },
  { key: "fast_food", label: "快餐" },
  { key: "any", label: "都行" },
];

// Family member relation options
const RELATION_OPTIONS = [
  { key: "child", label: "孩子" },
  { key: "parent", label: "父母" },
  { key: "spouse", label: "伴侣" },
  { key: "other", label: "其他" },
];

// Family member age group options
const AGE_GROUP_OPTIONS = [
  { key: "0-3", label: "0-3岁" },
  { key: "3-6", label: "3-6岁" },
  { key: "6-12", label: "6-12岁" },
  { key: "12+", label: "12岁以上" },
  { key: "adult", label: "成人" },
  { key: "elderly", label: "老人" },
];

export default function SettingsPage() {
  const router = useRouter();
  const { updateUser } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [options, setOptions] = useState<ProfileOptions | null>(null);
  const [profile, setProfile] = useState<FullProfile | null>(null);

  // Editable state - basic
  const [nickname, setNickname] = useState("");
  const [gender, setGender] = useState("");
  const [age, setAge] = useState("");
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [targetWeight, setTargetWeight] = useState("");
  const [activityLevel, setActivityLevel] = useState("moderate");

  // Diet preferences
  const [dietType, setDietType] = useState("normal");
  const [tastePref, setTastePref] = useState<string[]>([]);
  const [cuisinePref, setCuisinePref] = useState<string[]>([]);
  const [dislikedFoods, setDislikedFoods] = useState("");
  const [allergies, setAllergies] = useState<string[]>([]);
  const [healthGoals, setHealthGoals] = useState<string[]>([]);
  const [healthConditions, setHealthConditions] = useState<string[]>([]);

  // Cooking conditions
  const [cookingMethod, setCookingMethod] = useState("simple");
  const [cookingFacility, setCookingFacility] = useState("full_kitchen");
  const [mealPrepTime, setMealPrepTime] = useState("30min");
  const [mealPattern, setMealPattern] = useState("3_meals");

  // Lifestyle
  const [sleepPattern, setSleepPattern] = useState("early_bird");
  const [budgetLevel, setBudgetLevel] = useState("medium");
  const [waterIntakeGoal, setWaterIntakeGoal] = useState("");

  // New fields - constitution
  const [constitutionTypes, setConstitutionTypes] = useState<string[]>([]);
  // New fields - health sub goals
  const [healthSubGoals, setHealthSubGoals] = useState<string[]>([]);
  // New fields - preferred ingredients
  const [preferredIngredients, setPreferredIngredients] = useState<string[]>([]);
  const [ingredientInput, setIngredientInput] = useState("");
  // New fields - cooking frequency
  const [cookingFrequency, setCookingFrequency] = useState("often");
  // New fields - takeout preference
  const [takeoutPreference, setTakeoutPreference] = useState("any");
  // New fields - family cooking
  const [familyCooking, setFamilyCooking] = useState(false);
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [optionsRes, profileRes] = await Promise.all([
        api.get("/users/profile/options"),
        api.get("/users/profile/full"),
      ]);
      setOptions(optionsRes.data);
      setProfile(profileRes.data);

      // Populate editable state
      const p = profileRes.data;
      setNickname(p.user.nickname || "");
      setGender(p.user.gender || "");
      setAge(p.user.age ? String(p.user.age) : "");
      setHeight(p.user.height_cm ? String(p.user.height_cm) : "");
      setWeight(p.user.current_weight ? String(p.user.current_weight) : "");
      setTargetWeight(p.user.target_weight ? String(p.user.target_weight) : "");
      setActivityLevel(p.user.activity_level || "moderate");

      if (p.profile) {
        setDietType(p.profile.diet_type || "normal");
        setTastePref(p.profile.taste_preference ? p.profile.taste_preference.split(",") : []);
        setCuisinePref(p.profile.cuisine_preference || []);
        setDislikedFoods(p.profile.disliked_foods?.join("，") || "");
        setCookingMethod(p.profile.cooking_method || "simple");
        setCookingFacility(p.profile.cooking_facility || "full_kitchen");
        setMealPrepTime(p.profile.meal_prep_time || "30min");
        setMealPattern(p.profile.meal_pattern || "3_meals");
        setSleepPattern(p.profile.sleep_pattern || "early_bird");
        setBudgetLevel(p.profile.budget_level || "medium");
        setWaterIntakeGoal(p.profile.water_intake_goal ? String(p.profile.water_intake_goal) : "");

        // New fields
        setConstitutionTypes(p.profile.constitution_types || []);
        setHealthSubGoals(p.profile.health_sub_goals || []);
        setPreferredIngredients(p.profile.preferred_ingredients || []);
        setCookingFrequency(p.profile.cooking_frequency || "often");
        setTakeoutPreference(p.profile.takeout_preference || "any");
        setFamilyCooking(p.profile.family_cooking || false);
        setFamilyMembers(p.profile.family_members || []);
      }

      setAllergies(p.allergies.map((a: { allergen: string }) => a.allergen));
      setHealthGoals(p.health_goals.map((g: { goal_type: string }) => g.goal_type));
      setHealthConditions(p.health_conditions.map((c: { condition_type: string }) => c.condition_type));
    } catch {
      toast("error", "加载失败");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put("/users/profile/full", {
        user: {
          nickname,
          gender: gender || undefined,
          age: age ? Number(age) : undefined,
          height_cm: height ? Number(height) : undefined,
          current_weight: weight ? Number(weight) : undefined,
          target_weight: targetWeight ? Number(targetWeight) : undefined,
          activity_level: activityLevel,
        },
        profile: {
          diet_type: dietType,
          taste_preference: tastePref.join(","),
          cuisine_preference: cuisinePref.length > 0 ? cuisinePref : null,
          disliked_foods: dislikedFoods ? dislikedFoods.split(/[,，、]+/).filter(Boolean) : null,
          cooking_method: cookingMethod,
          cooking_facility: cookingFacility,
          meal_prep_time: mealPrepTime,
          meal_pattern: mealPattern,
          sleep_pattern: sleepPattern,
          budget_level: budgetLevel,
          water_intake_goal: waterIntakeGoal ? Number(waterIntakeGoal) : null,
          // New fields
          constitution_types: constitutionTypes,
          health_sub_goals: healthSubGoals,
          preferred_ingredients: preferredIngredients.length > 0 ? preferredIngredients : null,
          cooking_frequency: cookingFrequency,
          takeout_preference: takeoutPreference,
          family_cooking: familyCooking,
          family_members: familyMembers.length > 0 ? familyMembers : null,
        },
        health_goals: healthGoals.map((g) => ({ goal_type: g })),
        allergies: allergies.map((a) => ({ allergen: a })),
        health_conditions: healthConditions.map((c) => ({ condition_type: c, severity: "mild" })),
      });

      // Refresh user in auth store
      const { data } = await api.get("/users/profile");
      updateUser(data);

      toast("success", "保存成功");
    } catch {
      toast("error", "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const toggleItem = (list: string[], item: string): string[] => {
    return list.includes(item) ? list.filter((i) => i !== item) : [...list, item];
  };

  // Add preferred ingredient on Enter
  const handleIngredientKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const val = ingredientInput.trim();
      if (val && !preferredIngredients.includes(val)) {
        setPreferredIngredients([...preferredIngredients, val]);
      }
      setIngredientInput("");
    }
  };

  // Remove preferred ingredient
  const removeIngredient = (item: string) => {
    setPreferredIngredients(preferredIngredients.filter((i) => i !== item));
  };

  // Add family member
  const addFamilyMember = () => {
    setFamilyMembers([...familyMembers, { name: "", relation: "other", age_group: "adult", diet_note: "" }]);
  };

  // Update family member
  const updateFamilyMember = (index: number, field: keyof FamilyMember, value: string) => {
    const updated = [...familyMembers];
    updated[index] = { ...updated[index], [field]: value };
    setFamilyMembers(updated);
  };

  // Remove family member
  const removeFamilyMember = (index: number) => {
    setFamilyMembers(familyMembers.filter((_, i) => i !== index));
  };

  // Compute available sub-goals based on selected health goals
  const availableSubGoals = healthGoals
    .flatMap((goal) => HEALTH_SUB_GOALS[goal] || [])
    .filter(
      (sg, idx, arr) => arr.findIndex((x) => x.key === sg.key) === idx
    );

  if (loading || !options || !profile) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin" style={{ color: "var(--primary)" }} />
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <header className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} className="p-1">
            <ArrowLeft className="w-5 h-5" style={{ color: "var(--text-primary)" }} />
          </button>
          <h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>偏好设置</h1>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium text-white disabled:opacity-50"
          style={{ background: "var(--primary)" }}
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          保存
        </button>
      </header>

      <main className="flex-1 px-4 py-4 space-y-4 pb-20">
        {/* Basic Info */}
        <Section title="基础信息" icon={User}>
          <div className="space-y-3">
            <InputField label="昵称" value={nickname} onChange={setNickname} />
            <div className="grid grid-cols-2 gap-3">
              <InputField label="年龄" value={age} onChange={setAge} type="number" placeholder="28" />
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>性别</label>
                <div className="flex gap-2">
                  {[{ k: "female", l: "女" }, { k: "male", l: "男" }].map((g) => (
                    <button
                      key={g.k}
                      onClick={() => setGender(g.k)}
                      className="flex-1 py-2 rounded-lg text-sm transition-colors"
                      style={{
                        background: gender === g.k ? "var(--primary)" : "var(--bg-subtle)",
                        color: gender === g.k ? "#fff" : "var(--text-secondary)",
                        border: `1px solid ${gender === g.k ? "var(--primary)" : "var(--border-default)"}`,
                      }}
                    >
                      {g.l}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <InputField label="身高 (cm)" value={height} onChange={setHeight} type="number" placeholder="165" />
              <InputField label="当前体重 (kg)" value={weight} onChange={setWeight} type="number" placeholder="55" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <InputField label="目标体重 (kg)" value={targetWeight} onChange={setTargetWeight} type="number" placeholder="50" />
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>活动量</label>
                <select
                  value={activityLevel}
                  onChange={(e) => setActivityLevel(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm outline-none"
                  style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }}
                >
                  {options.activity_levels.map((a) => (
                    <option key={a.key} value={a.key}>{a.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </Section>

        {/* Health Goals */}
        <Section title="健康目标" icon={Target}>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>选择目标（可多选）</label>
              <div className="flex flex-wrap gap-2">
                {options.health_goal_types.map((g) => {
                  const selected = healthGoals.includes(g.key);
                  return (
                    <button
                      key={g.key}
                      onClick={() => setHealthGoals(toggleItem(healthGoals, g.key))}
                      className="px-3 py-2 rounded-xl text-sm transition-colors"
                      style={{
                        background: selected ? "var(--primary)" : "var(--bg-subtle)",
                        color: selected ? "#fff" : "var(--text-secondary)",
                        border: `1px solid ${selected ? "var(--primary)" : "var(--border-default)"}`,
                      }}
                    >
                      {g.emoji} {g.label}
                    </button>
                  );
                })}
              </div>
            </div>
            {/* Health Sub Goals */}
            {availableSubGoals.length > 0 && (
              <div>
                <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>子目标（可多选）</label>
                <div className="flex flex-wrap gap-2">
                  {availableSubGoals.map((sg) => {
                    const selected = healthSubGoals.includes(sg.key);
                    return (
                      <button
                        key={sg.key}
                        onClick={() => setHealthSubGoals(toggleItem(healthSubGoals, sg.key))}
                        className="px-3 py-1.5 rounded-full text-sm transition-colors"
                        style={{
                          background: selected ? "var(--primary)" : "var(--bg-subtle)",
                          color: selected ? "#fff" : "var(--text-secondary)",
                          border: `1px solid ${selected ? "var(--primary)" : "var(--border-default)"}`,
                        }}
                      >
                        {sg.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </Section>

        {/* Diet Preferences */}
        <Section title="饮食偏好" icon={Utensils}>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>饮食类型</label>
              <div className="flex flex-wrap gap-2">
                {options.diet_types.map((d) => (
                  <button
                    key={d.key}
                    onClick={() => setDietType(d.key)}
                    className="px-3 py-1.5 rounded-full text-sm transition-colors"
                    style={{
                      background: dietType === d.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: dietType === d.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${dietType === d.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>口味偏好</label>
              <div className="flex flex-wrap gap-2">
                {options.taste_preferences.map((t) => {
                  const selected = tastePref.includes(t.key);
                  return (
                    <button
                      key={t.key}
                      onClick={() => setTastePref(toggleItem(tastePref, t.key))}
                      className="px-3 py-1.5 rounded-full text-sm transition-colors"
                      style={{
                        background: selected ? "var(--primary)" : "var(--bg-subtle)",
                        color: selected ? "#fff" : "var(--text-secondary)",
                        border: `1px solid ${selected ? "var(--primary)" : "var(--border-default)"}`,
                      }}
                    >
                      {t.label}
                    </button>
                  );
                })}
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>偏好菜系</label>
              <div className="flex flex-wrap gap-2">
                {options.cuisine_options.map((c) => {
                  const selected = cuisinePref.includes(c);
                  return (
                    <button
                      key={c}
                      onClick={() => setCuisinePref(toggleItem(cuisinePref, c))}
                      className="px-3 py-1.5 rounded-full text-sm transition-colors"
                      style={{
                        background: selected ? "var(--primary)" : "var(--bg-subtle)",
                        color: selected ? "#fff" : "var(--text-secondary)",
                        border: `1px solid ${selected ? "var(--primary)" : "var(--border-default)"}`,
                      }}
                    >
                      {c}
                    </button>
                  );
                })}
              </div>
            </div>
            <InputField
              label="忌口食物（逗号分隔）"
              value={dislikedFoods}
              onChange={setDislikedFoods}
              placeholder="香菜，芹菜"
            />
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>过敏原</label>
              <div className="flex flex-wrap gap-2">
                {options.allergy_options.map((a) => {
                  const selected = allergies.includes(a.key);
                  return (
                    <button
                      key={a.key}
                      onClick={() => setAllergies(toggleItem(allergies, a.key))}
                      className="px-3 py-1.5 rounded-full text-sm transition-colors"
                      style={{
                        background: selected ? "var(--warning)" : "var(--bg-subtle)",
                        color: selected ? "#fff" : "var(--text-secondary)",
                        border: `1px solid ${selected ? "var(--warning)" : "var(--border-default)"}`,
                      }}
                    >
                      {a.label}
                    </button>
                  );
                })}
              </div>
            </div>
            {/* Preferred Ingredients */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>偏好食材</label>
              <input
                type="text"
                value={ingredientInput}
                onChange={(e) => setIngredientInput(e.target.value)}
                onKeyDown={handleIngredientKeyDown}
                placeholder="输入食材后按 Enter 添加"
                className="w-full px-3 py-2 rounded-lg text-sm outline-none"
                style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }}
              />
              {preferredIngredients.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {preferredIngredients.map((item) => (
                    <span
                      key={item}
                      className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm cursor-pointer transition-colors"
                      style={{
                        background: "var(--primary)",
                        color: "#fff",
                      }}
                      onClick={() => removeIngredient(item)}
                    >
                      {item}
                      <X className="w-3 h-3" />
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Section>

        {/* Constitution Types */}
        <Section title="体质辨识" icon={Heart}>
          <div>
            <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>选择你的体质（可多选）</label>
            <div className="flex flex-wrap gap-2">
              {CONSTITUTION_OPTIONS.map((c) => {
                const selected = constitutionTypes.includes(c.key);
                return (
                  <button
                    key={c.key}
                    onClick={() => setConstitutionTypes(toggleItem(constitutionTypes, c.key))}
                    className="px-3 py-2 rounded-xl text-sm transition-colors"
                    style={{
                      background: selected ? "var(--primary)" : "var(--bg-subtle)",
                      color: selected ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${selected ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {c.label}
                  </button>
                );
              })}
            </div>
          </div>
        </Section>

        {/* Cooking Conditions */}
        <Section title="烹饪条件" icon={ChefHat}>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>烹饪技能</label>
              <div className="flex flex-wrap gap-2">
                {options.cooking_methods.map((m) => (
                  <button
                    key={m.key}
                    onClick={() => setCookingMethod(m.key)}
                    className="px-3 py-1.5 rounded-full text-sm transition-colors"
                    style={{
                      background: cookingMethod === m.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: cookingMethod === m.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${cookingMethod === m.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>烹饪条件</label>
              <div className="flex gap-2">
                {options.cooking_facilities.map((f) => (
                  <button
                    key={f.key}
                    onClick={() => setCookingFacility(f.key)}
                    className="flex-1 py-2 rounded-lg text-sm transition-colors"
                    style={{
                      background: cookingFacility === f.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: cookingFacility === f.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${cookingFacility === f.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>备餐时间</label>
              <div className="flex flex-wrap gap-2">
                {options.meal_prep_times.map((t) => (
                  <button
                    key={t.key}
                    onClick={() => setMealPrepTime(t.key)}
                    className="px-3 py-1.5 rounded-full text-sm transition-colors"
                    style={{
                      background: mealPrepTime === t.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: mealPrepTime === t.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${mealPrepTime === t.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>就餐模式</label>
              <div className="flex gap-2">
                {options.meal_patterns.map((p) => (
                  <button
                    key={p.key}
                    onClick={() => setMealPattern(p.key)}
                    className="flex-1 py-2 rounded-lg text-sm transition-colors"
                    style={{
                      background: mealPattern === p.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: mealPattern === p.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${mealPattern === p.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
            {/* Cooking Frequency */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>做饭频次</label>
              <div className="flex flex-wrap gap-2">
                {COOKING_FREQUENCY_OPTIONS.map((o) => (
                  <button
                    key={o.key}
                    onClick={() => setCookingFrequency(o.key)}
                    className="px-3 py-1.5 rounded-full text-sm transition-colors"
                    style={{
                      background: cookingFrequency === o.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: cookingFrequency === o.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${cookingFrequency === o.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>
            {/* Takeout Preference */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>外卖偏好</label>
              <div className="flex flex-wrap gap-2">
                {TAKEOUT_PREFERENCE_OPTIONS.map((o) => (
                  <button
                    key={o.key}
                    onClick={() => setTakeoutPreference(o.key)}
                    className="px-3 py-1.5 rounded-full text-sm transition-colors"
                    style={{
                      background: takeoutPreference === o.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: takeoutPreference === o.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${takeoutPreference === o.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Section>

        {/* Health Conditions */}
        <Section title="健康情况" icon={Heart}>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>疾病情况（可多选）</label>
              <div className="flex flex-wrap gap-2">
                {options.health_condition_types.map((c) => {
                  const selected = healthConditions.includes(c.key);
                  return (
                    <button
                      key={c.key}
                      onClick={() => setHealthConditions(toggleItem(healthConditions, c.key))}
                      className="px-3 py-1.5 rounded-full text-sm transition-colors"
                      style={{
                        background: selected ? "var(--error)" : "var(--bg-subtle)",
                        color: selected ? "#fff" : "var(--text-secondary)",
                        border: `1px solid ${selected ? "var(--error)" : "var(--border-default)"}`,
                      }}
                    >
                      {c.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </Section>

        {/* Lifestyle */}
        <Section title="生活习惯" icon={Moon}>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>作息习惯</label>
              <div className="flex gap-2">
                {options.sleep_patterns.map((s) => (
                  <button
                    key={s.key}
                    onClick={() => setSleepPattern(s.key)}
                    className="flex-1 py-2 rounded-lg text-sm transition-colors"
                    style={{
                      background: sleepPattern === s.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: sleepPattern === s.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${sleepPattern === s.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>饮食预算</label>
              <div className="flex gap-2">
                {options.budget_levels.map((b) => (
                  <button
                    key={b.key}
                    onClick={() => setBudgetLevel(b.key)}
                    className="flex-1 py-2 rounded-lg text-sm transition-colors"
                    style={{
                      background: budgetLevel === b.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: budgetLevel === b.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${budgetLevel === b.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {b.label}
                  </button>
                ))}
              </div>
            </div>
            <InputField
              label="每日饮水目标 (ml)"
              value={waterIntakeGoal}
              onChange={setWaterIntakeGoal}
              type="number"
              placeholder="2000"
            />
          </div>
        </Section>

        {/* Family Cooking */}
        <Section title="家庭做饭" icon={Users}>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm" style={{ color: "var(--text-primary)" }}>是否为家人做饭</span>
              <button
                onClick={() => setFamilyCooking(!familyCooking)}
                className="relative w-12 h-7 rounded-full transition-colors"
                style={{ background: familyCooking ? "var(--primary)" : "var(--bg-subtle)", border: `1px solid ${familyCooking ? "var(--primary)" : "var(--border-default)"}` }}
              >
                <span
                  className="absolute top-0.5 w-6 h-6 rounded-full bg-white shadow transition-transform"
                  style={{ left: familyCooking ? "calc(100% - 1.625rem)" : "0.125rem" }}
                />
              </button>
            </div>
            {familyCooking && (
              <div className="space-y-3">
                {familyMembers.map((member, index) => (
                  <div
                    key={index}
                    className="p-3 rounded-xl space-y-3"
                    style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-default)" }}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>成员 {index + 1}</span>
                      <button
                        onClick={() => removeFamilyMember(index)}
                        className="p-1 rounded-lg transition-colors"
                        style={{ color: "var(--error)" }}
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    <InputField
                      label="昵称"
                      value={member.name}
                      onChange={(v) => updateFamilyMember(index, "name", v)}
                      placeholder="昵称"
                    />
                    <div>
                      <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>关系</label>
                      <select
                        value={member.relation}
                        onChange={(e) => updateFamilyMember(index, "relation", e.target.value)}
                        className="w-full px-3 py-2 rounded-lg text-sm outline-none"
                        style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }}
                      >
                        {RELATION_OPTIONS.map((r) => (
                          <option key={r.key} value={r.key}>{r.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>年龄段</label>
                      <select
                        value={member.age_group}
                        onChange={(e) => updateFamilyMember(index, "age_group", e.target.value)}
                        className="w-full px-3 py-2 rounded-lg text-sm outline-none"
                        style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }}
                      >
                        {AGE_GROUP_OPTIONS.map((a) => (
                          <option key={a.key} value={a.key}>{a.label}</option>
                        ))}
                      </select>
                    </div>
                    <InputField
                      label="饮食注意"
                      value={member.diet_note}
                      onChange={(v) => updateFamilyMember(index, "diet_note", v)}
                      placeholder="如：不吃辣、对花生过敏"
                    />
                  </div>
                ))}
                <button
                  onClick={addFamilyMember}
                  className="flex items-center justify-center gap-1.5 w-full py-2.5 rounded-xl text-sm font-medium transition-colors"
                  style={{
                    background: "var(--bg-subtle)",
                    color: "var(--primary)",
                    border: "1px dashed var(--primary)",
                  }}
                >
                  <Plus className="w-4 h-4" />
                  添加家庭成员
                </button>
              </div>
            )}
          </div>
        </Section>
      </main>
    </div>
  );
}

// Helper components
function Section({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border overflow-hidden" style={{ borderColor: "var(--border-default)" }}>
      <div className="flex items-center gap-2 px-4 py-3" style={{ background: "var(--bg-subtle)" }}>
        <Icon className="w-4 h-4" style={{ color: "var(--primary)" }} />
        <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{title}</span>
      </div>
      <div className="px-4 py-4">{children}</div>
    </div>
  );
}

function InputField({ label, value, onChange, type = "text", placeholder }: {
  label: string; value: string; onChange: (v: string) => void; type?: string; placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 rounded-lg text-sm outline-none"
        style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }}
      />
    </div>
  );
}
