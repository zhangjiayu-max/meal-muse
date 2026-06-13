# MealMuse 中医扩展数据库设计稿

> 版本：v1.0 | 创建日期：2026-06-07 | 对应：database-design.md 的中医模块扩展
>
> **设计目标：** 为后续接入中医体质辨识、食疗推荐、节气养生提供完整的数据层支撑，同时与现有营养数据库无缝融合。

---

## 1. 新增 ER 关系图

```
                          ┌──────────────────┐
                          │ tcm_constitutions│
                          │  (九种体质定义)   │
                          └────────┬─────────┘
                                   │ 1:N
                                   ▼
┌──────────────┐           ┌──────────────────┐           ┌──────────────────┐
│   users      │◀─────────│ user_tcm_profiles│           │ food_tcm_props   │
│  (用户表)     │ 1:N      │ (用户体质档案)    │           │ (食物中医属性)    │
└──────┬───────┘           └──────────────────┘           └────────┬─────────┘
       │                                                           │ 1:1
       │                                                           ▼
       │                                                   ┌──────────────────┐
       │                                                   │   food_items     │
       │                                                   │  (食物数据库)     │
       │                                                   └──────────────────┘
       │
       │                   ┌──────────────────┐
       │                   │  solar_terms     │
       │                   │  (二十四节气)     │
       │                   └──────────────────┘
       │
       │                   ┌──────────────────┐
       └──────────────────▶│ tcm_rec_rules    │
                           │ (食疗推荐规则)    │
                           └──────────────────┘
```

---

## 2. 新增表结构

### 2.1 `tcm_constitutions` — 九种体质定义表（预置）

依据《中医体质分类与判定》国家标准（GB/T 21709-2008）。

```sql
CREATE TABLE tcm_constitutions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(30) UNIQUE NOT NULL,     -- 系统编码
    -- code: balanced / qi_deficiency / yang_deficiency / yin_deficiency /
    --       phlegm_dampness / dampness_heat / blood_stasis /
    --       qi_stagnation / special_constitution
    name_cn         VARCHAR(20) NOT NULL,            -- 中文名：气虚质
    name_en         VARCHAR(50),                     -- 英文名：Qi Deficiency
    element         VARCHAR(10),                     -- 五行归属：木/火/土/金/水
    description     TEXT NOT NULL,                   -- 体质描述
    common_signs    TEXT[] DEFAULT '{}',             -- 常见表现
    -- e.g. ['易疲劳', '气短懒言', '出汗多', '声音低弱']
    physical_features TEXT[] DEFAULT '{}',           -- 形体特征
    mental_features TEXT[] DEFAULT '{}',             -- 心理特征
    disease_tendency TEXT[] DEFAULT '{}',            -- 发病倾向
    adaptability    TEXT,                            -- 对外界环境适应能力
    diet_principles TEXT NOT NULL,                   -- 饮食调养总则
    recommended_foods TEXT[] DEFAULT '{}',           -- 推荐食材
    avoided_foods   TEXT[] DEFAULT '{}',             -- 少食/忌口食材
    recommended_cooking TEXT[] DEFAULT '{}',         -- 推荐烹饪方式
    -- e.g. ['蒸', '煮', '炖', '焖']
    lifestyle_advice TEXT,                           -- 起居建议
    exercise_advice  TEXT,                           -- 运动建议
    emotion_advice   TEXT,                           -- 情志调摄
    sort_order      INT DEFAULT 0,                   -- 排序（平和质排第一）
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tcm_constitutions_code ON tcm_constitutions(code);
CREATE INDEX idx_tcm_constitutions_element ON tcm_constitutions(element);
```

**预置数据 — 九种体质：**

