"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "@/components/ui/toast";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/* ───── Step 2: Health Goals ───── */
const GOALS = [
  {
    key: "weight_loss", label: "减脂减重", emoji: "🔥",
    subGoals: [{ key: "rapid_loss", label: "速减" }, { key: "slow_loss", label: "慢减" }, { key: "body_shape", label: "塑形" }],
  },
  {
    key: "fertility", label: "备孕调理", emoji: "🌸",
    subGoals: [
      { key: "pregnancy_preparing", label: "备孕中" },
      { key: "early_pregnancy", label: "孕早期" },
      { key: "mid_pregnancy", label: "孕中期" },
      { key: "late_pregnancy", label: "孕晚期" },
      { key: "breastfeeding", label: "哺乳期" },
    ],
  },
  {
    key: "health", label: "养生保健", emoji: "🧘",
    subGoals: [
      { key: "qi_blood", label: "气血不足" },
      { key: "spleen_stomach", label: "脾胃调理" },
      { key: "kidney", label: "补肾" },
      { key: "liver", label: "护肝" },
      { key: "sleep", label: "安神助眠" },
    ],
  },
  {
    key: "muscle", label: "增肌塑形", emoji: "💪",
    subGoals: [{ key: "muscle_gain", label: "增肌" }, { key: "body_recomp", label: "减脂塑形" }, { key: "recovery", label: "运动恢复" }],
  },
  {
    key: "chronic_disease", label: "慢病管理", emoji: "🩺",
    subGoals: [
      { key: "diabetes", label: "糖尿病" },
      { key: "hypertension", label: "高血压" },
      { key: "hyperlipidemia", label: "高血脂" },
      { key: "gout", label: "痛风" },
      { key: "stomach", label: "胃病" },
    ],
  },
];

/* ───── Step 3: Constitution ───── */
const CONSTITUTIONS = [
  { key: "yang_deficiency", label: "阳虚质", emoji: "☀️", desc: "怕冷、手脚凉、喜热饮", questions: ["经常手脚冰凉？", "喜欢吃热食热饮？", "容易腹泻？"] },
  { key: "yin_deficiency", label: "阴虚质", emoji: "🔥", desc: "口干、手心热、易上火", questions: ["经常口干咽燥？", "手心脚心发热？", "容易上火长痘？"] },
  { key: "qi_deficiency", label: "气虚质", emoji: "💨", desc: "乏力、气短、易感冒", questions: ["容易疲乏无力？", "说话声音低？", "容易感冒？"] },
  { key: "blood_stasis", label: "血瘀质", emoji: "🩸", desc: "皮肤暗沉、易瘀青", questions: ["皮肤容易暗沉？", "容易有瘀青？", "嘴唇颜色偏暗？"] },
  { key: "phlegm_dampness", label: "痰湿质", emoji: "🌊", desc: "体胖、痰多、面部油腻", questions: ["体型偏胖？", "面部容易出油？", "痰多或身重不爽？"] },
  { key: "damp_heat", label: "湿热质", emoji: "🌿", desc: "面垢油光、口苦、长痘", questions: ["面部油光长痘？", "口苦口臭？", "小便偏黄？"] },
  { key: "qi_stagnation", label: "气郁质", emoji: "😰", desc: "情绪低落、胸闷叹气", questions: ["容易情绪低落？", "经常叹气胸闷？", "多愁善感？"] },
  { key: "special_diathesis", label: "特禀质", emoji: "❄️", desc: "过敏体质", questions: ["容易过敏打喷嚏？", "皮肤容易瘙痒？", "对花粉或食物过敏？"] },
  { key: "neutral", label: "平和质", emoji: "⚖️", desc: "正常体质，无特殊不适", questions: [] },
];

/* ───── Step 4: Diet ───── */
const DIET_TYPES = [
  { key: "normal", label: "普通饮食" },
  { key: "vegetarian", label: "素食" },
  { key: "low_carb", label: "低碳水" },
  { key: "mediterranean", label: "地中海饮食" },
  { key: "high_protein", label: "高蛋白" },
];

const TASTE_OPTIONS = [
  { key: "light", label: "清淡" },
  { key: "spicy", label: "辣味" },
  { key: "sweet", label: "甜味" },
  { key: "sour", label: "酸味" },
  { key: "salty", label: "咸香" },
];

