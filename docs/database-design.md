# MealMuse 数据库详细设计

> 版本：v1.1 | 更新日期：2026-06-07 | 新增：生理期追踪、家庭账户、身体数据、水果数据库

---

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| **UUID 主键** | 所有表使用 UUID v4 作为主键，避免自增 ID 暴露业务量 |
| **软删除** | 核心表使用 `deleted_at` 字段实现软删除 |
| **时间戳** | 所有表包含 `created_at` / `updated_at` |
| **JSONB 灵活字段** | 营养数据、偏好设置等使用 JSONB，兼顾结构化和灵活性 |
| **外键约束** | 严格外键约束保证数据一致性 |
| **索引策略** | 高频查询字段建立索引，避免过度索引 |

---

## 2. ER 关系图

```
                          ┌──────────────┐
                          │  food_items  │
                          │  (食物数据库) │
                          └──────┬───────┘
                                 │ 1:N
                                 ▼
┌──────────────┐  1:N   ┌──────────────────┐  N:1   ┌──────────────┐
│   users      │◀──────▶│   diet_records   │◀──────▶│  meal_plans  │
│  (用户表)     │        │  (饮食记录表)     │        │ (餐食计划表)  │
└──────┬───────┘        └──────────────────┘        └──────────────┘
       │                                                      
       │ 1:N                                                  
       ▼                                                      
┌──────────────┐        ┌──────────────────┐                  
│ health_goals │        │    ai_chats      │                  
│ (健康目标表)  │        │  (AI 对话表)     │                  
└──────────────┘        └──────────────────┘                  
       ▲                       ▲                              
       │ N:1                   │ N:1                          
       └───────────────────────┘                              
              users ◀────────────────────────┘                
```

---

## 3. 详细表结构

### 3.1 `users` — 用户表

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           VARCHAR(20) UNIQUE,
    wechat_openid   VARCHAR(128) UNIQUE,
    nickname        VARCHAR(50) NOT NULL,
    avatar_url      VARCHAR(512),
    gender          VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    birthday        DATE,
    height_cm       DECIMAL(5,1),            -- 身高 cm
    current_weight  DECIMAL(5,1),            -- 当前体重 kg
    target_weight   DECIMAL(5,1),            -- 目标体重 kg
    activity_level  VARCHAR(20) DEFAULT 'moderate'
                    CHECK (activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active')),
    preferences     JSONB DEFAULT '{}',      -- 饮食偏好
    -- preferences 结构：
    -- {
    --   "taste": ["清淡", "微辣"],         -- 口味偏好
    --   "allergens": ["海鲜", "花生"],     -- 过敏原
    --   "dislikes": ["香菜", "苦瓜"],      -- 不喜欢的食物
    --   "diet_type": "normal",             -- 饮食类型: normal/vegetarian/vegan/keto
    --   "cuisine_pref": ["川菜", "粤菜"]   -- 菜系偏好
    -- }
    daily_calorie_target INT,                -- 每日热量目标 kcal（AI 计算后写入）
    status          VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive', 'banned')),
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ              -- 软删除
);

-- 索引
CREATE INDEX idx_users_phone ON users(phone) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_wechat ON users(wechat_openid) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_status ON users(status) WHERE deleted_at IS NULL;

-- 自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | UUID | ✅ | 主键，自动生成 |
| phone | VARCHAR(20) | ❌ | 手机号，与 wechat_openid 至少一个 |
| wechat_openid | VARCHAR(128) | ❌ | 微信 OpenID |
| nickname | VARCHAR(50) | ✅ | 昵称，默认生成 |
| avatar_url | VARCHAR(512) | ❌ | 头像 URL |
| gender | VARCHAR(10) | ❌ | 性别 |
| birthday | DATE | ❌ | 生日，用于计算年龄 |
| height_cm | DECIMAL(5,1) | ❌ | 身高 cm |
| current_weight | DECIMAL(5,1) | ❌ | 当前体重 kg |
| target_weight | DECIMAL(5,1) | ❌ | 目标体重 kg |
| activity_level | VARCHAR(20) | ❌ | 活动量等级 |
| preferences | JSONB | ❌ | 饮食偏好（JSON） |
| daily_calorie_target | INT | ❌ | 每日热量目标 |
| status | VARCHAR(20) | ✅ | 账户状态 |
| last_login_at | TIMESTAMPTZ | ❌ | 最后登录时间 |

---

### 3.2 `health_goals` — 健康目标表

```sql
CREATE TABLE health_goals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_type       VARCHAR(20) NOT NULL
                    CHECK (goal_type IN ('weight_loss', 'pregnancy', 'health', 'muscle_gain', 'custom')),
    target_weight   DECIMAL(5,1),            -- 目标体重 kg
    target_date     DATE,                    -- 目标日期
    weekly_loss_rate DECIMAL(3,1),           -- 每周减重速率 kg（仅减肥）
    daily_calorie_target INT,                -- 计算出的每日热量目标
    macro_targets   JSONB,                   -- 宏量营养素目标
    -- macro_targets 结构：
    -- {
    --   "protein_g": 80,       -- 蛋白质 g
    --   "fat_g": 55,           -- 脂肪 g
    --   "carbs_g": 200,        -- 碳水 g
    --   "fiber_g": 25,         -- 膳食纤维 g
    --   "protein_ratio": 0.20, -- 蛋白质占比
    --   "fat_ratio": 0.30,     -- 脂肪占比
    --   "carbs_ratio": 0.50    -- 碳水占比
    -- }
    special_notes   TEXT,                    -- 特殊说明（如：备孕需补叶酸）
    status          VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active', 'paused', 'completed', 'abandoned')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_health_goals_user ON health_goals(user_id) WHERE status = 'active';
```

**goal_type 枚举说明：**

| 值 | 含义 | 特殊逻辑 |
|----|------|----------|
| weight_loss | 减脂减重 | 需计算热量缺口，关注每周减重速率 |
| pregnancy | 备孕调理 | 关注叶酸/铁/钙等营养素，避免寒凉食物 |
| health | 养生保健 | 根据体质推荐食疗，关注节气饮食 |
| muscle_gain | 增肌塑形 | 高蛋白目标，配合训练日/休息日不同方案 |
| custom | 自定义 | 用户自行设定目标 |