```sql
INSERT INTO tcm_constitutions (code, name_cn, element, description, common_signs, physical_features, diet_principles, recommended_foods, avoided_foods, recommended_cooking, sort_order) VALUES
('balanced', '平和质', '土',
 '阴阳气血调和，以体态适中、面色红润、精力充沛等为主要特征。',
 ARRAY['精力充沛', '面色红润', '睡眠良好', '二便正常'],
 ARRAY['体形匀称健壮'],
 '饮食有节，劳逸结合，保持平衡。',
 ARRAY['粳米', '燕麦', '红薯', '山药', '鸡肉', '鱼肉', '苹果', '葡萄'],
 ARRAY['过寒过热', '过于油腻', '暴饮暴食'],
 ARRAY['蒸', '煮', '炖'],
 1
),
('qi_deficiency', '气虚质', '土',
 '元气不足，以疲乏、气短、自汗等气虚表现为主要特征。',
 ARRAY['易疲劳', '气短懒言', '出汗多', '声音低弱', '易感冒'],
 ARRAY['肌肉松软不实'],
 '益气健脾，避免生冷寒凉、耗气食物。',
 ARRAY['粳米', '小米', '山药', '红薯', '黄芪', '红枣', '桂圆', '鸡肉', '牛肉', '香菇'],
 ARRAY['生冷寒凉', '油腻厚味', '辛辣刺激', '空心菜', '生萝卜'],
 ARRAY['蒸', '煮', '炖', '煲汤'],
 2
),
('yang_deficiency', '阳虚质', '火',
 '阳气不足，以畏寒怕冷、手足不温等虚寒表现为主要特征。',
 ARRAY['畏寒怕冷', '手足不温', '喜热饮食', '精神不振', '睡眠偏多'],
 ARRAY['肌肉松软不实'],
 '温补阳气，忌食生冷寒凉。',
 ARRAY['羊肉', '韭菜', '核桃', '桂圆', '红枣', '生姜', '茴香', '杜仲', '肉桂'],
 ARRAY['冰镇饮料', '西瓜', '苦瓜', '绿豆', '螃蟹', '冷饮', '生鱼片'],
 ARRAY['炖', '焖', '烤', '煲汤'],
 3
),
('yin_deficiency', '阴虚质', '水',
 '阴液亏少，以口燥咽干、手足心热等虚热表现为主要特征。',
 ARRAY['手足心热', '口燥咽干', '鼻微干', '喜冷饮', '大便干燥'],
 ARRAY['体形偏瘦'],
 '滋阴润燥，避免辛辣温燥、耗伤阴液。',
 ARRAY['银耳', '百合', '梨', '荸荠', '莲藕', '甲鱼', '鸭肉', '黑芝麻', '枸杞', '麦冬'],
 ARRAY['辣椒', '花椒', '生姜', '羊肉', '韭菜', '桂圆', '荔枝', '油炸食品'],
 ARRAY['蒸', '炖', '凉拌', '清炒'],
 4
),
('phlegm_dampness', '痰湿质', '土',
 '痰湿凝聚，以形体肥胖、腹部肥满、口黏苔腻等痰湿表现为主要特征。',
 ARRAY['面部油脂多', '多汗且黏', '胸闷痰多', '口甜腻或淡', '喜食肥甘甜黏'],
 ARRAY['体形肥胖', '腹部肥满松软'],
 '健脾利湿，化痰泻浊，忌肥甘厚味。',
 ARRAY['薏苡仁', '赤小豆', '冬瓜', '白萝卜', '荷叶', '海带', '鲫鱼', '扁豆', '茯苓'],
 ARRAY['肥肉', '甜点', '奶油', '油炸食品', '糯米', '年糕', '酒类'],
 ARRAY['蒸', '煮', '炖', '清炒'],
 5
),
('dampness_heat', '湿热质', '土',
 '湿热内蕴，以面垢油光、口苦苔黄腻等湿热表现为主要特征。',
 ARRAY['面垢油光', '易生痤疮', '口苦口干', '身重困倦', '大便黏滞'],
 ARRAY['形体中等或偏瘦'],
 '清热化湿，饮食清淡，忌辛辣油腻、烟酒。',
 ARRAY['绿豆', '苦瓜', '冬瓜', '丝瓜', '芹菜', '莲藕', '荸荠', '薏苡仁', '绿茶'],
 ARRAY['辣椒', '花椒', '烧烤', '羊肉', '狗肉', '酒', '烟', '巧克力'],
 ARRAY['蒸', '煮', '凉拌', '清炖'],
 6
),
('blood_stasis', '血瘀质', '金',
 '血行不畅，以肤色晦暗、舌质紫黯等血瘀表现为主要特征。',
 ARRAY['肤色晦暗', '色素沉着', '易出现瘀斑', '口唇黯淡', '舌黯有瘀点'],
 ARRAY['胖瘦均见'],
 '活血化瘀，避免寒凉收涩、油腻碍血。',
 ARRAY['山楂', '黑木耳', '洋葱', '醋', '红糖', '玫瑰花', '红花', '桃仁', '当归'],
 ARRAY['寒凉收涩', '乌梅', '柿子', '苦瓜', '肥肉', '过咸'],
 ARRAY['炖', '煮', '蒸', '煲汤'],
 7
),
('qi_stagnation', '气郁质', '木',
 '气机郁滞，以神情抑郁、忧虑脆弱等气郁表现为主要特征。',
 ARRAY['神情抑郁', '情感脆弱', '烦闷不乐', '胸胁胀痛', '嗳气叹气'],
 ARRAY['形体瘦者居多'],
 '疏肝理气，解郁安神，避免收敛酸涩、冰冻寒凉。',
 ARRAY['柑橘', '玫瑰花', '茉莉花', '佛手', '白萝卜', '芹菜', '香菜', '大麦', '洋葱'],
 ARRAY['收敛酸涩', '乌梅', '南瓜', '泡菜', '冷冻饮料', '浓茶', '咖啡过量'],
 ARRAY['蒸', '煮', '炖', '煲汤'],
 8
),
('special_constitution', '特禀质', '金',
 '先天失常，以生理缺陷、过敏反应等为主要特征。',
 ARRAY['过敏体质', '易患花粉症', '易药物过敏', '皮肤划痕症', '过敏性鼻炎'],
 ARRAY['形体特征一般无特殊'],
 '益气固表，养血消风，避免明确过敏原及腥膻发物。',
 ARRAY['粳米', '山药', '红枣', '莲子', '芡实', '核桃', '黑芝麻', '蜂蜜'],
 ARRAY['明确过敏原', '海鲜发物', '羊肉', '鹅肉', '辣椒', '酒', '生冷'],
 ARRAY['蒸', '煮', '炖'],
 9
);
```

