# MealMuse 优化设计文档 v1.0

> 日期: 2026-06-14
> 范围: 5个优化点的完整设计与实现方案

---

## 1. 左下角用户信息卡片

### 1.1 交互设计

- 点击侧边栏底部用户区域 → 弹出 Popover（不跳转）
- Popover 内容:
  - 头像 (emoji) + 昵称 (inline 可编辑)
  - 手机号 (脱敏: 138****1234)
  - 健康目标标签 (如 "🔥 减脂减重")
  - 饮食类型标签 (如 "低碳水")
  - 画像完整度进度条 + 百分比
  - 底部提示: "完善画像，让 AI 更懂你 →" (跳转 onboarding)
  - 操作: 编辑资料 / 退出登录

### 1.2 画像完整度算法

```
基础信息 30%: 昵称+性别+年龄+身高+体重 (每缺一项 -6%)
健康目标 20%: 至少一个 goal (无 -20%)
饮食偏好 30%: 饮食类型(必填)+口味+菜系+忌口 (有2项以上=满)
烹饪条件 10%: 烹饪技能+设备+备餐时间 (有2项=满)
生活方式 10%: 作息+预算 (都有=满)
```

### 1.3 新增 API

- `GET /users/profile/completeness` → `{ score: 75, missing: ["age", "goals"], hint: "完善画像..." }`

### 1.4 文件改动

| 文件 | 改动 |
|------|------|
| `components/sidebar.tsx` | 加 Popover + UserInfoCard 组件 |
| `app/api/v1/users.py` | 加 completeness 端点 |
| `components/user-info-card.tsx` | 新建组件 |

---

## 2. 专业版 Onboarding (6步)

### 2.1 步骤设计

**Step 1: 基础信息** (保持)
身高/体重/年龄/性别/目标体重

**Step 2: 健康目标** (增强)
```
🔥 减脂减重 → 子选: 速减 / 慢减 / 塑形
🌸 备孕调理 → 子选: 备孕中 / 孕早期 / 孕中期 / 孕晚期 / 哺乳期
🧘 养生保健 → 子选: 气血不足 / 脾胃调理 / 补肾 / 护肝 / 安神助眠
💪 增肌塑形 → 子选: 增肌 / 减脂塑形 / 运动恢复
🩺 慢病管理 → 新增: 糖尿病 / 高血压 / 高血脂 / 痛风 / 胃病
```

**Step 3: 体质辨识** (新增)
中医九种体质，每个有自测问题:
- ☀️ 阳虚质: 怕冷/手脚凉/喜热饮/容易腹泻
- 🔥 阴虚质: 口干/手心热/易上火/盗汗
- 💨 气虚质: 乏力/气短/易感冒/说话声音低
- 🩸 血瘀质: 皮肤暗沉/易瘀青/痛经/唇色暗
- 🌊 痰湿质: 体胖/痰多/面部油腻/身重不爽
- 🌿 湿热质: 面垢油光/口苦/长痘/小便黄
- 😰 气郁质: 情绪低落/胸闷叹气/多愁善感
- ❄️ 特禀质: 过敏体质/易打喷嚏/皮肤易痒
- ⚖️ 平和质: 正常体质 (不需要调理)

交互: 点击体质卡片选中 (可多选)，选中后显示2-3个确认问题 (是/否/不确定)

**Step 4: 饮食偏好** (增强)
- 饮食类型 + 口味 + 菜系 + 过敏忌口 (保持)
- 新增: 偏好食材 (标签选择: 鸡胸肉/三文鱼/豆腐/牛肉/虾/鸡蛋/牛奶...)
- 新增: 不喜欢吃的菜 (自由输入)
- 新增过敏原: 酒精/蜂蜜/芝麻/芒果/芹菜/亚硫酸盐

**Step 5: 烹饪与生活** (合并)
- 烹饪技能/设备/备餐时间/就餐模式
- 作息习惯/预算水平/饮水目标
- 新增: 每周做饭频次 (天天做/3-5次/偶尔/从不)
- 新增: 外卖偏好 (营养轻食/家常菜/快餐/都行)

**Step 6: 家庭成员** (新增)
- 是否为家人做饭: 是/否
- 是 → 添加家庭成员: 昵称+关系+年龄段+饮食注意
- 关系选项: 老公/老婆/孩子/父母/公婆/其他
- 年龄段: 0-3岁/3-6岁/6-12岁/12-18岁/18-60岁/60岁以上
- 饮食注意: 无特殊/低盐/低糖/补钙/补铁/易消化/其他