---

### 3.3 `food_items` — 食物数据库表（预置）

```sql
CREATE TABLE food_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,       -- 食物名称
    name_en         VARCHAR(100),                -- 英文名
    category        VARCHAR(50) NOT NULL,        -- 分类
    -- category: 谷物/蔬菜/水果/肉蛋/水产/豆制品/乳制品/坚果/调味品/饮品/零食/熟食
    subcategory     VARCHAR(50),                 -- 子分类
    per_amount      VARCHAR(20) NOT NULL,        -- 标准份量 "100g" / "1个" / "1碗"
    per_grams       DECIMAL(8,2),                -- 标准份量克数
    calories        INT NOT NULL,                -- 热量 kcal
    protein         DECIMAL(6,2),                -- 蛋白质 g
    fat             DECIMAL(6,2),                -- 脂肪 g
    carbs           DECIMAL(6,2),                -- 碳水化合物 g
    fiber           DECIMAL(6,2),                -- 膳食纤维 g
    vitamin_a       DECIMAL(8,2),                -- 维生素 A μg
    vitamin_c       DECIMAL(8,2),                -- 维生素 C mg
    vitamin_d       DECIMAL(8,2),                -- 维生素 D μg
    calcium         DECIMAL(8,2),                -- 钙 mg
    iron            DECIMAL(8,2),                -- 铁 mg
    zinc            DECIMAL(8,2),                -- 锌 mg
    folate          DECIMAL(8,2),                -- 叶酸 μg（备孕关键）
    sodium          DECIMAL(8,2),                -- 钠 mg
    glycemic_index  INT,                         -- 升糖指数 GI
    tags            TEXT[] DEFAULT '{}',          -- 标签 ["高蛋白", "低GI", "补铁", "寒凉"]
    season          TEXT[] DEFAULT '{}',          -- 应季月份 [1,2,3,...,12]
    is_common       BOOLEAN DEFAULT true,         -- 是否常见食材
    image_url       VARCHAR(512),                -- 图片
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_food_items_name ON food_items USING gin(to_tsvector('simple', name));
CREATE INDEX idx_food_items_category ON food_items(category);
CREATE INDEX idx_food_items_tags ON food_items USING gin(tags);
CREATE INDEX idx_food_items_common ON food_items(is_common) WHERE is_common = true;
```

**预置数据示例：**

```sql
INSERT INTO food_items (name, category, per_amount, per_grams, calories, protein, fat, carbs, fiber, iron, folate, tags) VALUES
('鸡胸肉',   '肉蛋',   '100g',  100, 133, 31.0, 1.2, 0,   0,   0.7,  0,   '{"高蛋白","低脂","增肌"}'),
('西兰花',   '蔬菜',   '100g',  100, 34,  4.3,  0.4, 4.3, 2.6, 1.0,  63,  '{"高纤维","补铁","备孕推荐"}'),
('糙米饭',   '谷物',   '1碗',   200, 220, 4.8,  1.8, 44,  3.2, 0.8,  0,   '{"低GI","高纤维"}'),
('三文鱼',   '水产',   '100g',  100, 208, 20,   13,  0,   0,   0.3,  0,   '{"高蛋白","Omega3","备孕推荐"}'),
('菠菜',     '蔬菜',   '100g',  100, 28,  2.9,  0.4, 3.6, 2.2, 2.7,  194, '{"补铁","补叶酸","备孕推荐","寒凉"}');
```

---

### 3.4 `diet_records` — 饮食记录表

```sql
CREATE TABLE diet_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_type       VARCHAR(20) NOT NULL
                    CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    food_text       TEXT NOT NULL,                -- 用户原始输入
    parsed_foods    JSONB NOT NULL,               -- AI 解析结果
    -- parsed_foods 结构：
    -- [
    --   {
    --     "food_item_id": "uuid",               -- 关联食物库（可选）
    --     "name": "红烧牛肉面",
    --     "amount": "1碗",
    --     "grams": 400,
    --     "calories": 520,
    --     "protein": 25,
    --     "fat": 18,
    --     "carbs": 62,
    --     "fiber": 2.1
    --   }
    -- ]
    total_calories  INT NOT NULL DEFAULT 0,       -- 总热量 kcal
    total_protein   DECIMAL(8,2) DEFAULT 0,       -- 总蛋白质 g
    total_fat       DECIMAL(8,2) DEFAULT 0,       -- 总脂肪 g
    total_carbs     DECIMAL(8,2) DEFAULT 0,       -- 总碳水 g
    total_fiber     DECIMAL(8,2) DEFAULT 0,       -- 总膳食纤维 g
    ai_analysis     TEXT,                         -- AI 营养分析
    recorded_at     TIMESTAMPTZ NOT NULL,         -- 记录时间（用户可选，非创建时间）
    record_date     DATE NOT NULL,               -- 记录日期（冗余，方便按日查询）
    meal_plan_id    UUID REFERENCES meal_plans(id), -- 关联餐食计划（可选）
    source          VARCHAR(20) DEFAULT 'manual'
                    CHECK (source IN ('manual', 'plan', 'photo', 'voice')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

-- 索引（高频查询：按用户+日期查、按用户+日期+餐次查）
CREATE INDEX idx_diet_records_user_date ON diet_records(user_id, record_date DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_diet_records_user_meal ON diet_records(user_id, record_date, meal_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_diet_records_meal_plan ON diet_records(meal_plan_id) WHERE meal_plan_id IS NOT NULL;
```

**meal_type 枚举说明：**

| 值 | 含义 | 典型时间 |
|----|------|----------|
| breakfast | 早餐 | 06:00 - 10:00 |
| lunch | 午餐 | 11:00 - 14:00 |
| dinner | 晚餐 | 17:00 - 20:00 |
| snack | 加餐 | 其他时间 |

**source 枚举说明：**

| 值 | 含义 |
|----|------|
| manual | 手动文字输入 |
| plan | 从餐食计划一键记录 |
| photo | 拍照识别（后续） |
| voice | 语音输入（后续） |

---

### 3.5 `meal_plans` — 餐食计划表