---

### 2.2 `user_tcm_profiles` — 用户体质档案表

```sql
CREATE TABLE user_tcm_profiles (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    primary_constitution    VARCHAR(30) REFERENCES tcm_constitutions(code),
    secondary_constitution  VARCHAR(30) REFERENCES tcm_constitutions(code),
    -- 体质测试原始得分（保留用于追溯）
    test_scores             JSONB DEFAULT '{}',
    -- test_scores 结构：
    -- {
    --   "balanced": 70, "qi_deficiency": 45, "yang_deficiency": 30, ...
    -- }
    -- 体质判定标准：原始分 >= 60 分且转化分 >= 40 分判定为"是"
    test_result_summary     TEXT,                   -- 测试结论摘要
    assessed_by             VARCHAR(20) DEFAULT 'quiz'
                            CHECK (assessed_by IN ('quiz', 'ai_chat', 'expert', 'self')),
    assessed_at             TIMESTAMPTZ DEFAULT NOW(),
    -- 体质会随时间、调理而变化，支持历史追踪
    is_current              BOOLEAN DEFAULT true,   -- 是否为当前生效的体质档案
    previous_profile_id     UUID REFERENCES user_tcm_profiles(id),
    notes                   TEXT,                   -- 用户/专家备注
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_tcm_profiles_user ON user_tcm_profiles(user_id, is_current);
CREATE INDEX idx_user_tcm_profiles_constitution ON user_tcm_profiles(primary_constitution);
```

**使用说明：**
- 用户可多次测试，每次生成一条记录，`is_current=true` 的只有一条
- 通过 `previous_profile_id` 形成体质变化链条，可用于展示"调理前后对比"
- AI 对话时，优先取 `is_current=true` 的体质档案作为 context

---

### 2.3 `food_tcm_properties` — 食物中医属性扩展表

