# 夫妻备孕双人餐食计划设计

> 日期：2026-06-19  
> 状态：待用户审阅  
> 范围：MealMuse 首版餐食计划优化，聚焦“夫妻备孕 + 温和减脂 + AI 每日推荐”

## 1. 背景

MealMuse 当前已经具备用户画像、饮食记录、经期追踪、家庭共享、AI 对话、餐食计划等基础模块，但项目尚未实际运行。现阶段最重要的不是继续扩展更多功能，而是把核心推荐闭环做准：

1. 用户输入身体数据、健康目标、偏好和忌口。
2. AI 基于目标和历史饮食生成每日餐食。
3. 用户采纳、替换、记录实际饮食。
4. 后续推荐根据记录结果持续优化。

用户明确提出产品目的主要是备孕、减肥，并支持多人共用。经讨论后确认：备孕不是单人目标，应优先支持夫妻共同备孕，而不是只为女性生成个人餐食；但首版也不宜直接做完整家庭协同。推荐方向是先做“夫妻备孕双人餐食计划”，后续再扩展为完整家庭餐桌。

## 2. 产品定位

首版优化后的核心定位：

**MealMuse 是夫妻备孕期的 AI 饮食助手，同时支持女方温和减脂和双方营养优化。**

这意味着首版餐食计划不再只是“给一个用户生成三餐”，而是：

- 生成一桌可共同食用的餐食，降低做饭成本。
- 为女方和男方分别计算营养目标与份量。
- 对女方兼顾备孕营养、经期/排卵期阶段和温和减脂。
- 对男方补充备孕相关营养建议，如锌、硒、优质脂肪、抗氧化食物和蛋白质。
- 双方过敏、忌口、口味偏好都进入 AI 推荐约束。
- 历史饮食先以主账号记录为主，保留扩展到双方分别记录的模型空间。

## 3. 首版边界

### 3.1 本次做

- 新增伴侣档案，作为主账号的轻量共同目标成员。
- Onboarding 支持选择目标优先级：
  - `pregnancy_safe`：备孕安全优先，默认。
  - `weight_loss`：体重管理优先，但禁止激进节食。
  - `balanced`：均衡兼顾。
- 餐食计划支持夫妻双人上下文。
- AI 返回同一桌菜、双方份量、双方推荐理由。
- 计划页展示“今日双人重点”“一桌菜”“份量分配”“为什么推荐”。
- 家庭共享保留现有功能，但不作为本轮主线。

### 3.2 本次不做

- 不做完整家庭成员独立账号协同计划。
- 不做家庭购物清单。
- 不做复杂权限流或多人共同编辑计划。
- 不做医疗诊断、用药建议、生育治疗建议。
- 不要求男方在首版必须独立登录；可以先由主账号维护伴侣档案。

## 4. 用户体验

### 4.1 Onboarding 流程

建议把现有专业版 onboarding 调整为 6 步：

1. 主账号基础信息：身高、体重、年龄、性别、活动量。
2. 目标选择：备孕、减脂、养生、增肌等，可多选。
3. 目标优先级：备孕安全优先、体重管理优先、均衡兼顾。
4. 饮食偏好：口味、菜系、饮食类型、过敏、忌口、不喜欢食物。
5. 备孕信息：经期信息、备孕阶段、重点关注营养。
6. 伴侣档案：昵称、性别、身高体重、活动量、口味偏好、忌口、是否一起吃饭。

如果用户跳过伴侣档案，系统仍可生成单人计划，但在备孕目标下提示“添加伴侣后可生成夫妻双人备孕餐”。

### 4.2 计划页移动端结构

计划页首屏推荐结构：

1. 顶部标题：`夫妻今日怎么吃` 或 `今天怎么吃`。
2. 状态标签：
   - 共同目标：备孕。
   - 女方：温和减脂 / 备孕安全优先。
   - 男方：备孕营养支持。
3. 今日双人重点：
   - 女方：叶酸、铁、钙、DHA、蛋白质、热量目标。
   - 男方：锌、硒、优质脂肪、抗氧化、蛋白质、热量目标。
4. 三餐一桌菜：
   - 早餐、午餐、晚餐。
   - 每餐显示共享菜品。
   - 每餐显示女方份量、男方份量。
5. 推荐理由：
   - 为什么适合女方。
   - 为什么适合男方。
   - 避开了哪些忌口或近期重复食物。
6. 操作：
   - 采纳全部为今日记录。
   - 换一餐。
   - 不喜欢这个食材。
   - 今天不和伴侣一起吃。

## 5. 数据设计

### 5.1 UserProfile 新增字段

当前 `user_profiles` 已有 `family_cooking`、`family_members` 等字段。为了让夫妻备孕语义更清晰，建议新增专门字段，而不是把伴侣长期塞在 `family_members` 里。

```python
goal_priority: str = "pregnancy_safe"
partner_profile: dict | None = None
couple_plan_enabled: bool = False
```

`goal_priority` 枚举：

```json
{
  "pregnancy_safe": "备孕安全优先",
  "weight_loss": "体重管理优先",
  "balanced": "均衡兼顾"
}
```