```sql
CREATE TABLE meal_plans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_date       DATE NOT NULL,               -- 计划日期
    breakfast       JSONB,                       -- 早餐方案
    lunch           JSONB,                       -- 午餐方案
    dinner          JSONB,                       -- 晚餐方案
    -- breakfast/lunch/dinner 结构：
    -- {
    --   "name": "元气早餐",
    --   "foods": [
    --     {
    --       "name": "小米粥",
    --       "amount": "1碗",
    --       "grams": 200,
    --       "calories": 120,
    --       "protein": 3,
    --       "fat": 1,
    --       "carbs": 25,
    --       "cooking_method": "煮",
    --       "recipe_tip": "小米淘洗后大火煮开，小火慢熬20分钟"
    --     }
    --   ],
    --   "total_calories": 290,
    --   "total_protein": 18,
    --   "total_fat": 10,
    --   "total_carbs": 32,
    --   "prep_time_min": 15
    -- }
    total_calories  INT DEFAULT 0,               -- 全天总热量
    total_protein   DECIMAL(8,2) DEFAULT 0,
    total_fat       DECIMAL(8,2) DEFAULT 0,
    total_carbs     DECIMAL(8,2) DEFAULT 0,
    ai_note         TEXT,                        -- AI 整体建议
    status          VARCHAR(20) DEFAULT 'pending'
                    CHECK (status IN ('pending', 'partial', 'completed', 'skipped')),
    -- pending: 未开始  partial: 部分已记录  completed: 全部已记录  skipped: 跳过
    generate_params JSONB,                       -- 生成时的参数快照
    -- {
    --   "model": "qwen-plus",
    --   "user_request": "今天想吃清淡点",
    --   "goal_type": "weight_loss",
    --   "target_calories": 1580
    -- }
    version         INT DEFAULT 1,               -- 版本号（替换/调整时递增）
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, plan_date)                   -- 每人每天一个计划
);

CREATE INDEX idx_meal_plans_user_date ON meal_plans(user_id, plan_date DESC);
CREATE INDEX idx_meal_plans_status ON meal_plans(status) WHERE status = 'pending';
```

---

### 3.6 `ai_chats` — AI 对话表

```sql
CREATE TABLE ai_chats (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id      UUID NOT NULL,               -- 会话 ID（一轮对话）
    role            VARCHAR(20) NOT NULL
                    CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,               -- 消息内容
    context_snapshot JSONB,                      -- 对话时的上下文快照
    -- {
    --   "goal_type": "weight_loss",
    --   "today_calories": 860,
    --   "today_meals": ["breakfast"],
    --   "weekly_avg_calories": 1520,
    --   "recent_deficiencies": ["iron", "fiber"]
    -- }
    model_used      VARCHAR(50),                 -- 使用的 AI 模型
    tokens_used     INT,                         -- 消耗 token 数
    cost_yuan       DECIMAL(6,4),                -- 费用（元）
    response_time_ms INT,                        -- 响应时间 ms
    is_streaming    BOOLEAN DEFAULT false,        -- 是否流式响应
    parent_id       UUID REFERENCES ai_chats(id), -- 父消息（用于树状对话）
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_ai_chats_user_session ON ai_chats(user_id, session_id, created_at);
CREATE INDEX idx_ai_chats_user_recent ON ai_chats(user_id, created_at DESC);
```

**会话管理说明：**

```
一个 session_id = 一轮连续对话

session_001:
  ├─ [user]      "我最近总是疲劳，饮食上需要调整什么？"
  ├─ [assistant]  "根据你近一周的饮食记录分析..."
  ├─ [user]      "那具体应该吃什么？"
  └─ [assistant]  "推荐以下食材..."

session_002:
  ├─ [user]      "今天中午吃什么好？"
  └─ [assistant]  "根据你的减重目标..."
```

---

### 3.7 `daily_summaries` — 每日饮食汇总表（冗余优化）

```sql
CREATE TABLE daily_summaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary_date    DATE NOT NULL,               -- 日期
    total_calories  INT DEFAULT 0,               -- 总热量
    total_protein   DECIMAL(8,2) DEFAULT 0,
    total_fat       DECIMAL(8,2) DEFAULT 0,
    total_carbs     DECIMAL(8,2) DEFAULT 0,
    total_fiber     DECIMAL(8,2) DEFAULT 0,
    meal_count      INT DEFAULT 0,               -- 记录餐数
    breakfast_cal   INT DEFAULT 0,               -- 早餐热量
    lunch_cal       INT DEFAULT 0,               -- 午餐热量
    dinner_cal      INT DEFAULT 0,               -- 晚餐热量
    snack_cal       INT DEFAULT 0,               -- 加餐热量
    calorie_target  INT,                         -- 当日目标热量
    calorie_diff    INT,                         -- 热量差值（正=超标，负=不足）
    target_achieved BOOLEAN DEFAULT false,        -- 是否达标
    weight_recorded DECIMAL(5,1),                -- 当日体重（可选）
    water_ml        INT,                         -- 饮水量 ml
    notes           TEXT,                        -- 备注
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, summary_date)
);

CREATE INDEX idx_daily_summaries_user_date ON daily_summaries(user_id, summary_date DESC);
CREATE INDEX idx_daily_summaries_user_week ON daily_summaries(user_id, summary_date DESC);
```

**用途：**
- 按日/周/月查询汇总数据时直接查此表，避免 `diet_records` 大量聚合计算
- 每次新增/修改 `diet_records` 时通过触发器或应用层更新此表
- 报告页面直接读取，性能好

---

### 3.8 `nutrition_references` — 营养参考标准表（预置）