与 `food_items` 1:1 或 N:1 关联。若一种食物在不同产地/品种下中医属性有差异，则使用 N:1。

```sql
CREATE TABLE food_tcm_properties (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    food_item_id    UUID REFERENCES food_items(id) ON DELETE CASCADE,
    -- 中医食性
    nature          VARCHAR(10) CHECK (nature IN ('hot', 'warm', 'neutral', 'cool', 'cold')),
    -- 性味：可同时有多种味道
    flavors         VARCHAR(10)[] DEFAULT '{}',
    -- flavors: {甘, 苦, 辛, 咸, 酸, 淡, 涩}
    -- 归经
    meridians       VARCHAR(20)[] DEFAULT '{}',
    -- meridians: {脾, 胃, 肺, 大肠, 心, 小肠, 肾, 膀胱, 肝, 胆, 三焦, 心包}
    -- 功效
    effects         TEXT[] DEFAULT '{}',
    -- effects: {补中益气, 健脾和胃, 养血安神, 清热解毒, 利水消肿, ...}
    -- 适用体质
    suitable_for_constitutions TEXT[] DEFAULT '{}',
    -- 不适用体质
    contraindicated_for_constitutions TEXT[] DEFAULT '{}',
    -- 特殊禁忌
    contraindications TEXT[] DEFAULT '{}',
    -- contraindications: {脾胃虚寒者慎食, 孕妇忌食, 经期慎食, ...}
    -- 最佳食用季节
    best_seasons    INT[] DEFAULT '{}',
    -- 食疗经典搭配（JSON，用于推荐时展示）
    classic_pairings JSONB DEFAULT '[]',
    -- classic_pairings: [
    --   {"pair_with": "红枣", "effect": "气血双补", "dish_example": "黄芪红枣鸡汤"}
    -- ]
    verified        BOOLEAN DEFAULT false,          -- 是否经中医专家审核
    verified_by     VARCHAR(100),                   -- 审核人
    source          TEXT,                           -- 数据来源（《本草纲目》/《食疗本草》/专家录入）
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(food_item_id)
);

CREATE INDEX idx_food_tcm_nature ON food_tcm_properties(nature);
CREATE INDEX idx_food_tcm_meridians ON food_tcm_properties USING gin(meridians);
CREATE INDEX idx_food_tcm_effects ON food_tcm_properties USING gin(effects);
CREATE INDEX idx_food_tcm_suitable ON food_tcm_properties USING gin(suitable_for_constitutions);
CREATE INDEX idx_food_tcm_verified ON food_tcm_properties(verified) WHERE verified = true;
```

**预置数据示例：**

```sql
INSERT INTO food_tcm_properties (food_item_id, nature, flavors, meridians, effects, suitable_for_constitutions, contraindicated_for_constitutions, contraindications, best_seasons, classic_pairings, verified, source) VALUES
(
    (SELECT id FROM food_items WHERE name = '生姜'),
    'warm', ARRAY['辛'], ARRAY['肺', '脾', '胃'],
    ARRAY['发汗解表', '温中止呕', '温肺止咳', '解毒'],
    ARRAY['yang_deficiency', 'qi_deficiency', 'balanced'],
    ARRAY['yin_deficiency', 'dampness_heat'],
    ARRAY['阴虚内热者忌食', '热盛及阴虚火旺者忌食'],
    ARRAY[10,11,12,1,2],
    '[{"pair_with": "红枣", "effect": "调和营卫", "dish_example": "姜枣茶"}, {"pair_with": "红糖", "effect": "温经散寒", "dish_example": "红糖姜茶"}]'::jsonb,
    true, '《本草纲目》《食疗本草》'
),
(
    (SELECT id FROM food_items WHERE name = '绿豆'),
    'cold', ARRAY['甘'], ARRAY['心', '胃'],
    ARRAY['清热解毒', '消暑利水'],
    ARRAY['dampness_heat', 'balanced'],
    ARRAY['yang_deficiency', 'qi_deficiency', 'special_constitution'],
    ARRAY['脾胃虚寒者慎食', '阳虚体质少食', '正在服用温补中药者忌食'],
    ARRAY[6,7,8],
    '[{"pair_with": "薏苡仁", "effect": "清热利湿", "dish_example": "绿豆薏米粥"}]'::jsonb,
    true, '《本草纲目》《食疗本草》'
),
(
    (SELECT id FROM food_items WHERE name = '菠菜'),
    'cool', ARRAY['甘'], ARRAY['肝', '胃', '大肠', '小肠'],
    ARRAY['滋阴平肝', '助消化', '止渴润肠'],
    ARRAY['yin_deficiency', 'blood_stasis', 'balanced'],
    ARRAY['yang_deficiency', 'phlegm_dampness'],
    ARRAY['脾虚便溏者慎食', '肾结石患者慎食（含草酸）', '经期寒凉体质慎食'],
    ARRAY[1,2,3,10,11,12],
    '[{"pair_with": "猪肝", "effect": "补肝养血", "dish_example": "菠菜猪肝汤"}]'::jsonb,
    true, '专家录入'
);
```