### 2.2 数据库改动

`user_profiles` 表新增字段:
```sql
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS constitution_types JSONB DEFAULT '[]';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS health_sub_goals JSONB DEFAULT '[]';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS preferred_ingredients JSONB DEFAULT '[]';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS cooking_frequency VARCHAR(20) DEFAULT 'often';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS takeout_preference VARCHAR(20) DEFAULT 'any';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS family_cooking BOOLEAN DEFAULT false;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS family_members JSONB DEFAULT '[]';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS onboarding_version INTEGER DEFAULT 2;
```

### 2.3 文件改动

| 文件 | 改动 |
|------|------|
| `app/onboarding/page.tsx` | 重写为6步，增加体质辨识、家庭成员步骤 |
| `app/models/user_profile.py` | 增加新字段 |
| `app/schemas/user.py` | 增加 OnboardingRequest 新字段 |
| `app/api/v1/users.py` | 更新 onboarding 端点 |

---

## 3. 用户画像核心资产

### 3.1 画像摘要机制

context_builder.py 新增 `get_profile_summary()`:
- 生成100-150字紧凑摘要
- 缓存到 Redis，key: `profile_summary:{user_id}`，TTL 24h
- 画像变更时 (PUT /users/profile/full) 清除缓存
- 格式示例:
  ```
  女28岁阳虚+气虚质，备孕中需补叶酸，偏好川菜忌海鲜香菜，
  低碳水饮食，为3口人做饭(老人高血压低盐)，
  近7天日均1400kcal，最近吃了番茄炒蛋×3
  ```

### 3.2 画像质量评分

```python
def calculate_profile_score(user, profile, goals, allergies, conditions) -> dict:
    score = 0
    missing = []
    
    # 基础信息 30%
    base_fields = {'nickname': user.nickname, 'gender': user.gender, 
                   'age': user.age, 'height_cm': user.height_cm, 'current_weight': user.current_weight}
    filled = sum(1 for v in base_fields.values() if v)
    base_score = int((filled / len(base_fields)) * 30)
    score += base_score
    missing.extend(k for k, v in base_fields.items() if not v)
    
    # 健康目标 20%
    if goals:
        score += 20
    else:
        missing.append('goals')
    
    # 饮食偏好 30%
    diet_count = sum(1 for attr in ['diet_type', 'taste_preference', 'cuisine_preference', 'disliked_foods']
                     if getattr(profile, attr, None))
    score += min(30, int((diet_count / 2) * 30))
    
    # 烹饪条件 10%
    cook_count = sum(1 for attr in ['cooking_method', 'cooking_facility', 'meal_prep_time']
                     if getattr(profile, attr, None))
    score += min(10, int((cook_count / 2) * 10))
    
    # 生活方式 10%
    life_count = sum(1 for attr in ['sleep_pattern', 'budget_level'] if getattr(profile, attr, None))
    score += min(10, int((life_count / 2) * 10))
    
    # 提示文案
    if score < 60:
        hint = "画像不完整，AI 建议可能不够精准"
    elif score < 80:
        hint = "画像基本完整，完善更多让推荐更精准"
    else:
        hint = "画像很完整，AI 正在提供最佳建议"
    
    return {'score': min(100, score), 'missing': missing, 'hint': hint}
```

### 3.3 体质→食材推荐映射

```python
CONSTITUTION_FOOD_MAP = {
    "yang_deficiency": {  # 阳虚质
        "recommend": ["羊肉", "牛肉", "生姜", "桂圆", "红枣", "韭菜", "核桃"],
        "avoid": ["西瓜", "冷饮", "苦瓜", "绿豆", "螃蟹"],
        "note": "宜温补，忌寒凉"
    },
    "yin_deficiency": {  # 阴虚质
        "recommend": ["银耳", "百合", "莲子", "枸杞", "鸭肉", "甲鱼"],
        "avoid": ["辣椒", "羊肉", "榴莲", "酒"],
        "note": "宜滋阴润燥，忌辛温燥热"
    },
    "qi_deficiency": {  # 气虚质
        "recommend": ["黄芪", "党参", "山药", "鸡肉", "小米", "红枣"],
        "avoid": ["萝卜", "薄荷", "空心菜"],
        "note": "宜补气健脾，忌耗气食物"
    },
    "phlegm_dampness": {  # 痰湿质
        "recommend": ["薏仁", "冬瓜", "白萝卜", "荷叶茶", "山楂"],
        "avoid": ["甜食", "肥肉", "酒", "糯米"],
        "note": "宜健脾化湿，忌甜腻肥厚"
    },
    "damp_heat": {  # 湿热质
        "recommend": ["绿豆", "苦瓜", "薏仁", "莲藕", "黄瓜"],
        "avoid": ["羊肉", "辣椒", "酒", "芒果", "榴莲"],
        "note": "宜清热化湿，忌辛温滋腻"
    },
    "blood_stasis": {  # 血瘀质
        "recommend": ["山楂", "黑木耳", "洋葱", "玫瑰花茶", "醋"],
        "avoid": ["寒凉食物"],
        "note": "宜活血化瘀"
    },
    "qi_stagnation": {  # 气郁质
        "recommend": ["玫瑰花", "佛手", "柑橘", "萝卜", "山药"],
        "avoid": ["浓茶", "咖啡（过量）"],
        "note": "宜疏肝理气"
    },
}
```