```sql
CREATE TABLE nutrition_references (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    population      VARCHAR(50) NOT NULL,        -- 人群分类
    -- population: adult_male / adult_female / pregnant / lactating / elderly / child
    age_min         INT,
    age_max         INT,
    nutrient        VARCHAR(50) NOT NULL,        -- 营养素名称
    unit            VARCHAR(10) NOT NULL,        -- 单位
    rni             DECIMAL(8,2),                -- 推荐摄入量 RNI
    ai_value        DECIMAL(8,2),                -- 适宜摄入量 AI
    ul              DECIMAL(8,2),                -- 可耐受最高摄入量 UL
    source          VARCHAR(100),                -- 数据来源
    notes           TEXT
);

-- 预置数据示例（中国居民膳食营养素参考摄入量 2023 版）
INSERT INTO nutrition_references (population, age_min, age_max, nutrient, unit, rni, source) VALUES
('adult_female', 18, 49, 'energy',      'kcal', 1800, '中国DRIs 2023'),
('adult_female', 18, 49, 'protein',     'g',    55,   '中国DRIs 2023'),
('adult_female', 18, 49, 'calcium',     'mg',   800,  '中国DRIs 2023'),
('adult_female', 18, 49, 'iron',        'mg',   20,   '中国DRIs 2023'),
('adult_female', 18, 49, 'folate',      'μg',   400,  '中国DRIs 2023'),
('pregnant',     18, 49, 'energy',      'kcal', 2100, '中国DRIs 2023'),
('pregnant',     18, 49, 'protein',     'g',    70,   '中国DRIs 2023'),
('pregnant',     18, 49, 'iron',        'mg',   24,   '中国DRIs 2023'),
('pregnant',     18, 49, 'folate',      'μg',   600,  '中国DRIs 2023'),
('pregnant',     18, 49, 'calcium',     'mg',   1000, '中国DRIs 2023'),
('pregnant',     18, 49, 'DHA',         'mg',   200,  '中国DRIs 2023');
```

---

### 3.9 `menstrual_cycles` — 生理期追踪表【新增】

```sql
CREATE TABLE menstrual_cycles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_start    DATE NOT NULL,               -- 经期开始日期
    period_end      DATE,                        -- 经期结束日期
    cycle_length    INT,                         -- 周期天数（本次）
    period_length   INT,                         -- 经期天数（本次）
    ovulation_day   DATE,                        -- 预测排卵日
    fertile_window_start DATE,                   -- 易孕窗口开始
    fertile_window_end   DATE,                   -- 易孕窗口结束
    symptoms        TEXT[] DEFAULT '{}',          -- 症状 ["痛经", "腰酸", "情绪波动"]
    mood            VARCHAR(20),                 -- 情绪状态
    flow_level      VARCHAR(20)                  -- 经量
                    CHECK (flow_level IN ('light', 'normal', 'heavy', 'very_heavy')),
    temperature     DECIMAL(4,2),                -- 基础体温 ℃（备孕用）
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_menstrual_cycles_user ON menstrual_cycles(user_id, period_start DESC);
```

**经期阶段计算逻辑（AI 推荐时使用）：**

```
┌──────────────────────────────────────────────────────────────┐
│ 一个完整周期（约 28 天）                                       │
│                                                              │
│  Day 1        Day 5      Day 14       Day 28                 │
│   │            │           │            │                     │
│   ▼            ▼           ▼            ▼                     │
│   ┌────────────┐ ┌─────────┐ ┌─────────────────────────────┐ │
│   │  月经期     │ │ 卵泡期  │ │  排卵期  │    黄体期         │ │
│   │ (Menstrual)│ │(Follic.)│ │(Ovulat.)│   (Luteal)        │ │
│   │ Day 1-5    │ │ Day 6-13│ │ Day 14  │   Day 15-28       │ │
│   └────────────┘ └─────────┘ └─────────┴───────────────────┘ │
│                                                              │
│  饮食重点：                                                    │
│  月经期 → 温补驱寒（红糖姜茶、当归羊肉汤）                      │
│  卵泡期 → 高蛋白补铁（鸡蛋、鱼、黑芝麻）                        │
│  排卵期 → 促排卵（黑豆、豆浆、叶酸）                            │
│  黄体期 → 缓解PMS（香蕉、燕麦、坚果）                          │
└──────────────────────────────────────────────────────────────┘
```

**预置数据 — 经期阶段饮食建议：**

```sql
CREATE TABLE cycle_phase_diet_tips (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase           VARCHAR(30) NOT NULL
                    CHECK (phase IN ('menstrual', 'follicular', 'ovulation', 'luteal')),
    phase_name_cn   VARCHAR(20) NOT NULL,        -- 中文名
    diet_focus      TEXT NOT NULL,                -- 饮食重点
    recommended_foods JSONB NOT NULL,             -- 推荐食物
    avoid_foods     JSONB NOT NULL,              -- 避免食物
    recommended_fruits JSONB NOT NULL,            -- 推荐水果
    avoid_fruits    JSONB NOT NULL,              -- 避免水果
    nutrients_focus TEXT[] NOT NULL,              -- 重点营养素
    sample_meals    JSONB,                        -- 示例餐食
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 预置数据
INSERT INTO cycle_phase_diet_tips (phase, phase_name_cn, diet_focus, recommended_foods, avoid_foods, recommended_fruits, avoid_fruits, nutrients_focus, sample_meals) VALUES
(
    'menstrual', '月经期',
    '温补驱寒，补充流失的铁质和蛋白质，忌生冷寒凉',
    '["红糖", "生姜", "当归", "羊肉", "红枣", "桂圆", "猪肝", "菠菜", "黑木耳", "红豆"]',
    '["冰淇淋", "冷饮", "西瓜", "梨", "螃蟹", "苦瓜"]',
    '["樱桃", "红枣", "桂圆", "榴莲", "荔枝"]',
    '["西瓜", "梨", "柿子", "柚子", "猕猴桃"]',
    '["铁", "蛋白质", "维生素C", "B族维生素"]',
    '{"breakfast": "红糖姜枣茶+水煮蛋+红枣小米粥", "lunch": "当归羊肉汤+菠菜炒猪肝+米饭", "dinner": "桂圆莲子粥+清蒸鲈鱼+西兰花"}'
),
(
    'follicular', '卵泡期',
    '补充优质蛋白和铁，为排卵做准备，多吃深色食物',
    '["鸡蛋", "鱼", "虾", "豆腐", "黑芝麻", "黑豆", "菠菜", "西兰花", "牛肉"]',
    '["油炸食品", "高糖食物"]',
    '["蓝莓", "草莓", "苹果", "葡萄", "牛油果"]',
    '["寒凉水果适量即可"]',
    '["铁", "蛋白质", "维生素E", "锌"]',
    '{"breakfast": "黑芝麻糊+水煮蛋+全麦面包", "lunch": "清蒸鲈鱼+西兰花炒虾仁+糙米饭", "dinner": "番茄牛肉炖土豆+凉拌菠菜+玉米"}'
),
(
    'ovulation', '排卵期',
    '补充叶酸和锌，促进卵子质量，温补子宫',
    '["黑豆", "黄豆", "豆浆", "坚果", "深海鱼", "牛油果", "芦笋", "菠菜"]',
    '["酒精", "咖啡过量", "寒凉食物"]',
    '["牛油果", "蓝莓", "石榴", "猕猴桃"]',
    '["冰镇水果"]',
    '["叶酸", "锌", "Omega-3", "维生素D"]',
    '{"breakfast": "黑豆豆浆+牛油果吐司+坚果", "lunch": "三文鱼沙拉+芦笋炒虾仁+糙米饭", "dinner": "番茄豆腐汤+蒜蓉菠菜+杂粮饭"}'
),
(
    'luteal', '黄体期',
    '补充B族维生素和镁，缓解PMS症状，控制盐分摄入',
    '["香蕉", "燕麦", "坚果", "菠菜", "全谷物", "红薯", "鸡肉", "深海鱼"]',
    '["高盐食物", "咖啡因过量", "酒精", "辛辣刺激"]',
    '["香蕉", "苹果", "橙子", "樱桃", "蓝莓"]',
    '["高糖水果适量"]',
    '["维生素B6", "镁", "钙", "Omega-3"]',
    '{"breakfast": "燕麦香蕉粥+坚果+酸奶", "lunch": "鸡肉沙拉+红薯+西兰花", "dinner": "清蒸三文鱼+蒜蓉菠菜+小米粥"}'
);
```