**与 `fruit_items` 的关联：**
- `fruit_items` 已包含 `nature` 字段（寒热温凉），后续可通过视图将 `fruit_items` 和 `food_items` 的中医属性统一查询

---

### 2.4 `solar_terms` — 二十四节气表（预置）

```sql
CREATE TABLE solar_terms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(20) UNIQUE NOT NULL,     -- start_of_spring / rain_water ...
    name_cn         VARCHAR(10) NOT NULL,            -- 立春
    name_en         VARCHAR(30),
    order_num       INT NOT NULL,                    -- 1-24
    -- 典型公历日期（用于前端展示，实际每年日期微调由应用层处理）
    typical_month   INT NOT NULL,
    typical_day     INT NOT NULL,
    -- 季节归属
    season          VARCHAR(10) CHECK (season IN ('spring', 'summer', 'autumn', 'winter')),
    -- 气候特征
    climate_features TEXT,
    -- 养生总则
    health_principle TEXT NOT NULL,
    -- 饮食原则
    diet_principle  TEXT NOT NULL,
    -- 推荐食材
    recommended_foods TEXT[] DEFAULT '{}',
    -- 推荐食谱（JSON）
    recommended_dishes JSONB DEFAULT '[]',
    -- 重点调理脏腑
    target_organs   TEXT[] DEFAULT '{}',
    -- target_organs: {肝, 心, 脾, 肺, 肾}
    -- 适用体质重点
    focus_constitutions TEXT[] DEFAULT '{}',
    -- 情志调摄
    emotion_advice  TEXT,
    -- 起居建议
    lifestyle_advice TEXT,
    -- 运动建议
    exercise_advice TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_solar_terms_order ON solar_terms(order_num);
CREATE INDEX idx_solar_terms_season ON solar_terms(season);
```

**预置数据示例（节选）：**

```sql
INSERT INTO solar_terms (code, name_cn, order_num, typical_month, typical_day, season, health_principle, diet_principle, recommended_foods, recommended_dishes, target_organs, focus_constitutions) VALUES
('start_of_spring', '立春', 1, 2, 4, 'spring',
 '立春养生，重点在养肝护阳，顺应春生之气。',
 '少酸增甘，以养脾气；多食绿色蔬菜，疏肝理气。',
 ARRAY['韭菜', '葱', '蒜', '菠菜', '芹菜', '荠菜', '豆芽', '红枣', '山药'],
 '[{"name": "韭菜炒鸡蛋", "effect": "温阳养肝", "constitution": "阳虚质/平和质"}, {"name": "山药红枣粥", "effect": "健脾养胃", "constitution": "气虚质/平和质"}]'::jsonb,
 ARRAY['肝', '脾'],
 ARRAY['qi_deficiency', 'yang_deficiency', 'qi_stagnation']
),
('winter_solstice', '冬至', 22, 12, 22, 'winter',
 '冬至一阳生，养生重在补肾藏精，温阳护体。',
 '温补肾阳，多食黑色食物；少食生冷，宜进补。',
 ARRAY['羊肉', '黑芝麻', '黑豆', '核桃', '枸杞', '桂圆', '红枣', '山药', '栗子'],
 '[{"name": "当归生姜羊肉汤", "effect": "温阳补血", "constitution": "阳虚质/气虚质"}, {"name": "黑芝麻核桃粥", "effect": "补肾益精", "constitution": "阴虚质/平和质"}]'::jsonb,
 ARRAY['肾'],
 ARRAY['yang_deficiency', 'qi_deficiency', 'balanced']
);
```