### 3.4 文件改动

| 文件 | 改动 |
|------|------|
| `app/services/context_builder.py` | 增加体质映射、画像摘要、增强注入 |
| `app/api/v1/users.py` | 增加 completeness 端点、画像更新清缓存 |

---

## 4. AI 对话 + 餐食计划画像融合

### 4.1 对话增强

- 每次对话开头注入画像摘要 (100-150字固定开销)
- 对话摘要机制: 历史超20条时 LLM 生成前情摘要
- 对话 Action (v2): "我吃了碗面"→记录, "不吃香菜了"→更新画像

### 4.2 餐食计划关键改造

`meal_plan_engine.py` 改动:

1. **注入近期饮食去重**
```python
recent_foods = await _get_recent_food_names(db, user.id, days=3)
# prompt 中加: "用户近3天已吃过: {recent_foods}，请不要重复推荐"
```

2. **注入家庭成员餐食需求**
```python
family_needs = await _get_family_needs(db, user.id)
# prompt 中加: "需为家庭成员一起做饭: {family_needs}，每餐要兼顾所有人口味和禁忌"
```

3. **营养追踪补缺**
```python
nutrient_balance = await _get_nutrient_balance(db, user.id, days=3)
# "近3天维生素A摄入充足可降权重，铁摄入不足需优先补充"
```

### 4.3 文件改动

| 文件 | 改动 |
|------|------|
| `app/services/meal_plan_engine.py` | 增加近期饮食、家庭餐食、营养追踪 |
| `app/services/context_builder.py` | 增加画像摘要 |
| `app/agents/chat_agent.py` | 注入画像摘要 |

---

## 5. MCP 平台接入

### 5.1 接入方案

使用 FastMCP 自建 MCP Server，封装外部 API:

**P0: Spoonacular + Open Food Facts**
- `food_search` 工具: 搜索菜谱
- `nutrition_lookup` 工具: 查食品营养
- `ingredient_substitute` 工具: 食材替代

**P1: 天气 + 地图**
- `weather` 工具: 查天气→推荐饮食
- `nearby_restaurant` 工具: 附近健康餐厅

### 5.2 架构

```
用户提问
  ↓
ChatAgent / MealAgent
  ↓
MCPRouter.route(message, context)
  ├→ food_search → Spoonacular API
  ├→ nutrition_lookup → Open Food Facts API
  ├→ weather → 和风天气/wttr.in
  ├→ nearby → 高德地图
  └→ 内部知识库 (ChromaDB)
  ↓
合并结果 → LLM 生成
```

### 5.3 文件改动

| 文件 | 改动 |
|------|------|
| `app/mcp/client.py` | 新建，MCP 通用客户端 |
| `app/mcp/router.py` | 新建，意图路由 |
| `app/mcp/servers/food.py` | 新建，Spoonacular 封装 |
| `app/mcp/servers/nutrition.py` | 新建，Open Food Facts 封装 |

---

## 实施顺序

1. ✅ 设计文档写入项目目录
2. 🔄 **P0: 后端画像增强** (user_profile model + schema + API)
3. 🔄 **P0: Onboarding 6步前端** (page.tsx 重写)
4. 🔄 **P0: Context Builder 增强** (体质映射+画像摘要)
5. 🔄 **P0: 餐食计划改造** (去重+家庭餐+营养追踪)
6. 🔄 **P1: 用户信息卡片** (sidebar Popover)
7. 🔄 **P2: MCP 接入** (food_search + nutrition)