`partner_profile` 建议结构：

```json
{
  "nickname": "老公",
  "gender": "male",
  "age": 30,
  "height_cm": 175,
  "current_weight": 72,
  "activity_level": "moderate",
  "taste_preference": "mild",
  "cuisine_preference": ["粤菜", "家常菜"],
  "disliked_foods": ["香菜"],
  "allergens": [],
  "diet_notes": ["少酒", "少油炸"],
  "daily_calorie_target": 2200,
  "macro_targets": {
    "protein_g": 100,
    "fat_g": 70,
    "carbs_g": 260
  }
}
```

### 5.2 MealPlan 返回结构增强

当前 `MealPlan` 已有 `breakfast`、`lunch`、`dinner` JSONB 字段。为降低迁移成本，首版可以继续用 JSONB 承载增强结构。

单餐结构建议：

```json
{
  "name": "番茄牛肉豆腐煲套餐",
  "foods": [
    {
      "name": "番茄牛肉豆腐煲",
      "amount": "1锅",
      "calories": 520,
      "protein": 42,
      "fat": 22,
      "carbs": 32
    }
  ],
  "serving_advice": {
    "primary": {
      "label": "女方",
      "portion": "牛肉豆腐煲 1 小碗，糙米饭半碗",
      "calories": 520,
      "reason": "补铁、蛋白质和叶酸，主食半碗保持温和热量缺口"
    },
    "partner": {
      "label": "男方",
      "portion": "牛肉豆腐煲 1.5 碗，糙米饭 1 碗，加核桃 2 颗",
      "calories": 760,
      "reason": "增加蛋白质、锌和优质脂肪，支持备孕期营养"
    }
  },
  "total_calories": 1280,
  "total_protein": 88,
  "total_fat": 42,
  "total_carbs": 145,
  "reason_tags": ["补铁", "高蛋白", "备孕友好", "温和减脂"],
  "personalized_reason": "这餐兼顾女方补铁和男方蛋白质需求，并避开双方不喜欢的香菜。"
}
```

`total_calories` 保持表示整餐共享菜总热量估算。个人摄入以 `serving_advice.primary.calories` 和 `serving_advice.partner.calories` 为准。

### 5.3 未来可迁移结构

如果夫妻计划稳定后，再新增结构化表：

- `household_profiles`
- `household_members`
- `meal_plan_participants`
- `meal_serving_allocations`

首版暂不做这些表，避免早期过度设计。

## 6. AI 推荐策略

### 6.1 上下文输入

餐食计划生成必须注入：

- 主账号基础信息。
- 主账号健康目标。
- 主账号目标优先级。
- 主账号饮食偏好、忌口、过敏。
- 伴侣档案和伴侣忌口。
- 经期/排卵期阶段。
- 近 3 天食物去重。
- 近 7 天营养摄入短板。
- 厨房条件、备餐时间、预算。

当前代码中 `meal_plan_engine.generate_plan()` 已经构建了 `prompt`，但 AI 调用没有把 `prompt` 作为 user message 传给 `call_ai()`。实施时必须先修复这个问题，否则画像和历史饮食不会真正影响生成结果。

### 6.2 目标优先级规则

`pregnancy_safe`：

- 禁止激进热量缺口。
- 女方每日热量不低于基础安全阈值。
- 优先保证蛋白质、叶酸、铁、钙、DHA。
- 不推荐极端低碳、生酮、代餐式节食。

`weight_loss`：

- 允许温和热量缺口。
- 仍需满足备孕关键营养素下限。
- 如果营养下限和热量缺口冲突，以营养下限优先。

`balanced`：

- 采用较小热量缺口。
- 优先做饮食质量优化，如少油、少糖、增加蔬菜和优质蛋白。

男方备孕营养建议：

- 增加优质蛋白、锌、硒、Omega-3、维生素 C/E 等抗氧化来源。
- 减少酒精、高糖、高油炸、过量加工肉类。
- 不表达治疗承诺，只提供饮食支持建议。

### 6.3 AI 输出要求

AI 必须返回严格 JSON，并包含：

- 三餐内容。
- 每餐共享食物列表。
- 每餐双方份量建议。
- 每餐双方推荐理由。
- 全天双方热量估算。
- 忌口和近期重复规避说明。
- `ai_note`：1-2 句总体说明。

## 7. 后端改动

### 7.1 模型层

文件：[meal-muse-api/app/models/user_profile.py](/Users/xiaoyuer/projects/meal_muse/meal-muse-api/app/models/user_profile.py)

新增字段：

- `goal_priority`
- `partner_profile`
- `couple_plan_enabled`

### 7.2 Schema 层

文件：[meal-muse-api/app/schemas/user.py](/Users/xiaoyuer/projects/meal_muse/meal-muse-api/app/schemas/user.py)

新增：

- `PartnerProfile`
- `UserProfileUpdate.goal_priority`
- `UserProfileUpdate.partner_profile`
- `UserProfileUpdate.couple_plan_enabled`
- `UserProfileResponse` 对应字段