---

### 3.10 `families` — 家庭账户表【新增】

```sql
CREATE TABLE families (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,       -- 家庭名称 "小美和阿杰的家"
    invite_code     VARCHAR(20) UNIQUE NOT NULL,  -- 邀请码（6位）
    creator_id      UUID NOT NULL REFERENCES users(id),
    max_members     INT DEFAULT 6,               -- 最大成员数
    settings        JSONB DEFAULT '{}',           -- 家庭设置
    -- {
    --   "shared_grocery_list": true,           -- 共享购物清单
    --   "meal_plan_sync": true,                -- 餐食计划同步
    --   "allow_member_view_all": true          -- 成员可查看所有人数据
    -- }
    status          VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active', 'dissolved')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_families_invite ON families(invite_code) WHERE status = 'active';
```

---

### 3.11 `family_members` — 家庭成员表【新增】

```sql
CREATE TABLE family_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_id       UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL DEFAULT 'member'
                    CHECK (role IN ('owner', 'admin', 'member', 'child')),
    -- owner: 创建者  admin: 管理员  member: 普通成员  child: 儿童（只读）
    relation        VARCHAR(30),                 -- 家庭关系
    -- relation: spouse/partner/parent/child/sibling/other
    display_name    VARCHAR(50),                 -- 家庭内显示名
    can_view_health BOOLEAN DEFAULT true,        -- 可查看健康数据
    can_edit_plan   BOOLEAN DEFAULT true,        -- 可编辑餐食计划
    joined_at       TIMESTAMPTZ DEFAULT NOW(),
    status          VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active', 'left', 'removed')),

    UNIQUE(family_id, user_id)
);

CREATE INDEX idx_family_members_family ON family_members(family_id) WHERE status = 'active';
CREATE INDEX idx_family_members_user ON family_members(user_id) WHERE status = 'active';
```

---

### 3.12 `body_metrics` — 身体数据追踪表【新增】

```sql
CREATE TABLE body_metrics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_date     DATE NOT NULL,               -- 记录日期
    weight          DECIMAL(5,1),                -- 体重 kg
    body_fat_pct    DECIMAL(4,1),                -- 体脂率 %
    muscle_mass     DECIMAL(5,1),                -- 肌肉量 kg
    bmi             DECIMAL(4,1),                -- BMI
    waist_circum    DECIMAL(5,1),                -- 腰围 cm
    hip_circum      DECIMAL(5,1),                -- 臀围 cm
    blood_pressure_sys INT,                      -- 收缩压 mmHg
    blood_pressure_dia INT,                      -- 舒张压 mmHg
    blood_sugar     DECIMAL(4,1),                -- 空腹血糖 mmol/L
    heart_rate      INT,                         -- 心率 bpm
    sleep_hours     DECIMAL(3,1),                -- 睡眠时长 h
    water_ml        INT,                         -- 饮水量 ml
    steps           INT,                         -- 步数
    exercise_min    INT,                         -- 运动时长 min
    source          VARCHAR(20) DEFAULT 'manual'
                    CHECK (source IN ('manual', 'apple_health', 'xiaomi', 'huawei')),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, metric_date)
);

CREATE INDEX idx_body_metrics_user_date ON body_metrics(user_id, metric_date DESC);
```

**source 枚举说明：**

| 值 | 含义 |
|----|------|
| manual | 手动输入 |
| apple_health | Apple Health 同步 |
| xiaomi | 小米手环/手表 |
| huawei | 华为手环/手表 |

---

### 3.13 `fruit_items` — 水果数据库表（预置）【新增】

