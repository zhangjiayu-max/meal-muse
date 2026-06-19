# Couple Preconception Meal Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight couple preconception meal planning flow that generates one shared menu with separate portions and nutrition rationale for the primary user and partner.

**Architecture:** Keep the first implementation scoped to existing `UserProfile` and `MealPlan` JSONB fields. Add partner and goal-priority fields to the profile, pass couple context into the meal plan engine, enhance the AI JSON contract, and render the extra serving advice in the mobile plan page. Avoid full household collaboration tables until the couple plan proves useful.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Pydantic, PostgreSQL JSONB, Next.js App Router, React, Tailwind CSS v4, axios.

---

## File Map

- `meal-muse-api/app/models/user_profile.py`: add profile fields for couple planning.
- `meal-muse-api/app/schemas/user.py`: expose partner profile and couple settings in profile update/response.
- `meal-muse-api/app/schemas/meal.py`: allow enhanced meal details with serving advice and recommendation reasons.
- `meal-muse-api/app/api/v1/users.py`: accept onboarding values for goal priority and partner profile.
- `meal-muse-api/app/api/v1/meals.py`: pass generate options into the engine.
- `meal-muse-api/app/services/context_builder.py`: include couple details in AI context summaries.
- `meal-muse-api/app/services/meal_plan_engine.py`: fix prompt delivery, generate couple plans, preserve generation params, and enhance fallback meals.
- `meal-muse-web/types/index.ts`: add frontend profile and meal-plan types.
- `meal-muse-web/app/onboarding/page.tsx`: add goal-priority and partner profile inputs.
- `meal-muse-web/app/(main)/plan/page.tsx`: render couple plan title, serving advice, and AI reasons.

## Task 1: Backend Profile Schema And Onboarding Fields

**Files:**
- Modify: `meal-muse-api/app/models/user_profile.py`
- Modify: `meal-muse-api/app/schemas/user.py`
- Modify: `meal-muse-api/app/api/v1/users.py`

- [ ] **Step 1: Add model fields**

In `meal-muse-api/app/models/user_profile.py`, add these fields after `health_sub_goals`:

```python
    goal_priority: Mapped[str] = mapped_column(String(30), default="pregnancy_safe")
    partner_profile: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    couple_plan_enabled: Mapped[bool] = mapped_column(default=False)
```

- [ ] **Step 2: Add Pydantic partner schema**

In `meal-muse-api/app/schemas/user.py`, add before `UserProfileResponse`:

```python
class PartnerProfile(BaseModel):
    nickname: str | None = None
    gender: str | None = None
    age: int | None = None
    height_cm: float | None = None
    current_weight: float | None = None
    activity_level: str | None = None
    taste_preference: str | None = None
    cuisine_preference: list[str] | None = None
    disliked_foods: list[str] | None = None
    allergens: list[str] | None = None
    diet_notes: list[str] | None = None
    daily_calorie_target: int | None = None
    macro_targets: dict | None = None
```

- [ ] **Step 3: Expose profile response/update fields**

In `UserProfileResponse`, add:

```python
    goal_priority: str = "pregnancy_safe"
    partner_profile: PartnerProfile | dict | None = None
    couple_plan_enabled: bool = False
```

In `UserProfileUpdate`, add:

```python
    goal_priority: str | None = None
    partner_profile: PartnerProfile | dict | None = None
    couple_plan_enabled: bool | None = None
```

- [ ] **Step 4: Extend onboarding request**

In `meal-muse-api/app/api/v1/users.py`, add to `OnboardingRequest`:

```python
    goal_priority: str = Field(default="pregnancy_safe", description="pregnancy_safe/weight_loss/balanced")
    partner_profile: dict | None = Field(default=None, description="伴侣档案")
    couple_plan_enabled: bool = Field(default=False, description="是否启用夫妻备孕双人计划")
```

- [ ] **Step 5: Save onboarding profile values**

In both the update and create branches for `UserProfile`, set:

```python
            profile.goal_priority = req.goal_priority
            profile.partner_profile = req.partner_profile or {}
            profile.couple_plan_enabled = req.couple_plan_enabled
```

For the create branch, include:

```python
                goal_priority=req.goal_priority,
                partner_profile=req.partner_profile or {},
                couple_plan_enabled=req.couple_plan_enabled,
```

- [ ] **Step 6: Syntax check**

Run:

```bash
cd meal-muse-api
python -m compileall app/models/user_profile.py app/schemas/user.py app/api/v1/users.py
```

Expected: all three files compile successfully.

## Task 2: Meal Schemas And API Generate Options

**Files:**
- Modify: `meal-muse-api/app/schemas/meal.py`
- Modify: `meal-muse-api/app/api/v1/meals.py`

- [ ] **Step 1: Add serving schema classes**

In `meal-muse-api/app/schemas/meal.py`, add after `FoodItem`:

```python
class ServingAdviceItem(BaseModel):
    label: str | None = None
    portion: str | None = None
    calories: int | None = None
    reason: str | None = None


class ServingAdvice(BaseModel):
    primary: ServingAdviceItem | None = None
    partner: ServingAdviceItem | None = None
```

- [ ] **Step 2: Extend MealDetail**

In `MealDetail`, add:

```python
    serving_advice: ServingAdvice | dict | None = None
    reason_tags: list[str] | None = None
    personalized_reason: str | None = None
```

- [ ] **Step 3: Extend generate request**

In `MealPlanGenerate`, add:

```python
    couple_plan_enabled: bool | None = None
    goal_priority: str | None = Field(default=None, max_length=30)
    meal_context: str | None = Field(default=None, max_length=100)
```

- [ ] **Step 4: Pass request options to engine**

In `meal-muse-api/app/api/v1/meals.py`, change:

```python
    plan = await generate_plan(db, current_user, plan_date)
```

to:

```python
    plan = await generate_plan(
        db,
        current_user,
        plan_date,
        couple_plan_enabled=req.couple_plan_enabled,
        goal_priority=req.goal_priority,
        meal_context=req.meal_context,
    )
```

- [ ] **Step 5: Syntax check**

Run:

```bash
cd meal-muse-api
python -m compileall app/schemas/meal.py app/api/v1/meals.py
```

Expected: both files compile successfully.

## Task 3: Context Builder Couple Summary

**Files:**
- Modify: `meal-muse-api/app/services/context_builder.py`

- [ ] **Step 1: Add helper functions near label constants**

Add:

```python
GOAL_PRIORITY_LABELS = {
    "pregnancy_safe": "备孕安全优先",
    "weight_loss": "体重管理优先",
    "balanced": "均衡兼顾",
}


def _format_partner_profile(partner: dict | None) -> str | None:
    if not partner:
        return None
    parts = []
    nickname = partner.get("nickname") or "伴侣"
    parts.append(nickname)
    if partner.get("age"):
        parts.append(f"{partner['age']}岁")
    if partner.get("height_cm") and partner.get("current_weight"):
        parts.append(f"{partner['height_cm']}cm/{partner['current_weight']}kg")
    if partner.get("taste_preference"):
        parts.append(f"口味{partner['taste_preference']}")
    if partner.get("cuisine_preference"):
        parts.append("偏好" + "、".join(partner["cuisine_preference"]))
    if partner.get("disliked_foods"):
        parts.append("忌" + "、".join(partner["disliked_foods"]))
    if partner.get("allergens"):
        parts.append("过敏" + "、".join(partner["allergens"]))
    if partner.get("diet_notes"):
        parts.append("注意" + "、".join(partner["diet_notes"]))
    return "，".join(parts)
```

- [ ] **Step 2: Include couple context in `get_user_context()`**

Inside the `if profile:` block, after sub-goals are appended, add:

```python
        if profile.goal_priority:
            info.append(f"目标优先级：{GOAL_PRIORITY_LABELS.get(profile.goal_priority, profile.goal_priority)}")
        if profile.couple_plan_enabled:
            partner_desc = _format_partner_profile(profile.partner_profile)
            if partner_desc:
                info.append(f"夫妻备孕双人计划：伴侣信息({partner_desc})")
                info.append("男方备孕营养重点：优质蛋白、锌、硒、Omega-3、抗氧化食物，减少酒精、高糖和油炸")
```

- [ ] **Step 3: Include couple context in `get_ai_prompt_context()`**

Inside `if profile:`, after disliked foods, add:

```python
        if profile.goal_priority:
            parts.append(f"目标优先级：{GOAL_PRIORITY_LABELS.get(profile.goal_priority, profile.goal_priority)}")
        if profile.couple_plan_enabled:
            partner_desc = _format_partner_profile(profile.partner_profile)
            if partner_desc:
                parts.append(f"伴侣：{partner_desc}")
```