文件：[meal-muse-api/app/schemas/meal.py](/Users/xiaoyuer/projects/meal_muse/meal-muse-api/app/schemas/meal.py)

增强：

- `MealDetail.serving_advice`
- `MealDetail.reason_tags`
- `MealDetail.personalized_reason`

### 7.3 Service 层

文件：[meal-muse-api/app/services/context_builder.py](/Users/xiaoyuer/projects/meal_muse/meal-muse-api/app/services/context_builder.py)

新增或增强：

- `get_profile_summary()` 输出目标优先级和伴侣摘要。
- `get_ai_prompt_context()` 增加伴侣忌口和夫妻备孕目标。

文件：[meal-muse-api/app/services/meal_plan_engine.py](/Users/xiaoyuer/projects/meal_muse/meal-muse-api/app/services/meal_plan_engine.py)

改动：

- 修复 `call_ai()` 未传入生成 prompt 的问题。
- `_build_meal_prompt()` 增加夫妻备孕规则。
- 新增 `_get_partner_context(profile)`。
- 新增 `_get_goal_priority(profile)`。
- 增强 fallback plan，至少提供女方/男方份量说明。
- 保存 `generate_params`，记录本次使用的目标优先级、是否夫妻计划、近期去重食物。

### 7.4 API 层

文件：[meal-muse-api/app/api/v1/users.py](/Users/xiaoyuer/projects/meal_muse/meal-muse-api/app/api/v1/users.py)

改动：

- 完整画像更新支持伴侣档案。
- 更新画像后清理 `profile_summary:{user_id}` 缓存。

文件：[meal-muse-api/app/api/v1/meals.py](/Users/xiaoyuer/projects/meal_muse/meal-muse-api/app/api/v1/meals.py)

改动：

- `POST /meals/generate` 支持可选参数：
  - `couple_plan_enabled`
  - `goal_priority`
  - `meal_context`，如“今天不和伴侣一起吃”。
- `POST /meals/{plan_id}/replace` 替换单餐时保留夫妻上下文。

## 8. 前端改动

### 8.1 Onboarding

文件：[meal-muse-web/app/onboarding/page.tsx](/Users/xiaoyuer/projects/meal_muse/meal-muse-web/app/onboarding/page.tsx)

新增：

- 目标优先级选择。
- 伴侣档案步骤。
- 跳过伴侣档案入口。
- 备孕目标下提示伴侣档案价值。

### 8.2 计划页

文件：[meal-muse-web/app/(main)/plan/page.tsx](/Users/xiaoyuer/projects/meal_muse/meal-muse-web/app/(main)/plan/page.tsx)

改动：

- 页面标题根据是否夫妻计划切换：
  - `夫妻今日怎么吃`
  - `今天怎么吃`
- 增加“今日双人重点”模块。
- 每餐展示双方份量。
- 展示 `reason_tags` 和 `personalized_reason`。
- 替换 `alert()` 为现有 `toast()`。
- 后续可加“今天不和伴侣一起吃”开关。

## 9. 安全与合规边界

- 不声称能提高怀孕概率或治疗不孕不育。
- 不替代医生、营养师或生殖医学建议。
- 对备孕、孕期、慢病、过敏等场景，输出应以“饮食支持建议”为边界。
- 对极端减肥、过低热量、断食、药物、补剂过量建议要拒绝或降级为安全建议。
- 对男方备孕建议避免医学承诺，只表达营养支持方向。

## 10. 测试策略

### 10.1 后端单元测试

重点覆盖：

- `goal_priority` 默认值为 `pregnancy_safe`。
- 伴侣档案能进入 prompt。
- 双方忌口都能进入 prompt。
- 近 3 天食物能进入去重提示。
- AI 返回增强 JSON 后能解析并保存。
- fallback plan 包含双方份量建议。

### 10.2 API 测试

重点覆盖：

- 更新完整画像时可写入伴侣档案。
- 生成计划时返回增强结构。
- 替换单餐时保留 `serving_advice`。
- 未填写伴侣档案时仍可生成单人计划。

### 10.3 前端验证

重点覆盖：

- 移动端计划页文本不溢出。
- 单人计划和夫妻计划都能正常渲染。
- 空状态能引导补充伴侣档案。
- 采纳、换一餐、生成中、失败状态都有反馈。

## 11. 实施顺序

1. 修复餐食计划 prompt 未传入 AI 的问题。
2. 增加后端 schema/model 字段和画像更新能力。
3. 增强 context builder 和 meal plan prompt。
4. 增强 AI 返回解析和 fallback plan。
5. 更新计划页渲染双人份量和推荐理由。
6. 更新 onboarding 伴侣档案步骤。
7. 补测试与基础移动端验证。

## 12. 成功标准

- 用户能选择“备孕安全优先 / 体重管理优先 / 均衡兼顾”。
- 用户能录入伴侣档案。
- 备孕目标下能生成夫妻双人餐食计划。
- 每餐能显示同一桌菜和双方份量。
- 推荐理由能解释女方和男方各自营养目的。
- 近期饮食会影响推荐去重。
- 未填写伴侣档案时系统仍能生成单人计划，不阻断使用。