```sql
CREATE TABLE fruit_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(50) NOT NULL UNIQUE, -- 水果名称
    name_en         VARCHAR(50),                 -- 英文名
    calories_per_100g INT NOT NULL,              -- 热量 kcal/100g
    sugar_per_100g  DECIMAL(4,1),                -- 含糖量 g/100g
    gi_value        INT,                         -- 升糖指数 GI
    gl_value        DECIMAL(4,1),                -- 血糖负荷 GL
    fiber_per_100g  DECIMAL(4,1),                -- 膳食纤维 g
    vitamin_c       DECIMAL(6,2),                -- 维生素C mg
    folic_acid      DECIMAL(6,2),                -- 叶酸 μg
    iron            DECIMAL(6,2),                -- 铁 mg
    potassium       DECIMAL(6,2),                -- 钾 mg
    nature          VARCHAR(20)                  -- 性味
                    CHECK (nature IN ('hot', 'warm', 'neutral', 'cool', 'cold')),
    -- hot: 热性  warm: 温性  neutral: 平性  cool: 凉性  cold: 寒性
    taste           VARCHAR(20),                 -- 味道
    effects         TEXT[] DEFAULT '{}',          -- 功效
    -- effects: ["补血", "润肠", "美白", "抗氧化", "补叶酸", "降血压"]
    suitable_for    TEXT[] DEFAULT '{}',          -- 适宜人群
    -- suitable_for: ["减肥", "备孕", "经期", "孕妇", "高血压", "糖尿病"]
    avoid_for       TEXT[] DEFAULT '{}',          -- 不适宜人群
    -- avoid_for: ["经期寒凉体质", "脾胃虚寒", "高血糖"]
    seasons         INT[] DEFAULT '{}',           -- 应季月份 [1,2,...,12]
    image_url       VARCHAR(512),
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_fruit_items_seasons ON fruit_items USING gin(seasons);
CREATE INDEX idx_fruit_items_suitable ON fruit_items USING gin(suitable_for);
CREATE INDEX idx_fruit_items_nature ON fruit_items(nature);
```

**预置水果数据示例：**

```sql
INSERT INTO fruit_items (name, calories_per_100g, sugar_per_100g, gi_value, nature, effects, suitable_for, avoid_for, seasons) VALUES
('樱桃',   46,  10.2, 22, 'warm',  '{"补铁","补血","美容"}',           '{"经期","备孕","贫血"}',           '{"高血糖"}',             '{5,6}'),
('红枣',   122, 28.0, 103,'warm',  '{"补血","安神","健脾"}',           '{"经期","备孕","贫血"}',           '{"糖尿病","高血糖"}',     '{9,10,11}'),
('桂圆',   71,  16.0, 53, 'warm',  '{"补血","安神","益气"}',           '{"经期","体寒"}',                  '{"上火","高血糖"}',       '{7,8}'),
('榴莲',   147, 27.0, 70, 'hot',   '{"活血散寒","补虚"}',              '{"经期寒凉体质"}',                 '{"高血糖","肥胖"}',       '{6,7,8,9}'),
('蓝莓',   57,  10.0, 25, 'neutral','{"抗氧化","护眼","补叶酸"}',       '{"备孕","用眼过度"}',              '{}',                     '{6,7,8}'),
('牛油果', 160,  0.7, 27, 'neutral','{"补叶酸","好脂肪","美容"}',       '{"备孕","减肥"}',                  '{}',                     '{3,4,5,6,7,8,9}'),
('苹果',   52,  10.4, 36, 'neutral','{"润肠","降脂","美容"}',           '{"减肥","便秘","高血脂"}',         '{}',                     '{7,8,9,10,11}'),
('香蕉',   89,  12.2, 52, 'neutral','{"润肠","补钾","安神"}',           '{"经前期","便秘","高血压"}',        '{"腹泻","高血糖"}',       '{1,2,3,4,5,6,7,8,9,10,11,12}'),
('西瓜',   30,  6.2,  72, 'cold',  '{"清热","解暑","利尿"}',           '{"暑热"}',                         '{"经期","脾胃虚寒","高血糖"}', '{6,7,8}'),
('梨',     50,  9.8,  36, 'cool',  '{"润肺","止咳","清热"}',           '{"咳嗽","干燥"}',                  '{"经期","脾胃虚寒"}',     '{8,9,10}'),
('猕猴桃', 61,  9.0,  39, 'cold',  '{"补VC","通便","美白"}',           '{"便秘","美白需求"}',              '{"经期","脾胃虚寒"}',     '{9,10,11}'),
('草莓',   32,  4.9,  25, 'cool',  '{"补VC","美白","抗氧化"}',         '{"美白","备孕"}',                  '{"脾胃虚寒"}',           '{2,3,4}'),
('橙子',   47,  9.4,  43, 'neutral','{"补VC","开胃","化痰"}',           '{"感冒","开胃"}',                  '{}',                     '{10,11,12,1,2,3}'),
('石榴',   83,  13.7, 35, 'warm',  '{"补血","抗氧化","收敛"}',         '{"经期","备孕"}',                  '{"便秘"}',               '{9,10,11}'),
('葡萄',   69,  16.1, 46, 'neutral','{"补血","抗氧化","补钾"}',         '{"贫血","疲劳"}',                  '{"高血糖"}',             '{7,8,9,10}');
```

---

## 4. 视图

### 4.1 用户当日饮食汇总视图

```sql
CREATE VIEW v_user_today_diet AS
SELECT
    u.id AS user_id,
    u.nickname,
    u.daily_calorie_target,
    COALESCE(ds.total_calories, 0) AS today_calories,
    COALESCE(ds.total_protein, 0) AS today_protein,
    COALESCE(ds.total_fat, 0) AS today_fat,
    COALESCE(ds.total_carbs, 0) AS today_carbs,
    COALESCE(ds.meal_count, 0) AS meal_count,
    ROUND(
        COALESCE(ds.total_calories, 0)::numeric /
        NULLIF(u.daily_calorie_target, 0) * 100, 1
    ) AS calorie_progress_pct
FROM users u
LEFT JOIN daily_summaries ds
    ON u.id = ds.user_id AND ds.summary_date = CURRENT_DATE
WHERE u.deleted_at IS NULL;
```

### 4.2 用户本周营养趋势视图

```sql
CREATE VIEW v_user_weekly_nutrition AS
SELECT
    user_id,
    DATE_TRUNC('week', summary_date) AS week_start,
    ROUND(AVG(total_calories)) AS avg_daily_calories,
    ROUND(AVG(total_protein), 1) AS avg_daily_protein,
    ROUND(AVG(total_fat), 1) AS avg_daily_fat,
    ROUND(AVG(total_carbs), 1) AS avg_daily_carbs,
    ROUND(AVG(total_fiber), 1) AS avg_daily_fiber,
    COUNT(*) AS days_recorded,
    SUM(CASE WHEN target_achieved THEN 1 ELSE 0 END) AS days_achieved
FROM daily_summaries
WHERE summary_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY user_id, DATE_TRUNC('week', summary_date);
```