---

### 2.5 `tcm_recommendation_rules` — 食疗推荐规则表

用于程序化生成推荐，减少对 AI 的完全依赖，提升响应速度。

```sql
CREATE TABLE tcm_recommendation_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_type       VARCHAR(30) NOT NULL
                    CHECK (rule_type IN ('constitution', 'season', 'symptom', 'goal', 'menstrual_phase')),
    -- 触发条件
    trigger_key     VARCHAR(50) NOT NULL,           -- e.g. 'qi_deficiency' / 'start_of_spring' / 'fatigue'
    trigger_conditions JSONB DEFAULT '{}',
    -- trigger_conditions: {"min_score": 40, "weather": "cold", ...}
    -- 推荐动作
    action_type     VARCHAR(30) NOT NULL
                    CHECK (action_type IN ('food', 'dish', 'cooking_method', 'avoid', 'tip')),
    action_target   VARCHAR(100) NOT NULL,          -- 目标食物/菜品/方式
    action_params   JSONB DEFAULT '{}',
    -- action_params: {"priority": 1, "meal": "breakfast", "frequency": "daily"}
    -- 推荐文案
    recommendation_text TEXT NOT NULL,              -- "气虚体质建议早餐食用山药红枣粥..."
    -- 适用人群过滤
    suitable_constitutions TEXT[] DEFAULT '{}',
    unsuitable_constitutions TEXT[] DEFAULT '{}',
    -- 优先级与权重
    priority        INT DEFAULT 100,                -- 越小越优先
    weight          DECIMAL(4,2) DEFAULT 1.00,      -- 推荐权重（AI 排序用）
    -- 元信息
    source          VARCHAR(50) DEFAULT 'expert',   -- expert / ai_generated / classical
    verified        BOOLEAN DEFAULT false,
    enabled         BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tcm_rules_type_key ON tcm_recommendation_rules(rule_type, trigger_key);
CREATE INDEX idx_tcm_rules_priority ON tcm_recommendation_rules(priority, weight DESC);
CREATE INDEX idx_tcm_rules_enabled ON tcm_recommendation_rules(enabled) WHERE enabled = true;
```

**预置规则示例：**

```sql
INSERT INTO tcm_recommendation_rules (rule_type, trigger_key, action_type, action_target, recommendation_text, suitable_constitutions, priority, source, verified) VALUES
('constitution', 'qi_deficiency', 'food', '山药', '气虚体质宜常食山药，健脾益胃，补肺固肾。可蒸食、煮粥或煲汤。',
 ARRAY['qi_deficiency'], 10, 'expert', true),
('constitution', 'yang_deficiency', 'avoid', '西瓜', '阳虚体质畏寒怕冷，西瓜性寒，易伤阳气，应尽量避免或少食。',
 ARRAY['yang_deficiency'], 10, 'expert', true),
('season', 'start_of_spring', 'dish', '韭菜炒鸡蛋', '立春时节，阳气初生，韭菜性温味辛，有助温阳养肝，适合春季食用。',
 ARRAY['yang_deficiency', 'qi_deficiency', 'balanced'], 20, 'classical', true),
('menstrual_phase', 'menstrual', 'food', '红糖姜茶', '经期温补驱寒，红糖姜茶可活血化瘀、缓解痛经。',
 ARRAY['yang_deficiency', 'qi_deficiency', 'blood_stasis'], 10, 'expert', true);
```

---

## 3. 现有表的扩展字段

### 3.1 `users` 表增加中医相关预留