- [ ] **Step 4: Include couple summary in `get_profile_summary()`**

After sub-goals are appended, add:

```python
    if profile.goal_priority:
        segs.append(GOAL_PRIORITY_LABELS.get(profile.goal_priority, profile.goal_priority))
    if profile.couple_plan_enabled:
        partner_desc = _format_partner_profile(profile.partner_profile)
        if partner_desc:
            segs.append(f"夫妻备孕，伴侣{partner_desc}")
```

- [ ] **Step 5: Syntax check**

Run:

```bash
cd meal-muse-api
python -m compileall app/services/context_builder.py
```

Expected: file compiles successfully.

## Task 4: Meal Plan Engine Couple Generation

**Files:**
- Modify: `meal-muse-api/app/services/meal_plan_engine.py`

- [ ] **Step 1: Extend system prompt JSON contract**

Update `MEAL_PLAN_SYSTEM` so each meal example includes:

```json
"serving_advice": {
  "primary": {"label": "女方", "portion": "具体份量", "calories": 数字, "reason": "推荐理由"},
  "partner": {"label": "男方", "portion": "具体份量", "calories": 数字, "reason": "推荐理由"}
},
"reason_tags": ["补铁", "高蛋白"],
"personalized_reason": "为什么推荐这餐"
```

Add rules:

```text
- 如果是夫妻备孕双人计划，生成同一桌饭，但必须给女方和男方分别给出份量和推荐理由
- 女方备孕重点：叶酸、铁、钙、DHA、蛋白质；如果减脂，只能温和控制热量
- 男方备孕重点：优质蛋白、锌、硒、Omega-3、抗氧化食物；减少酒精、高糖、油炸
- 不做医疗承诺，不声称治疗不孕不育
```

- [ ] **Step 2: Add helper functions before `_build_meal_prompt()`**

Add:

```python
GOAL_PRIORITY_LABELS = {
    "pregnancy_safe": "备孕安全优先",
    "weight_loss": "体重管理优先",
    "balanced": "均衡兼顾",
}


def _format_partner_context(profile: UserProfile | None) -> str | None:
    if not profile or not profile.couple_plan_enabled or not profile.partner_profile:
        return None
    partner = profile.partner_profile or {}
    parts = []
    nickname = partner.get("nickname") or "伴侣"
    parts.append(f"称呼：{nickname}")
    if partner.get("age"):
        parts.append(f"年龄：{partner['age']}岁")
    if partner.get("height_cm") and partner.get("current_weight"):
        parts.append(f"身高体重：{partner['height_cm']}cm/{partner['current_weight']}kg")
    if partner.get("daily_calorie_target"):
        parts.append(f"热量目标：{partner['daily_calorie_target']}kcal")
    if partner.get("taste_preference"):
        parts.append(f"口味：{partner['taste_preference']}")
    if partner.get("cuisine_preference"):
        parts.append("菜系偏好：" + "、".join(partner["cuisine_preference"]))
    if partner.get("disliked_foods"):
        parts.append("忌口：" + "、".join(partner["disliked_foods"]))
    if partner.get("allergens"):
        parts.append("过敏：" + "、".join(partner["allergens"]))
    if partner.get("diet_notes"):
        parts.append("饮食注意：" + "、".join(partner["diet_notes"]))
    return "；".join(parts)


def _get_goal_priority(profile: UserProfile | None, override: str | None = None) -> str:
    if override in GOAL_PRIORITY_LABELS:
        return override
    if profile and profile.goal_priority in GOAL_PRIORITY_LABELS:
        return profile.goal_priority
    return "pregnancy_safe"
```

- [ ] **Step 3: Extend `_build_meal_prompt()` signature**

Add parameters:

```python
    couple_plan_enabled: bool = False,
    partner_context: str | None = None,
    goal_priority: str = "pregnancy_safe",
    meal_context: str | None = None,
```

Before final output instruction, add:

```python
    prompt += f"\n\n目标优先级：{GOAL_PRIORITY_LABELS.get(goal_priority, goal_priority)}"
    if meal_context:
        prompt += f"\n\n本次特殊要求：{meal_context}"
    if couple_plan_enabled and partner_context:
        prompt += f"""

夫妻备孕双人计划：
- 伴侣信息：{partner_context}
- 请生成同一桌饭，不要为两个人生成完全不同菜单
- 每餐必须给出 serving_advice.primary 和 serving_advice.partner
- 女方份量兼顾备孕营养与温和体重管理
- 男方份量重点支持备孕营养：优质蛋白、锌、硒、Omega-3、抗氧化食物
- 双方忌口和过敏都必须规避
"""
```

- [ ] **Step 4: Extend `generate_plan()` signature and body**

Change signature:

```python
async def generate_plan(
    db: AsyncSession,
    user: User,
    plan_date: date,
    couple_plan_enabled: bool | None = None,
    goal_priority: str | None = None,
    meal_context: str | None = None,
) -> MealPlan:
```

After `profile = await _get_profile(...)`, compute:

```python
    effective_couple_plan_enabled = bool(
        couple_plan_enabled if couple_plan_enabled is not None
        else (profile.couple_plan_enabled if profile else False)
    )
    effective_goal_priority = _get_goal_priority(profile, goal_priority)
    partner_context = _format_partner_context(profile) if effective_couple_plan_enabled else None
```

Pass the new values into `_build_meal_prompt()`.

- [ ] **Step 5: Fix AI call to include prompt**

Change:

```python
        raw = await call_ai([], system_prompt=MEAL_PLAN_SYSTEM, temperature=0.7)
```

to:

```python
        raw = await call_ai(
            [{"role": "user", "content": prompt}],
            system_prompt=MEAL_PLAN_SYSTEM,
            temperature=0.7,
        )
```

- [ ] **Step 6: Save generation params**

When updating existing plan, set:

```python
        existing.generate_params = {
            "couple_plan_enabled": effective_couple_plan_enabled,
            "goal_priority": effective_goal_priority,
            "meal_context": meal_context,
            "recent_foods": recent_foods,
        }
```

When creating a new `MealPlan`, pass the same dict as `generate_params`.

- [ ] **Step 7: Enhance fallback meal details**

Add this helper:

```python
def _with_default_serving_advice(meal: dict, meal_type: str) -> dict:
    if meal.get("serving_advice"):
        return meal
    meal = dict(meal)
    calories = meal.get("total_calories", 0)
    meal["serving_advice"] = {
        "primary": {
            "label": "女方",
            "portion": "按推荐份量食用，主食保持半份到一份",
            "calories": int(calories * 0.45),
            "reason": "兼顾备孕营养和温和热量控制",
        },
        "partner": {
            "label": "男方",
            "portion": "蛋白质和主食可比女方增加约三分之一",
            "calories": int(calories * 0.60),
            "reason": "补充优质蛋白、锌和硒等备孕支持营养",
        },
    }
    meal["reason_tags"] = meal.get("reason_tags") or ["备孕友好", "高蛋白"]
    meal["personalized_reason"] = meal.get("personalized_reason") or "兜底方案优先选择高蛋白、少油、营养均衡的家常搭配。"
    return meal
```

In `_get_fallback_plan()`, before returning:

```python
    for meal_type in ["breakfast", "lunch", "dinner"]:
        plan[meal_type] = _with_default_serving_advice(plan[meal_type], meal_type)
```

In `_get_fallback_meal()`, return `_with_default_serving_advice(...)`.

- [ ] **Step 8: Syntax check**

Run:

```bash
cd meal-muse-api
python -m compileall app/services/meal_plan_engine.py
```

Expected: file compiles successfully.

## Task 5: Frontend Types And Onboarding Inputs

**Files:**
- Modify: `meal-muse-web/types/index.ts`
- Modify: `meal-muse-web/app/onboarding/page.tsx`

- [ ] **Step 1: Extend frontend types**

In `meal-muse-web/types/index.ts`, add:

```typescript
export interface PartnerProfile {
  nickname?: string;
  gender?: string;
  age?: number | null;
  height_cm?: number | null;
  current_weight?: number | null;
  activity_level?: string;
  taste_preference?: string;
  cuisine_preference?: string[];
  disliked_foods?: string[];
  allergens?: string[];
  diet_notes?: string[];
  daily_calorie_target?: number | null;
  macro_targets?: Record<string, number> | null;
}
```

Extend `UserProfile`:

```typescript
  constitution_types: string[] | null;
  health_sub_goals: string[] | null;
  preferred_ingredients: string[] | null;
  cooking_frequency: string;
  takeout_preference: string;
  family_cooking: boolean;
  family_members: Record<string, unknown>[] | null;
  onboarding_version: number;
  goal_priority: "pregnancy_safe" | "weight_loss" | "balanced";
  partner_profile: PartnerProfile | null;
  couple_plan_enabled: boolean;
```

- [ ] **Step 2: Add onboarding constants**

In `meal-muse-web/app/onboarding/page.tsx`, add near constants:

```typescript
const GOAL_PRIORITIES = [
  { key: "pregnancy_safe", label: "备孕安全优先", desc: "保证备孕关键营养，减脂只做温和控制" },
  { key: "weight_loss", label: "体重管理优先", desc: "控制热量，但不做激进节食" },
  { key: "balanced", label: "均衡兼顾", desc: "更重视长期饮食质量和稳定执行" },
];

const PARTNER_DIET_NOTES = ["少酒", "少油炸", "少高糖", "补锌", "高蛋白", "不吃辣"];
```

- [ ] **Step 3: Add onboarding state**

After goals state:

```typescript
  const [goalPriority, setGoalPriority] = useState<"pregnancy_safe" | "weight_loss" | "balanced">("pregnancy_safe");
```

Before family state:

```typescript
  const [couplePlanEnabled, setCouplePlanEnabled] = useState(false);
  const [partnerNickname, setPartnerNickname] = useState("");
  const [partnerAge, setPartnerAge] = useState("");
  const [partnerHeight, setPartnerHeight] = useState("");
  const [partnerWeight, setPartnerWeight] = useState("");
  const [partnerTastePreference, setPartnerTastePreference] = useState("mild");
  const [partnerDislikedFoods, setPartnerDislikedFoods] = useState("");
  const [partnerDietNotes, setPartnerDietNotes] = useState<string[]>([]);
```

- [ ] **Step 4: Add partner note toggle**

Add helper:

```typescript
  const togglePartnerDietNote = (note: string) => {
    setPartnerDietNotes((prev) =>
      prev.includes(note) ? prev.filter((item) => item !== note) : [...prev, note]
    );
  };
```

- [ ] **Step 5: Insert goal priority UI in Step 2**

After the goals list, add a block visible when `goals.includes("fertility") || goals.includes("pregnancy")`:

```tsx
            {(goals.includes("fertility") || goals.includes("pregnancy")) && (
              <div>
                <label className="block text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                  备孕与体重目标优先级
                </label>
                <div className="space-y-2">
                  {GOAL_PRIORITIES.map((item) => {
                    const selected = goalPriority === item.key;
                    return (
                      <button
                        key={item.key}
                        onClick={() => setGoalPriority(item.key as "pregnancy_safe" | "weight_loss" | "balanced")}
                        className="w-full p-3 rounded-xl text-left transition-colors"
                        style={{
                          background: selected ? "var(--primary)" : "var(--bg-subtle)",
                          color: selected ? "#fff" : "var(--text-primary)",
                          border: `1px solid ${selected ? "var(--primary)" : "var(--border-default)"}`,
                        }}
                      >
                        <span className="block text-sm font-semibold">{item.label}</span>
                        <span className="block text-xs mt-1" style={{ color: selected ? "rgba(255,255,255,0.8)" : "var(--text-secondary)" }}>
                          {item.desc}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
```

- [ ] **Step 6: Replace Step 6 family heading with couple-first UI**

At the start of Step 6 content, add a couple card before the existing family controls:

```tsx
            <div
              className="p-4 rounded-xl space-y-3"
              style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-default)" }}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    夫妻备孕双人计划
                  </h3>
                  <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                    同一桌饭，给两个人分别建议份量和营养重点。
                  </p>
                </div>
                <button
                  onClick={() => setCouplePlanEnabled((v) => !v)}
                  className="px-3 py-1.5 rounded-full text-xs font-medium"
                  style={{
                    background: couplePlanEnabled ? "var(--primary)" : "var(--bg-card)",
                    color: couplePlanEnabled ? "#fff" : "var(--text-secondary)",
                    border: `1px solid ${couplePlanEnabled ? "var(--primary)" : "var(--border-default)"}`,
                  }}
                >
                  {couplePlanEnabled ? "已开启" : "开启"}
                </button>
              </div>

              {couplePlanEnabled && (
                <div className="space-y-3">
                  <input className="w-full px-3 py-2.5 rounded-xl text-sm outline-none" value={partnerNickname} onChange={(e) => setPartnerNickname(e.target.value)} placeholder="伴侣称呼，如 老公" style={{ background: "var(--bg-card)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }} />
                  <div className="grid grid-cols-3 gap-2">
                    <input type="number" className="w-full px-3 py-2.5 rounded-xl text-sm outline-none" value={partnerAge} onChange={(e) => setPartnerAge(e.target.value)} placeholder="年龄" style={{ background: "var(--bg-card)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }} />
                    <input type="number" className="w-full px-3 py-2.5 rounded-xl text-sm outline-none" value={partnerHeight} onChange={(e) => setPartnerHeight(e.target.value)} placeholder="身高" style={{ background: "var(--bg-card)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }} />
                    <input type="number" className="w-full px-3 py-2.5 rounded-xl text-sm outline-none" value={partnerWeight} onChange={(e) => setPartnerWeight(e.target.value)} placeholder="体重" style={{ background: "var(--bg-card)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }} />
                  </div>
                  <input className="w-full px-3 py-2.5 rounded-xl text-sm outline-none" value={partnerDislikedFoods} onChange={(e) => setPartnerDislikedFoods(e.target.value)} placeholder="伴侣忌口，如 香菜、动物内脏" style={{ background: "var(--bg-card)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }} />
                  <div className="flex flex-wrap gap-2">
                    {PARTNER_DIET_NOTES.map((note) => {
                      const selected = partnerDietNotes.includes(note);
                      return (
                        <button
                          key={note}
                          onClick={() => togglePartnerDietNote(note)}
                          className="px-3 py-1.5 rounded-full text-xs transition-colors"
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
              )}
            </div>
```

- [ ] **Step 7: Include fields in submit body**

In the onboarding submit JSON, add:

```typescript
          goal_priority: goalPriority,
          couple_plan_enabled: couplePlanEnabled,
          partner_profile: couplePlanEnabled
            ? {
                nickname: partnerNickname || "伴侣",
                gender: "male",
                age: partnerAge ? Number(partnerAge) : null,
                height_cm: partnerHeight ? Number(partnerHeight) : null,
                current_weight: partnerWeight ? Number(partnerWeight) : null,
                taste_preference: partnerTastePreference,
                disliked_foods: partnerDislikedFoods ? partnerDislikedFoods.split(/[,，、\s]+/).filter(Boolean) : [],
                diet_notes: partnerDietNotes,
              }
            : null,
```

- [ ] **Step 8: Frontend lint/type check**

Run:

```bash
cd meal-muse-web
npm run lint
```

Expected: no new lint errors from onboarding/types changes.

## Task 6: Plan Page Couple Rendering

**Files:**
- Modify: `meal-muse-web/app/(main)/plan/page.tsx`

- [ ] **Step 1: Extend local interfaces**

Add:

```typescript
interface ServingAdviceItem {
  label?: string;
  portion?: string;
  calories?: number;
  reason?: string;
}

interface ServingAdvice {
  primary?: ServingAdviceItem;
  partner?: ServingAdviceItem;
}
```

Extend `MealDetail`:

```typescript
  serving_advice?: ServingAdvice | null;
  reason_tags?: string[] | null;
  personalized_reason?: string | null;
```

Extend `MealPlan`:

```typescript
  generate_params?: {
    couple_plan_enabled?: boolean;
    goal_priority?: string;
    meal_context?: string | null;
    recent_foods?: string[];
  } | null;
```

- [ ] **Step 2: Replace alerts with toast**

Import:

```typescript
import { toast } from "@/components/ui/toast";
```

Change `alert("生成失败")`, `alert("替换失败")`, and adoption alerts to `toast("error", "...")` or `toast("success", "...")`.

- [ ] **Step 3: Add couple state check**

Inside component before return:

```typescript
  const isCouplePlan = Boolean(plan?.generate_params?.couple_plan_enabled);
```

- [ ] **Step 4: Update page title and summary**

Change header title to:

```tsx
<h1 className="text-lg font-bold text-gray-900">
  {isCouplePlan ? "夫妻今日怎么吃" : "餐食计划"}
</h1>
```

Inside summary card, add chips:

```tsx
              {isCouplePlan && (
                <div className="flex flex-wrap gap-2 mt-3">
                  <span className="text-xs px-2 py-1 rounded-full bg-white text-green-700">共同目标：备孕</span>
                  <span className="text-xs px-2 py-1 rounded-full bg-white text-green-700">同一桌饭，份量分配</span>
                </div>
              )}
```

- [ ] **Step 5: Render serving advice for each meal**

After nutrient row, add:

```tsx
                      {meal.serving_advice && (
                        <div className="grid gap-2 pt-2 border-t border-gray-50">
                          {meal.serving_advice.primary && (
                            <div className="rounded-lg bg-green-50 px-3 py-2">
                              <div className="text-xs font-medium text-green-800">
                                {meal.serving_advice.primary.label || "女方"}：{meal.serving_advice.primary.portion}
                              </div>
                              {meal.serving_advice.primary.reason && (
                                <div className="text-xs text-green-700 mt-1">{meal.serving_advice.primary.reason}</div>
                              )}
                            </div>
                          )}
                          {meal.serving_advice.partner && (
                            <div className="rounded-lg bg-blue-50 px-3 py-2">
                              <div className="text-xs font-medium text-blue-800">
                                {meal.serving_advice.partner.label || "男方"}：{meal.serving_advice.partner.portion}
                              </div>
                              {meal.serving_advice.partner.reason && (
                                <div className="text-xs text-blue-700 mt-1">{meal.serving_advice.partner.reason}</div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
```

- [ ] **Step 6: Render reason tags and personalized reason**

After serving advice, add:

```tsx
                      {(meal.reason_tags?.length || meal.personalized_reason) && (
                        <div className="pt-2">
                          {meal.reason_tags?.length ? (
                            <div className="flex flex-wrap gap-1 mb-2">
                              {meal.reason_tags.map((tag) => (
                                <span key={tag} className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          ) : null}
                          {meal.personalized_reason && (
                            <p className="text-xs leading-relaxed text-gray-500">{meal.personalized_reason}</p>
                          )}
                        </div>
                      )}
```

- [ ] **Step 7: Frontend lint/type check**

Run:

```bash
cd meal-muse-web
npm run lint
```

Expected: no new lint errors from plan page changes.

## Task 7: Verification And Final Commit

**Files:**
- Verify all touched files.

- [ ] **Step 1: Run backend syntax checks**

Run:

```bash
cd meal-muse-api
python -m compileall app
```

Expected: compile completes without syntax errors.

- [ ] **Step 2: Run frontend lint**

Run:

```bash
cd meal-muse-web
npm run lint
```

Expected: lint exits successfully or only reports pre-existing unrelated issues.

- [ ] **Step 3: Inspect git diff**

Run:

```bash
git diff -- meal-muse-api/app/models/user_profile.py meal-muse-api/app/schemas/user.py meal-muse-api/app/schemas/meal.py meal-muse-api/app/api/v1/users.py meal-muse-api/app/api/v1/meals.py meal-muse-api/app/services/context_builder.py meal-muse-api/app/services/meal_plan_engine.py meal-muse-web/types/index.ts meal-muse-web/app/onboarding/page.tsx meal-muse-web/app/(main)/plan/page.tsx
```

Expected: diff only contains couple meal-plan changes.

- [ ] **Step 4: Commit implementation**

Run:

```bash
git add meal-muse-api/app/models/user_profile.py meal-muse-api/app/schemas/user.py meal-muse-api/app/schemas/meal.py meal-muse-api/app/api/v1/users.py meal-muse-api/app/api/v1/meals.py meal-muse-api/app/services/context_builder.py meal-muse-api/app/services/meal_plan_engine.py meal-muse-web/types/index.ts meal-muse-web/app/onboarding/page.tsx meal-muse-web/app/(main)/plan/page.tsx docs/superpowers/plans/2026-06-19-couple-preconception-meal-plan-implementation.md
git commit -m "feat: 支持夫妻备孕双人餐食计划"
```

Expected: commit succeeds.

## Self-Review

- Spec coverage: The plan covers profile fields, onboarding, partner profile, couple prompt context, meal response structure, plan-page rendering, safety-oriented prompt rules, and verification.
- Scope control: Full household collaboration, shopping lists, and partner independent login are deliberately excluded.
- Type consistency: Backend uses `goal_priority`, `partner_profile`, and `couple_plan_enabled`; frontend uses the same names in onboarding payload, profile types, and plan generation params.