---

## 5. 触发器

### 5.1 饮食记录变更时更新每日汇总

```sql
CREATE OR REPLACE FUNCTION refresh_daily_summary()
RETURNS TRIGGER AS $$
BEGIN
    -- 重新计算当日汇总
    INSERT INTO daily_summaries (user_id, summary_date, total_calories, total_protein,
                                  total_fat, total_carbs, total_fiber, meal_count,
                                  breakfast_cal, lunch_cal, dinner_cal, snack_cal)
    SELECT
        user_id,
        record_date,
        SUM(total_calories),
        SUM(total_protein),
        SUM(total_fat),
        SUM(total_carbs),
        SUM(total_fiber),
        COUNT(*),
        SUM(CASE WHEN meal_type = 'breakfast' THEN total_calories ELSE 0 END),
        SUM(CASE WHEN meal_type = 'lunch' THEN total_calories ELSE 0 END),
        SUM(CASE WHEN meal_type = 'dinner' THEN total_calories ELSE 0 END),
        SUM(CASE WHEN meal_type = 'snack' THEN total_calories ELSE 0 END)
    FROM diet_records
    WHERE user_id = COALESCE(NEW.user_id, OLD.user_id)
      AND record_date = COALESCE(NEW.record_date, OLD.record_date)
      AND deleted_at IS NULL
    GROUP BY user_id, record_date
    ON CONFLICT (user_id, summary_date)
    DO UPDATE SET
        total_calories = EXCLUDED.total_calories,
        total_protein = EXCLUDED.total_protein,
        total_fat = EXCLUDED.total_fat,
        total_carbs = EXCLUDED.total_carbs,
        total_fiber = EXCLUDED.total_fiber,
        meal_count = EXCLUDED.meal_count,
        breakfast_cal = EXCLUDED.breakfast_cal,
        lunch_cal = EXCLUDED.lunch_cal,
        dinner_cal = EXCLUDED.dinner_cal,
        snack_cal = EXCLUDED.snack_cal,
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_diet_records_refresh_summary
    AFTER INSERT OR UPDATE OR DELETE ON diet_records
    FOR EACH ROW EXECUTE FUNCTION refresh_daily_summary();
```

---

## 6. 数据量预估 & 分区策略

### 6.1 数据量预估（首年）

| 表 | 日增量 | 月增量 | 年增量 | 单行大小 | 年数据量 |
|----|--------|--------|--------|----------|----------|
| users | 10 | 300 | 3,600 | 1 KB | 3.6 MB |
| diet_records | 1,000 | 30,000 | 365,000 | 2 KB | 730 MB |
| meal_plans | 500 | 15,000 | 182,500 | 3 KB | 548 MB |
| ai_chats | 3,000 | 90,000 | 1,095,000 | 1 KB | 1.1 GB |
| daily_summaries | 500 | 15,000 | 182,500 | 0.5 KB | 91 MB |
| menstrual_cycles | 100 | 3,000 | 36,000 | 0.5 KB | 18 MB |
| body_metrics | 200 | 6,000 | 73,000 | 0.5 KB | 36.5 MB |
| families | 5 | 150 | 1,800 | 0.5 KB | 0.9 MB |
| family_members | 10 | 300 | 3,600 | 0.3 KB | 1.1 MB |
| food_items | 预置 | - | - | - | 约 5 MB (5000条) |
| fruit_items | 预置 | - | - | - | 约 0.5 MB (100条) |
| cycle_phase_diet_tips | 预置 | - | - | - | 约 0.1 MB (4条) |
| nutrition_references | 预置 | - | - | - | 约 0.5 MB (200条) |

### 6.2 分区策略

当 `ai_chats` 和 `diet_records` 数据量超过 500 万行时，按月分区：

```sql
-- ai_chats 按月分区示例
CREATE TABLE ai_chats (
    -- ... 字段同上 ...
) PARTITION BY RANGE (created_at);

CREATE TABLE ai_chats_2026_06 PARTITION OF ai_chats
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

CREATE TABLE ai_chats_2026_07 PARTITION OF ai_chats
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
```

---

## 7. 安全策略

| 策略 | 实现 |
|------|------|
| **行级安全 (RLS)** | 用户只能访问自己的数据 |
| **字段加密** | phone 字段应用层 AES 加密存储 |
| **软删除** | 核心表 deleted_at 字段，定期归档 |
| **审计日志** | 敏感操作记录到 audit_logs 表 |
| **数据脱敏** | 日志中 phone 脱敏为 138****8888 |

```sql
-- RLS 示例
ALTER TABLE diet_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_own_diet_records ON diet_records
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::uuid);
```

---

## 8. 完整 ER 图（最终版）