const CUISINE_OPTIONS = [
  "川菜", "粤菜", "湘菜", "鲁菜", "日料", "韩餐", "西餐", "东北菜",
];

const ALLERGY_OPTIONS = [
  "牛奶", "鸡蛋", "花生", "海鲜", "麸质", "大豆", "坚果", "贝类",
  "酒精", "蜂蜜", "芝麻", "芒果", "芹菜", "亚硫酸盐",
];

const INGREDIENT_OPTIONS = [
  "鸡胸肉", "三文鱼", "牛肉", "虾", "豆腐", "鸡蛋", "牛奶", "猪肉",
  "鲈鱼", "排骨", "羊肉", "鸭肉", "菠菜", "西兰花", "番茄", "黄瓜",
  "南瓜", "红薯", "玉米", "糙米", "燕麦", "全麦面包", "酸奶",
];

/* ───── Step 5: Cooking & Lifestyle ───── */
const COOKING_METHODS = [
  { key: "simple", label: "简单（煮/微波）" },
  { key: "medium", label: "中等（炒/煎）" },
  { key: "advanced", label: "高级（烘焙/慢炖）" },
];

const COOKING_FREQUENCIES = [
  { key: "often", label: "天天做" },
  { key: "sometimes", label: "3-5次/周" },
  { key: "rarely", label: "偶尔" },
  { key: "never", label: "从不做饭" },
];

const COOKING_FACILITIES = [
  { key: "full_kitchen", label: "完整厨房" },
  { key: "no_kitchen", label: "无厨房" },
];

const MEAL_PREP_TIMES = [
  { key: "none", label: "没时间" },
  { key: "15min", label: "15分钟" },
  { key: "30min", label: "30分钟" },
  { key: "60min+", label: "1小时+" },
];

const MEAL_PATTERNS = [
  { key: "3_meals", label: "一日三餐" },
  { key: "4_meals", label: "含加餐" },
  { key: "5_meals", label: "少食多餐" },
];

const TAKEOUT_PREFERENCES = [
  { key: "healthy_light", label: "营养轻食" },
  { key: "home_style", label: "家常菜" },
  { key: "fast_food", label: "快餐" },
  { key: "any", label: "都行" },
];

const SLEEP_PATTERNS = [
  { key: "early_bird", label: "早睡早起" },
  { key: "night_owl", label: "晚睡晚起" },
];

const BUDGET_LEVELS = [
  { key: "low", label: "经济实惠" },
  { key: "medium", label: "适中" },
  { key: "high", label: "不限预算" },
];

/* ───── Step 6: Family ───── */
const RELATION_OPTIONS = ["老公", "老婆", "孩子", "父母", "公婆", "其他"];
const AGE_GROUP_OPTIONS = ["0-3岁", "3-6岁", "6-12岁", "12-18岁", "18-60岁", "60岁以上"];
const FAMILY_DIET_NOTES = ["无特殊", "低盐", "低糖", "补钙", "补铁", "易消化", "其他"];