```sql
-- 在 users 表中增加一个 tcm_profile 快捷引用（可选，为查询优化）
-- 或通过视图实现，避免冗余字段

CREATE VIEW v_users_with_tcm AS
SELECT
    u.*,
    tcp.primary_constitution,
    tc.name_cn AS primary_constitution_name,
    tcp.assessed_at AS tcm_assessed_at
FROM users u
LEFT JOIN user_tcm_profiles tcp
    ON u.id = tcp.user_id AND tcp.is_current = true
LEFT JOIN tcm_constitutions tc
    ON tcp.primary_constitution = tc.code
WHERE u.deleted_at IS NULL;
```

### 3.2 `meal_plans` 表增加中医维度

```sql
-- 在 meal_plans.generate_params 中预留中医参数
-- 已有 JSONB 结构，扩展如下：
-- {
--   "model": "qwen-plus",
--   "user_request": "今天想吃清淡点",
--   "goal_type": "health",
--   "tcm_constitution": "qi_deficiency",     -- 【新增】用户体质
--   "solar_term": "start_of_spring",          -- 【新增】当前节气
--   "tcm_focus": "健脾益气",                  -- 【新增】调理重点
--   "target_calories": 1580
-- }
```

### 3.3 `ai_chats` 的 context_snapshot 扩展

```sql
-- context_snapshot 扩展中医维度：
-- {
--   "goal_type": "health",
--   "today_calories": 860,
--   "tcm_constitution": "qi_deficiency",       -- 【新增】
--   "solar_term": "winter_solstice",            -- 【新增】
--   "menstrual_phase": "follicular",            -- 【新增】已有
--   "recent_deficiencies": ["iron", "fiber"]
-- }
```

---

## 4. 中医与营养的融合查询视图

### 4.1 食物综合查询视图

```sql
CREATE VIEW v_foods_with_tcm AS
SELECT
    fi.id,
    fi.name,
    fi.category,
    fi.calories,
    fi.protein,
    fi.fat,
    fi.carbs,
    fi.tags,
    ftp.nature,
    ftp.flavors,
    ftp.meridians,
    ftp.effects,
    ftp.suitable_for_constitutions,
    ftp.contraindicated_for_constitutions,
    ftp.contraindications,
    ftp.verified
FROM food_items fi
LEFT JOIN food_tcm_properties ftp ON fi.id = ftp.food_item_id
WHERE fi.deleted_at IS NULL;
```

### 4.2 用户今日中医适宜性评分视图

```sql
CREATE VIEW v_user_diet_tcm_compatibility AS
SELECT
    dr.user_id,
    dr.record_date,
    dr.total_calories,
    fi.name AS food_name,
    ftp.nature,
    CASE
        WHEN ftp.suitable_for_constitutions @> ARRAY[tcp.primary_constitution] THEN 2
        WHEN ftp.contraindicated_for_constitutions @> ARRAY[tcp.primary_constitution] THEN -2
        WHEN ftp.nature = 'neutral' THEN 1
        ELSE 0
    END AS compatibility_score,
    tcp.primary_constitution
FROM diet_records dr
CROSS JOIN LATERAL jsonb_to_recordset(dr.parsed_foods) AS fi(name text)
LEFT JOIN food_items f ON f.name = fi.name
LEFT JOIN food_tcm_properties ftp ON f.id = ftp.food_item_id
LEFT JOIN user_tcm_profiles tcp ON dr.user_id = tcp.user_id AND tcp.is_current = true
WHERE dr.deleted_at IS NULL;
```

---

## 5. 数据填充路线图

| 阶段 | 数据内容 | 量级估算 | 来源 |
|------|---------|---------|------|
| **MVP** | 九种体质定义 + 20 条食物中医属性 + 4 个关键节气 | ~100 条 | 中医专家审核录入 |
| **V1.1** | 100 种常见食物中医属性 | ~100 条 | 古典文献 + 专家 |
| **V1.2** | 二十四节气完整数据 + 推荐食谱 | ~50 条 | 古典文献 |
| **V2.0** | 500+ 食物中医属性 + 食疗规则引擎 | ~500 条 | AI 辅助生成 + 专家审核 |

---

*文档版本：v1.0 | 创建日期：2026-06-07*