```
                              ┌─────────────────────┐
                              │  families (家庭账户)  │
                              ├─────────────────────┤
                              │ PK id               │
                              │    name             │
                              │    invite_code (UQ) │
                              │ FK creator_id       │
                              │    max_members      │
                              │    settings (JSON)  │
                              │    status           │
                              └──────────┬──────────┘
                                         │ 1:N
                                         ▼
┌─────────────────────┐      ┌─────────────────────┐
│       users         │ 1:N  │  family_members     │
├─────────────────────┤◀─────├─────────────────────┤
│ PK id               │      │ PK id               │
│    phone (UQ)       │      │ FK family_id        │
│    wechat_openid(UQ)│      │ FK user_id          │
│    nickname          │      │    role             │
│    avatar_url        │      │    relation         │
│    gender            │      │    display_name     │
│    birthday          │      │    can_view_health  │
│    height_cm         │      │    can_edit_plan    │
│    current_weight    │      │    status           │
│    target_weight     │      └─────────────────────┘
│    activity_level    │
│    preferences (JSON)│
│    daily_calorie_target│
│    status            │
│    last_login_at     │
│    created_at        │
│    updated_at        │
│    deleted_at        │
└────────┬────────────┘
         │
         │ 1:N
         ├──────────────────────────────────────────────┐
         │                    │                         │
         ▼                    ▼                         ▼
┌─────────────────┐ ┌─────────────────┐     ┌─────────────────────┐
│  health_goals   │ │menstrual_cycles │     │    ai_chats         │
├─────────────────┤ │ (生理期追踪)     │     ├─────────────────────┤
│ PK id           │ ├─────────────────┤     │ PK id               │
│ FK user_id      │ │ PK id           │     │ FK user_id          │
│    goal_type    │ │ FK user_id      │     │    session_id       │
│    target_weight│ │    period_start │     │    role             │
│    target_date  │ │    period_end   │     │    content          │
│    weekly_loss  │ │    cycle_length │     │    context_snapshot │
│    daily_cal    │ │    ovulation_day│     │    model_used       │
│    macro(JSON)  │ │    fertile_win  │     │    tokens_used      │
│    special_notes│ │    symptoms[]   │     │    cost_yuan        │
│    status       │ │    flow_level   │     │    response_time_ms │
│    created_at   │ │    temperature  │     │    parent_id        │
│    updated_at   │ │    notes        │     │    created_at       │
└─────────────────┘ │    created_at   │     └─────────────────────┘
                    │    updated_at   │
                    └─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐         ┌─────────────────────┐
│   meal_plans        │ 1:N     │   diet_records      │
├─────────────────────┤◀────────├─────────────────────┤
│ PK id               │         │ PK id               │
│ FK user_id          │         │ FK user_id          │
│    plan_date (UQ)   │         │ FK meal_plan_id     │
│    breakfast (JSON) │         │    meal_type        │
│    lunch (JSON)     │         │    food_text        │
│    dinner (JSON)    │         │    parsed_foods(JSON)│
│    total_calories   │         │    total_calories   │
│    total_protein    │         │    total_protein    │
│    total_fat        │         │    total_fat        │
│    total_carbs      │         │    total_carbs      │
│    ai_note          │         │    total_fiber      │
│    status           │         │    ai_analysis      │
│    generate_params  │         │    recorded_at      │
│    version          │         │    record_date      │
│    created_at       │         │    source           │
│    updated_at       │         │    created_at       │
└─────────────────────┘         │    updated_at       │
                                │    deleted_at       │
┌─────────────────────┐         └─────────────────────┘
│   food_items        │
├─────────────────────┤         ┌─────────────────────┐
│ PK id               │         │ daily_summaries     │
│    name             │         ├─────────────────────┤
│    name_en          │         │ PK id               │
│    category         │         │ FK user_id          │
│    subcategory      │         │    summary_date(UQ) │
│    per_amount       │         │    total_calories   │
│    per_grams        │         │    total_protein    │
│    calories         │         │    total_fat        │
│    protein          │         │    total_carbs      │
│    fat              │         │    total_fiber      │
│    carbs            │         │    meal_count       │
│    fiber            │         │    breakfast_cal    │
│    vitamin_a/c/d    │         │    lunch_cal        │
│    calcium/iron/zinc│         │    dinner_cal       │
│    folate           │         │    snack_cal        │
│    sodium           │         │    calorie_target   │
│    glycemic_index   │         │    calorie_diff     │
│    tags[]           │         │    target_achieved  │
│    season[]         │         │    weight_recorded  │
│    is_common        │         │    water_ml         │
│    image_url        │         │    notes            │
│    created_at       │         │    created_at       │
│    updated_at       │         │    updated_at       │
└─────────────────────┘         └─────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│nutrition_references │  │ cycle_phase_diet    │  │   fruit_items       │
├─────────────────────┤  │ (经期阶段饮食建议)   │  │  (水果数据库)        │
│ PK id               │  ├─────────────────────┤  ├─────────────────────┤
│    population       │  │ PK id               │  │ PK id               │
│    age_min          │  │    phase            │  │    name (UQ)        │
│    age_max          │  │    phase_name_cn    │  │    calories/100g    │
│    nutrient         │  │    diet_focus       │  │    sugar/100g       │
│    unit             │  │    recommended_food │  │    gi_value         │
│    rni              │  │    avoid_foods      │  │    gl_value         │
│    ai_value         │  │    recommended_fruit│  │    nature (寒热)    │
│    ul               │  │    avoid_fruits     │  │    effects[]        │
│    source           │  │    nutrients_focus  │  │    suitable_for[]   │
│    notes            │  │    sample_meals     │  │    avoid_for[]      │
└─────────────────────┘  └─────────────────────┘  │    seasons[]        │
                                                  └─────────────────────┘

┌─────────────────────┐
│   body_metrics      │
│  (身体数据追踪)      │
├─────────────────────┤
│ PK id               │
│ FK user_id          │
│    metric_date (UQ) │
│    weight           │
│    body_fat_pct     │
│    muscle_mass      │
│    bmi              │
│    waist/hip        │
│    blood_pressure   │
│    blood_sugar      │
│    heart_rate       │
│    sleep_hours      │
│    water_ml         │
│    steps            │
│    exercise_min     │
│    source           │
│    notes            │
└─────────────────────┘
```

### 表清单汇总

| 序号 | 表名 | 说明 | 类型 |
|------|------|------|------|
| 1 | users | 用户表 | 业务 |
| 2 | health_goals | 健康目标表 | 业务 |
| 3 | food_items | 食物数据库 | 预置 |
| 4 | diet_records | 饮食记录表 | 业务 |
| 5 | meal_plans | 餐食计划表 | 业务 |
| 6 | ai_chats | AI 对话表 | 业务 |
| 7 | daily_summaries | 每日汇总表 | 冗余 |
| 8 | nutrition_references | 营养参考标准 | 预置 |
| 9 | **menstrual_cycles** | **生理期追踪表** | **业务【新增】** |
| 10 | **cycle_phase_diet_tips** | **经期阶段饮食建议** | **预置【新增】** |
| 11 | **families** | **家庭账户表** | **业务【新增】** |
| 12 | **family_members** | **家庭成员表** | **业务【新增】** |
| 13 | **body_metrics** | **身体数据追踪表** | **业务【新增】** |
| 14 | **fruit_items** | **水果数据库** | **预置【新增】** |

---

*文档版本：v1.1 | 更新日期：2026-06-07*