/* ================================================================ */
/*  Component                                                        */
/* ================================================================ */
export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);

  // Step 1: Body data
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState<"male" | "female" | "">("");
  const [targetWeight, setTargetWeight] = useState("");

  // Step 2: Goals (multi-select) + sub-goals
  const [goals, setGoals] = useState<string[]>([]);
  const [healthSubGoals, setHealthSubGoals] = useState<string[]>([]);

  // Step 3: Constitution
  const [constitutionTypes, setConstitutionTypes] = useState<string[]>([]);
  const [constitutionAnswers, setConstitutionAnswers] = useState<Record<string, Record<number, string>>>({});

  // Step 4: Diet preferences
  const [dietType, setDietType] = useState("normal");
  const [tastePref, setTastePref] = useState<string[]>([]);
  const [cuisinePref, setCuisinePref] = useState<string[]>([]);
  const [allergies, setAllergies] = useState<string[]>([]);
  const [dislikedFoods, setDislikedFoods] = useState("");
  const [preferredIngredients, setPreferredIngredients] = useState<string[]>([]);
  const [ingredientSearch, setIngredientSearch] = useState("");

  // Step 5: Cooking & Lifestyle
  const [cookingMethod, setCookingMethod] = useState("simple");
  const [cookingFrequency, setCookingFrequency] = useState("often");
  const [cookingFacility, setCookingFacility] = useState("full_kitchen");
  const [mealPrepTime, setMealPrepTime] = useState("30min");
  const [mealPattern, setMealPattern] = useState("3_meals");
  const [takeoutPreference, setTakeoutPreference] = useState("any");
  const [sleepPattern, setSleepPattern] = useState("early_bird");
  const [budgetLevel, setBudgetLevel] = useState("medium");
  const [waterIntakeGoal, setWaterIntakeGoal] = useState("");

  // Step 6: Family
  const [familyCooking, setFamilyCooking] = useState(false);
  const [familyMembers, setFamilyMembers] = useState<
    Array<{ name: string; relation: string; age_group: string; diet_note: string[] }>
  >([]);

  /* ───── Toggles ───── */
  const toggleGoal = (key: string) => {
    setGoals((prev) => {
      const next = prev.includes(key) ? prev.filter((g) => g !== key) : [...prev, key];
      // Remove sub-goals belonging to a de-selected goal
      if (!next.includes(key)) {
        const goal = GOALS.find((g) => g.key === key);
        if (goal) {
          const subKeys = goal.subGoals.map((s) => s.key);
          setHealthSubGoals((prevSub) => prevSub.filter((s) => !subKeys.includes(s)));
        }
      }
      return next;
    });
  };

  const toggleSubGoal = (key: string) => {
    setHealthSubGoals((prev) =>
      prev.includes(key) ? prev.filter((s) => s !== key) : [...prev, key]
    );
  };

  const toggleConstitution = (key: string) => {
    setConstitutionTypes((prev) => {
      // If selecting "neutral", clear all others
      if (key === "neutral") {
        if (prev.includes("neutral")) return [];
        setConstitutionAnswers({});
        return ["neutral"];
      }
      // If selecting a non-neutral, remove "neutral" if present
      const withoutNeutral = prev.includes("neutral") ? [] : prev;
      const next = withoutNeutral.includes(key)
        ? withoutNeutral.filter((c) => c !== key)
        : [...withoutNeutral, key];
      // Clean up answers for removed types
      if (!next.includes(key)) {
        setConstitutionAnswers((ans) => {
          const copy = { ...ans };
          delete copy[key];
          return copy;
        });
      }
      return next;
    });
  };

  const setConstitutionAnswer = (ckey: string, qIdx: number, value: string) => {
    setConstitutionAnswers((prev) => ({
      ...prev,
      [ckey]: { ...(prev[ckey] || {}), [qIdx]: value },
    }));
  };

  const toggleTaste = (key: string) => {
    setTastePref((prev) =>
      prev.includes(key) ? prev.filter((t) => t !== key) : [...prev, key]
    );
  };

  const toggleCuisine = (item: string) => {
    setCuisinePref((prev) =>
      prev.includes(item) ? prev.filter((c) => c !== item) : [...prev, item]
    );
  };

  const toggleAllergy = (item: string) => {
    setAllergies((prev) =>
      prev.includes(item) ? prev.filter((a) => a !== item) : [...prev, item]
    );
  };

  const toggleIngredient = (item: string) => {
    setPreferredIngredients((prev) =>
      prev.includes(item) ? prev.filter((i) => i !== item) : [...prev, item]
    );
  };

  const addFamilyMember = () => {
    setFamilyMembers((prev) => [
      ...prev,
      { name: "", relation: "", age_group: "", diet_note: [] },
    ]);
  };

  const removeFamilyMember = (idx: number) => {
    setFamilyMembers((prev) => prev.filter((_, i) => i !== idx));
  };

  const updateFamilyMember = (
    idx: number,
    field: "name" | "relation" | "age_group" | "diet_note",
    value: string | string[]
  ) => {
    setFamilyMembers((prev) =>
      prev.map((m, i) => (i === idx ? { ...m, [field]: value } : m))
    );
  };

  const toggleFamilyDietNote = (idx: number, note: string) => {
    setFamilyMembers((prev) =>
      prev.map((m, i) => {
        if (i !== idx) return m;
        const notes = m.diet_note.includes(note)
          ? m.diet_note.filter((n) => n !== note)
          : [...m.diet_note, note];
        return { ...m, diet_note: notes };
      })
    );
  };

  /* ───── Helpers ───── */
  const canNext = () => {
    if (step === 1) return height && weight && age && gender;
    if (step === 2) return goals.length > 0;
    if (step === 3) return true;
    if (step === 4) return true;
    if (step === 5) return true;
    if (step === 6) return true;
    return true;
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/users/onboarding`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          height_cm: Number(height),
          weight_kg: Number(weight),
          age: Number(age),
          gender,
          target_weight: targetWeight ? Number(targetWeight) : null,
          goals,
          health_sub_goals: healthSubGoals,
          constitution_types: constitutionTypes,
          constitution_answers: constitutionAnswers,
          diet_type: dietType,
          taste_pref: tastePref,
          cuisine_pref: cuisinePref,
          allergies,
          disliked_foods: dislikedFoods ? dislikedFoods.split(/[,，、\s]+/).filter(Boolean) : [],
          preferred_ingredients: preferredIngredients,
          cooking_method: cookingMethod,
          cooking_frequency: cookingFrequency,
          cooking_facility: cookingFacility,
          meal_prep_time: mealPrepTime,
          meal_pattern: mealPattern,
          takeout_preference: takeoutPreference,
          sleep_pattern: sleepPattern,
          budget_level: budgetLevel,
          water_intake_goal: waterIntakeGoal ? Number(waterIntakeGoal) : null,
          family_cooking: familyCooking,
          family_members: familyMembers,
        }),
      });
      if (!res.ok) throw new Error("提交失败");
      toast("success", "设置完成，欢迎使用 MealMuse!");
      router.push("/");
    } catch {
      toast("error", "提交失败，请重试");
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    if (step < 6) {
      setStep(step + 1);
    } else {
      handleSubmit();
    }
  };

  /* ───── Check if all answers for a constitution are "否" ───── */
  const isConstitutionDenied = (ckey: string) => {
    const c = CONSTITUTIONS.find((x) => x.key === ckey);
    if (!c || c.questions.length === 0) return false;
    const ans = constitutionAnswers[ckey];
    if (!ans) return false;
    return c.questions.every((_, idx) => ans[idx] === "否");
  };

  /* ───── Filter ingredients by search ───── */
  const filteredIngredients = ingredientSearch.trim()
    ? INGREDIENT_OPTIONS.filter((i) => i.includes(ingredientSearch.trim()))
    : INGREDIENT_OPTIONS;

  /* ================================================================ */
  /*  Render                                                           */
  /* ================================================================ */
  return (
    <div
      className="min-h-screen flex items-center justify-center px-4 py-8"
      style={{ background: "var(--bg-page)" }}
    >
      <div
        className="w-full max-w-md rounded-2xl p-6 shadow-sm"
        style={{ background: "var(--bg-card)", border: "1px solid var(--border-default)" }}
      >
        {/* ──── Progress bar ──── */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              第 {step} 步 / 共 6 步
            </span>
            <span className="text-sm font-bold" style={{ color: "var(--primary)" }}>
              {Math.round((step / 6) * 100)}%
            </span>
          </div>
          <div
            className="w-full h-2 rounded-full overflow-hidden"
            style={{ background: "var(--border-default)" }}
          >
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{ width: `${(step / 6) * 100}%`, background: "var(--primary)" }}
            />
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════ */}
        {/*  Step 1: Body data                                        */}
        {/* ═══════════════════════════════════════════════════════════ */}
        {step === 1 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
                身体数据
              </h2>
              <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
                帮助 AI 为你定制饮食方案
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
                  身高 (cm)
                </label>
                <input
                  type="number"
                  value={height}
                  onChange={(e) => setHeight(e.target.value)}
                  placeholder="165"
                  className="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
                  style={{
                    background: "var(--bg-subtle)",
                    border: "1px solid var(--border-default)",
                    color: "var(--text-primary)",
                  }}
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
                  体重 (kg)
                </label>
                <input
                  type="number"
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                  placeholder="55"
                  className="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
                  style={{
                    background: "var(--bg-subtle)",
                    border: "1px solid var(--border-default)",
                    color: "var(--text-primary)",
                  }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
                  年龄
                </label>
                <input
                  type="number"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  placeholder="28"
                  className="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
                  style={{
                    background: "var(--bg-subtle)",
                    border: "1px solid var(--border-default)",
                    color: "var(--text-primary)",
                  }}
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
                  性别
                </label>
                <div className="flex gap-2">
                  {[
                    { key: "female", label: "女" },
                    { key: "male", label: "男" },
                  ].map((g) => (
                    <button
                      key={g.key}
                      onClick={() => setGender(g.key as "male" | "female")}
                      className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors"
                      style={{
                        background: gender === g.key ? "var(--primary)" : "var(--bg-subtle)",
                        color: gender === g.key ? "#fff" : "var(--text-secondary)",
                        border: `1px solid ${gender === g.key ? "var(--primary)" : "var(--border-default)"}`,
                      }}
                    >
                      {g.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
                目标体重 (kg)（可选）
              </label>
              <input
                type="number"
                value={targetWeight}
                onChange={(e) => setTargetWeight(e.target.value)}
                placeholder="50"
                className="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
                style={{
                  background: "var(--bg-subtle)",
                  border: "1px solid var(--border-default)",
                  color: "var(--text-primary)",
                }}
              />
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════ */}
        {/*  Step 2: Health Goals (enhanced with sub-goals)            */}
        {/* ═══════════════════════════════════════════════════════════ */}
        {step === 2 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
                健康目标
              </h2>
              <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
                可多选，AI 会据此调整推荐
              </p>
            </div>

            <div className="space-y-3">
              {GOALS.map((g) => {
                const selected = goals.includes(g.key);
                return (
                  <div key={g.key}>
                    <button
                      onClick={() => toggleGoal(g.key)}
                      className="w-full p-4 rounded-xl text-left transition-all"
                      style={{
                        background: selected ? "var(--primary)" : "var(--bg-subtle)",
                        color: selected ? "#fff" : "var(--text-primary)",
                        border: `1.5px solid ${selected ? "var(--primary)" : "var(--border-default)"}`,
                      }}
                    >
                      <span className="text-2xl mr-2">{g.emoji}</span>
                      <span className="text-sm font-medium">{g.label}</span>
                    </button>

                    {/* Sub-goal pills when selected */}
                    {selected && (
                      <div className="flex flex-wrap gap-2 mt-2 ml-1">
                        {g.subGoals.map((sg) => {
                          const subSelected = healthSubGoals.includes(sg.key);
                          return (
                            <button
                              key={sg.key}
                              onClick={() => toggleSubGoal(sg.key)}
                              className="px-3 py-1.5 rounded-full text-sm transition-colors"
                              style={{
                                background: subSelected
                                  ? "rgba(255,255,255,0.3)"
                                  : "var(--bg-subtle)",
                                color: subSelected ? "#fff" : "var(--text-secondary)",
                                border: `1px solid ${subSelected ? "rgba(255,255,255,0.5)" : "var(--border-default)"}`,
                              }}
                            >
                              {sg.label}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════ */}
        {/*  Step 3: Constitution (new)                               */}
        {/* ═══════════════════════════════════════════════════════════ */}
        {step === 3 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
                体质辨识
              </h2>
              <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
                根据中医体质学说，选择符合你的体质（可多选）
              </p>
            </div>

            <div className="grid grid-cols-3 gap-2.5">
              {CONSTITUTIONS.map((c) => {
                const selected = constitutionTypes.includes(c.key);
                const denied = isConstitutionDenied(c.key);
                return (
                  <div key={c.key}>
                    <button
                      onClick={() => toggleConstitution(c.key)}
                      className="w-full p-3 rounded-xl text-center transition-all"
                      style={{
                        background: selected ? "var(--primary)" : "var(--bg-subtle)",
                        color: selected ? "#fff" : "var(--text-primary)",
                        border: `1.5px solid ${selected ? "var(--primary)" : "var(--border-default)"}`,
                        opacity: denied ? 0.5 : 1,
                      }}
                    >
                      <span className="text-xl block mb-1">{c.emoji}</span>
                      <span className="text-xs font-medium block">{c.label}</span>
                      <span
                        className="text-[10px] block mt-0.5 leading-tight"
                        style={{ color: selected ? "rgba(255,255,255,0.8)" : "var(--text-secondary)" }}
                      >
                        {c.desc}
                      </span>
                    </button>

                    {/* Confirmation questions */}
                    {selected && c.questions.length > 0 && !denied && (
                      <div
                        className="mt-2 p-2.5 rounded-xl space-y-2"
                        style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-default)" }}
                      >
                        {c.questions.map((q, qIdx) => (
                          <div key={qIdx}>
                            <p
                              className="text-xs font-medium mb-1"
                              style={{ color: "var(--text-primary)" }}
                            >
                              {q}
                            </p>
                            <div className="flex gap-1.5">
                              {["是", "否", "不确定"].map((opt) => {
                                const ans = constitutionAnswers[c.key]?.[qIdx];
                                const active = ans === opt;
                                return (
                                  <button
                                    key={opt}
                                    onClick={() => setConstitutionAnswer(c.key, qIdx, opt)}
                                    className="flex-1 py-1 rounded-full text-xs transition-colors"
                                    style={{
                                      background: active ? "var(--primary)" : "var(--bg-card)",
                                      color: active ? "#fff" : "var(--text-secondary)",
                                      border: `1px solid ${active ? "var(--primary)" : "var(--border-default)"}`,
                                    }}
                                  >
                                    {opt}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Denied hint */}
                    {denied && (
                      <p
                        className="text-[10px] text-center mt-1"
                        style={{ color: "var(--warning)" }}
                      >
                        你可能不是这个体质
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════ */}
        {/*  Step 4: Diet preferences (enhanced)                      */}
        {/* ═══════════════════════════════════════════════════════════ */}
        {step === 4 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
                饮食偏好
              </h2>
              <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
                让推荐更贴合你的口味
              </p>
            </div>

            {/* Diet type */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                饮食类型
              </label>
              <div className="flex flex-wrap gap-2">
                {DIET_TYPES.map((d) => (
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

            {/* Taste */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                口味偏好（可多选）
              </label>
              <div className="flex flex-wrap gap-2">
                {TASTE_OPTIONS.map((t) => {
                  const selected = tastePref.includes(t.key);
                  return (
                    <button
                      key={t.key}
                      onClick={() => toggleTaste(t.key)}
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

            {/* Cuisine */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                偏好菜系（可多选）
              </label>
              <div className="flex flex-wrap gap-2">
                {CUISINE_OPTIONS.map((c) => {
                  const selected = cuisinePref.includes(c);
                  return (
                    <button
                      key={c}
                      onClick={() => toggleCuisine(c)}
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

            {/* Preferred ingredients */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                偏好食材（可多选）
              </label>
              <input
                type="text"
                value={ingredientSearch}
                onChange={(e) => setIngredientSearch(e.target.value)}
                placeholder="搜索食材..."
                className="w-full px-3 py-2 rounded-xl text-sm outline-none mb-2"
                style={{
                  background: "var(--bg-subtle)",
                  border: "1px solid var(--border-default)",
                  color: "var(--text-primary)",
                }}
              />
              <div className="flex flex-wrap gap-2">
                {filteredIngredients.map((item) => {
                  const selected = preferredIngredients.includes(item);
                  return (
                    <button
                      key={item}
                      onClick={() => toggleIngredient(item)}
                      className="px-3 py-1.5 rounded-full text-sm transition-colors"
                      style={{
                        background: selected ? "var(--primary)" : "var(--bg-subtle)",
                        color: selected ? "#fff" : "var(--text-secondary)",
                        border: `1px solid ${selected ? "var(--primary)" : "var(--border-default)"}`,
                      }}
                    >
                      {item}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Allergies */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                过敏忌口（可多选）
              </label>
              <div className="flex flex-wrap gap-2">
                {ALLERGY_OPTIONS.map((a) => {
                  const selected = allergies.includes(a);
                  return (
                    <button
                      key={a}
                      onClick={() => toggleAllergy(a)}
                      className="px-3 py-1.5 rounded-full text-sm transition-colors"
                      style={{
                        background: selected ? "var(--warning)" : "var(--bg-subtle)",
                        color: selected ? "#fff" : "var(--text-secondary)",
                        border: `1px solid ${selected ? "var(--warning)" : "var(--border-default)"}`,
                      }}
                    >
                      {a}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Disliked foods */}
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
                其他忌口食物（用逗号分隔）
              </label>
              <input
                type="text"
                value={dislikedFoods}
                onChange={(e) => setDislikedFoods(e.target.value)}
                placeholder="如：香菜，芹菜"
                className="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
                style={{
                  background: "var(--bg-subtle)",
                  border: "1px solid var(--border-default)",
                  color: "var(--text-primary)",
                }}
              />
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════ */}
        {/*  Step 5: Cooking & Lifestyle (merged)                     */}
        {/* ═══════════════════════════════════════════════════════════ */}
        {step === 5 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
                烹饪与生活
              </h2>
              <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
                让推荐更适合你的实际情况
              </p>
            </div>

            {/* Cooking method */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                烹饪技能
              </label>
              <div className="flex flex-wrap gap-2">
                {COOKING_METHODS.map((m) => (
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

            {/* Cooking frequency (new) */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                做饭频率
              </label>
              <div className="flex flex-wrap gap-2">
                {COOKING_FREQUENCIES.map((f) => (
                  <button
                    key={f.key}
                    onClick={() => setCookingFrequency(f.key)}
                    className="px-3 py-1.5 rounded-full text-sm transition-colors"
                    style={{
                      background: cookingFrequency === f.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: cookingFrequency === f.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${cookingFrequency === f.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Cooking facility */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                烹饪条件
              </label>
              <div className="flex gap-2">
                {COOKING_FACILITIES.map((f) => (
                  <button
                    key={f.key}
                    onClick={() => setCookingFacility(f.key)}
                    className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors"
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

            {/* Meal prep time */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                备餐时间
              </label>
              <div className="flex flex-wrap gap-2">
                {MEAL_PREP_TIMES.map((t) => (
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

            {/* Meal pattern */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                就餐模式
              </label>
              <div className="flex gap-2">
                {MEAL_PATTERNS.map((p) => (
                  <button
                    key={p.key}
                    onClick={() => setMealPattern(p.key)}
                    className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors"
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

            {/* Takeout preference (new) */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                外卖偏好
              </label>
              <div className="flex flex-wrap gap-2">
                {TAKEOUT_PREFERENCES.map((t) => (
                  <button
                    key={t.key}
                    onClick={() => setTakeoutPreference(t.key)}
                    className="px-3 py-1.5 rounded-full text-sm transition-colors"
                    style={{
                      background: takeoutPreference === t.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: takeoutPreference === t.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${takeoutPreference === t.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Sleep pattern */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                作息习惯
              </label>
              <div className="flex gap-2">
                {SLEEP_PATTERNS.map((s) => (
                  <button
                    key={s.key}
                    onClick={() => setSleepPattern(s.key)}
                    className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors"
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

            {/* Budget level */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                饮食预算
              </label>
              <div className="flex gap-2">
                {BUDGET_LEVELS.map((b) => (
                  <button
                    key={b.key}
                    onClick={() => setBudgetLevel(b.key)}
                    className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors"
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

            {/* Water intake goal */}
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
                每日饮水目标 (ml)
              </label>
              <input
                type="number"
                value={waterIntakeGoal}
                onChange={(e) => setWaterIntakeGoal(e.target.value)}
                placeholder="2000"
                className="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
                style={{
                  background: "var(--bg-subtle)",
                  border: "1px solid var(--border-default)",
                  color: "var(--text-primary)",
                }}
              />
              <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>
                建议 1500-2500ml，留空则不设目标
              </p>
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════ */}
        {/*  Step 6: Family members (new)                             */}
        {/* ═══════════════════════════════════════════════════════════ */}
        {step === 6 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
                家庭成员
              </h2>
              <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
                为家人定制饮食方案
              </p>
            </div>

            {/* Family cooking toggle */}
            <div>
              <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                你是否为家人做饭？
              </label>
              <div className="flex gap-2">
                {[
                  { key: true, label: "是" },
                  { key: false, label: "否" },
                ].map((opt) => (
                  <button
                    key={String(opt.key)}
                    onClick={() => setFamilyCooking(opt.key)}
                    className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors"
                    style={{
                      background: familyCooking === opt.key ? "var(--primary)" : "var(--bg-subtle)",
                      color: familyCooking === opt.key ? "#fff" : "var(--text-secondary)",
                      border: `1px solid ${familyCooking === opt.key ? "var(--primary)" : "var(--border-default)"}`,
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Family members list */}
            {familyCooking && (
              <div className="space-y-3">
                {familyMembers.map((member, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl space-y-2.5"
                    style={{
                      background: "var(--bg-subtle)",
                      border: "1px solid var(--border-default)",
                    }}
                  >
                    {/* Header with delete */}
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                        成员 {idx + 1}
                      </span>
                      <button
                        onClick={() => removeFamilyMember(idx)}
                        className="text-xs px-2 py-1 rounded-full transition-colors"
                        style={{
                          background: "var(--warning)",
                          color: "#fff",
                        }}
                      >
                        删除
                      </button>
                    </div>

                    {/* Name */}
                    <input
                      type="text"
                      value={member.name}
                      onChange={(e) => updateFamilyMember(idx, "name", e.target.value)}
                      placeholder="昵称"
                      className="w-full px-3 py-2 rounded-xl text-sm outline-none"
                      style={{
                        background: "var(--bg-card)",
                        border: "1px solid var(--border-default)",
                        color: "var(--text-primary)",
                      }}
                    />

                    {/* Relation */}
                    <select
                      value={member.relation}
                      onChange={(e) => updateFamilyMember(idx, "relation", e.target.value)}
                      className="w-full px-3 py-2 rounded-xl text-sm outline-none"
                      style={{
                        background: "var(--bg-card)",
                        border: "1px solid var(--border-default)",
                        color: "var(--text-primary)",
                      }}
                    >
                      <option value="">选择关系</option>
                      {RELATION_OPTIONS.map((r) => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>

                    {/* Age group */}
                    <select
                      value={member.age_group}
                      onChange={(e) => updateFamilyMember(idx, "age_group", e.target.value)}
                      className="w-full px-3 py-2 rounded-xl text-sm outline-none"
                      style={{
                        background: "var(--bg-card)",
                        border: "1px solid var(--border-default)",
                        color: "var(--text-primary)",
                      }}
                    >
                      <option value="">选择年龄段</option>
                      {AGE_GROUP_OPTIONS.map((a) => (
                        <option key={a} value={a}>{a}</option>
                      ))}
                    </select>

                    {/* Diet notes */}
                    <div>
                      <label className="block text-[10px] font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                        饮食注意
                      </label>
                      <div className="flex flex-wrap gap-1.5">
                        {FAMILY_DIET_NOTES.map((note) => {
                          const selected = member.diet_note.includes(note);
                          return (
                            <button
                              key={note}
                              onClick={() => toggleFamilyDietNote(idx, note)}
                              className="px-2.5 py-1 rounded-full text-xs transition-colors"
                              style={{
                                background: selected ? "var(--primary)" : "var(--bg-card)",
                                color: selected ? "#fff" : "var(--text-secondary)",
                                border: `1px solid ${selected ? "var(--primary)" : "var(--border-default)"}`,
                              }}
                            >
                              {note}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Add member button */}
                <button
                  onClick={addFamilyMember}
                  className="w-full py-3 rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-1"
                  style={{
                    background: "var(--bg-subtle)",
                    color: "var(--primary)",
                    border: "1.5px dashed var(--primary)",
                  }}
                >
                  <span className="text-lg">+</span>
                  添加家庭成员
                </button>
              </div>
            )}
          </div>
        )}

        {/* ──── Navigation buttons ──── */}
        <div className="flex gap-3 mt-8">
          {step > 1 && (
            <button
              onClick={() => setStep(step - 1)}
              className="flex-1 py-3 rounded-xl text-sm font-medium transition-colors"
              style={{
                background: "var(--bg-subtle)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border-default)",
              }}
            >
              上一步
            </button>
          )}
          <button
            onClick={handleNext}
            disabled={!canNext() || submitting}
            className="flex-1 py-3 rounded-xl text-sm font-bold text-white transition-colors disabled:opacity-50"
            style={{ background: "var(--primary)" }}
          >
            {step < 6 ? "下一步" : submitting ? "提交中..." : "开始使用 🎉"}
          </button>
        </div>
      </div>
    </div>
  );
}
