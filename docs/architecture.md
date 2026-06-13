# MealMuse 技术架构设计

> 版本：v1.0 | 创建日期：2026-06-07

---

## 1. 技术选型

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | Next.js 14+ (App Router) | React 生态，SSR/SSG，SEO 友好 |
| **UI 框架** | Tailwind CSS + shadcn/ui | 原子化 CSS + 高质量组件库 |
| **后端** | Python FastAPI | 异步高性能，AI 生态天然友好 |
| **数据库** | PostgreSQL 16 | 成熟可靠，JSONB 支持灵活数据 |
| **ORM** | SQLAlchemy 2.0 + Alembic | 异步 ORM + 数据库迁移 |
| **AI 模型** | 通义千问 (qwen-plus) | 阿里云，中文理解强，成本可控 |
| **认证** | JWT + 手机验证码 | 无状态认证 |
| **缓存** | Redis | 会话缓存、AI 上下文缓存 |
| **部署** | Docker + 阿里云 ECS | 容器化部署 |
| **CI/CD** | GitHub Actions | 自动化构建部署 |

---

## 2. 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端 (Browser)                       │
│                    Next.js + Tailwind CSS                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Nginx (反向代理)                          │
│                 SSL 终止 / 负载均衡 / 静态资源                  │
└──────────┬─────────────────────────────┬────────────────────┘
           │                             │
           ▼                             ▼
┌─────────────────────┐     ┌─────────────────────────────────┐
│   Next.js Server    │     │      FastAPI Backend             │
│   (前端 SSR/API)    │     │                                  │
│                     │     │  ┌───────────┐ ┌──────────────┐ │
│  - 页面渲染         │     │  │ Auth 模块  │ │ Diet 模块    │ │
│  - BFF 层 (可选)    │     │  │ 登录/注册  │ │ 饮食记录     │ │
│  - 静态资源         │     │  └───────────┘ │ 营养分析     │ │
│                     │     │                └──────────────┘ │
└─────────────────────┘     │  ┌───────────┐ ┌──────────────┐ │
                            │  │ Meal 模块  │ │ Chat 模块    │ │
                            │  │ 餐食生成   │ │ AI 对话      │ │
                            │  └───────────┘ └──────────────┘ │
                            │  ┌───────────┐ ┌──────────────┐ │
                            │  │ Report 模块│ │ AI Service   │ │
                            │  │ 统计报告   │ │ 通义千问 API  │ │
                            │  └───────────┘ └──────────────┘ │
                            └──────────────┬──────────────────┘
                                           │
                    ┌──────────────────────┼──────────────────┐
                    │                      │                  │
                    ▼                      ▼                  ▼
           ┌──────────────┐     ┌──────────────┐    ┌──────────────┐
           │ PostgreSQL   │     │    Redis     │    │ 通义千问 API │
           │              │     │              │    │              │
           │ - users      │     │ - 会话缓存   │    │ - Chat       │
           │ - diet_record│     │ - AI 上下文  │    │ - 食物解析   │
           │ - meal_plans │     │ - 限流计数   │    │ - 餐食生成   │
           │ - ai_chats   │     └──────────────┘    └──────────────┘
           └──────────────┘
```

---

## 3. API 设计

### 3.1 认证相关

| Method | Endpoint | 说明 |
|--------|----------|------|
| POST | `/api/v1/auth/send-code` | 发送手机验证码 |
| POST | `/api/v1/auth/login` | 手机号+验证码登录 |
| POST | `/api/v1/auth/wechat` | 微信登录 |
| POST | `/api/v1/auth/refresh` | 刷新 Token |
| GET | `/api/v1/auth/me` | 获取当前用户信息 |

### 3.2 用户 & 目标

| Method | Endpoint | 说明 |
|--------|----------|------|
| GET | `/api/v1/users/profile` | 获取个人资料 |
| PUT | `/api/v1/users/profile` | 更新个人资料 |
| GET | `/api/v1/goals` | 获取健康目标 |
| POST | `/api/v1/goals` | 创建/更新健康目标 |

### 3.3 饮食记录

| Method | Endpoint | 说明 |
|--------|----------|------|
| POST | `/api/v1/diet/records` | 创建饮食记录（自然语言输入） |
| GET | `/api/v1/diet/records` | 获取记录列表（支持日期筛选） |
| GET | `/api/v1/diet/records/{id}` | 获取单条记录详情 |
| PUT | `/api/v1/diet/records/{id}` | 修改记录 |
| DELETE | `/api/v1/diet/records/{id}` | 删除记录 |
| GET | `/api/v1/diet/today` | 获取今日饮食汇总 |

### 3.4 餐食计划

| Method | Endpoint | 说明 |
|--------|----------|------|
| GET | `/api/v1/meals/plan?date=2026-06-07` | 获取指定日期的餐食计划 |
| POST | `/api/v1/meals/generate` | 生成今日三餐计划 |
| POST | `/api/v1/meals/{meal_id}/replace` | 替换某一餐 |
| POST | `/api/v1/meals/{meal_id}/adjust` | 调整某一餐（用户偏好） |

### 3.5 AI 对话

| Method | Endpoint | 说明 |
|--------|----------|------|
| POST | `/api/v1/chat/send` | 发送消息（普通响应） |
| GET | `/api/v1/chat/sessions` | 获取对话历史列表 |
| GET | `/api/v1/chat/sessions/{id}` | 获取某次对话详情 |
| DELETE | `/api/v1/chat/sessions/{id}` | 删除对话 |

### 3.6 报告

| Method | Endpoint | 说明 |
|--------|----------|------|
| GET | `/api/v1/reports/daily?date=2026-06-07` | 每日报告 |
| GET | `/api/v1/reports/weekly?week=2026-W23` | 每周报告 |
| GET | `/api/v1/reports/monthly?month=2026-06` | 每月报告 |

### 3.7 请求/响应示例

#### 创建饮食记录

```json
// POST /api/v1/diet/records
// Request
{
  "meal_type": "lunch",
  "food_text": "中午吃了一碗红烧牛肉面，一个苹果，一杯酸奶",
  "recorded_at": "2026-06-07T12:30:00+08:00"
}

// Response
{
  "id": "rec_abc123",
  "meal_type": "lunch",
  "food_text": "中午吃了一碗红烧牛肉面，一个苹果，一杯酸奶",
  "parsed_foods": [
    {"name": "红烧牛肉面", "amount": "1碗", "calories": 520, "protein": 25, "fat": 18, "carbs": 62},
    {"name": "苹果", "amount": "1个", "calories": 85, "protein": 0.4, "fat": 0.2, "carbs": 22},
    {"name": "酸奶", "amount": "1杯(200ml)", "calories": 130, "protein": 6, "fat": 4, "carbs": 18}
  ],
  "total_calories": 735,
  "nutrients": {
    "protein": 31.4,
    "fat": 22.2,
    "carbs": 102,
    "fiber": 4.2
  },
  "ai_analysis": "午餐热量 735kcal，蛋白质摄入充足。建议晚餐适当减少碳水，增加蔬菜摄入。",
  "recorded_at": "2026-06-07T12:30:00+08:00"
}
```

#### 生成餐食计划

```json
// POST /api/v1/meals/generate
// Request
{
  "date": "2026-06-07",
  "preferences": "今天想吃清淡一点"
}

// Response
{
  "date": "2026-06-07",
  "total_calories": 1580,
  "breakfast": {
    "name": "元气早餐",
    "foods": [
      {"name": "小米粥", "amount": "1碗", "calories": 120},
      {"name": "水煮蛋", "amount": "2个", "calories": 140},
      {"name": "凉拌黄瓜", "amount": "1份", "calories": 30}
    ],
    "total_calories": 290,
    "nutrients": {"protein": 18, "fat": 10, "carbs": 32}
  },
  "lunch": {
    "name": "均衡午餐",
    "foods": [
      {"name": "清蒸鲈鱼", "amount": "1份", "calories": 180},
      {"name": "西兰花炒虾仁", "amount": "1份", "calories": 120},
      {"name": "糙米饭", "amount": "1碗", "calories": 220}
    ],
    "total_calories": 520,
    "nutrients": {"protein": 42, "fat": 12, "carbs": 55}
  },
  "dinner": {
    "name": "轻食晚餐",
    "foods": [
      {"name": "番茄豆腐汤", "amount": "1碗", "calories": 80},
      {"name": "蒜蓉菠菜", "amount": "1份", "calories": 40},
      {"name": "玉米", "amount": "1根", "calories": 110},
      {"name": "鸡胸肉沙拉", "amount": "1份", "calories": 250}
    ],
    "total_calories": 480,
    "nutrients": {"protein": 35, "fat": 8, "carbs": 48}
  },
  "ai_note": "今天推荐清淡饮食，总热量 1580kcal，适合您的减重目标。蛋白质充足，碳水适中。"
}
```

---

## 4. AI 集成方案

### 4.1 模型选择策略

```python
# 多模型支持，可切换
AI_MODELS = {
    "primary": {
        "name": "qwen-plus",           # 通义千问 - 主力模型
        "provider": "alibaba",
        "max_tokens": 8192,
        "cost_per_1k": 0.004,           # 元/千 tokens
    },
    "fallback": {
        "name": "ernie-3.5-8k",         # 文心一言 - 备选
        "provider": "baidu",
        "max_tokens": 8192,
        "cost_per_1k": 0.008,
    },
    "lightweight": {
        "name": "qwen-turbo",           # 轻量任务
        "provider": "alibaba",
        "max_tokens": 8192,
        "cost_per_1k": 0.001,
    }
}
```

### 4.2 Prompt 设计

#### 食物解析 Prompt

```
你是一个专业的营养师助手。请解析用户输入的饮食描述，提取每种食物的名称、份量和营养成分。

用户输入：{food_text}

请以 JSON 格式返回：
{
  "foods": [
    {
      "name": "食物名称",
      "amount": "估算份量",
      "calories": 热量(kcal),
      "protein": 蛋白质(g),
      "fat": 脂肪(g),
      "carbs": 碳水化合物(g),
      "fiber": 膳食纤维(g)
    }
  ],
  "total_calories": 总热量,
  "analysis": "简要分析(50字内)"
}
```

#### 餐食生成 Prompt

```
你是一个专业的营养师，正在为用户制定今日三餐方案。

用户信息：
- 目标：{goal_type}（如：减重/备孕/养生）
- 身体数据：身高 {height}cm，体重 {weight}kg，年龄 {age}
- 饮食偏好：{preferences}
- 今日特殊要求：{user_request}
- 最近 3 天饮食摘要：{recent_diet_summary}

请生成今日三餐方案，要求：
1. 总热量控制在 {target_calories} kcal 左右
2. 营养均衡，蛋白质/脂肪/碳水比例合理
3. 考虑最近饮食，避免重复
4. 食材常见、做法简单
5. 如有备孕/养生需求，重点推荐相关食材

以 JSON 格式返回三餐方案。
```

#### AI 对话 System Prompt

```
你是 MealMuse，一个专业的 AI 饮食健康助手。

你的职责：
1. 基于用户的饮食记录，提供个性化的饮食建议
2. 回答健康饮食相关问题
3. 帮助用户达成健康目标（减肥/备孕/养生等）

当前用户信息：
- 健康目标：{goal_type}
- 身体数据：{body_info}
- 今日饮食记录：{today_records}
- 近 7 天饮食摘要：{weekly_summary}

重要规则：
1. 只提供饮食和营养相关建议，不提供医疗诊断
2. 如果用户询问医疗问题，建议咨询专业医生
3. 建议要具体、可执行，避免空泛
4. 语气友好、鼓励，像一个贴心的健康伙伴
5. 如果用户的饮食有问题，温和地指出并给出替代方案
```

### 4.3 AI 调用流程

```
用户输入
    │
    ▼
┌──────────────────┐
│  构建 Context    │
│  - 用户画像      │
│  - 近期饮食      │
│  - 健康目标      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────┐
│  Redis 缓存检查   │────▶│ 有缓存？     │
└────────┬─────────┘     │  是 → 直接用  │
         │ 否            └──────────────┘
         ▼
┌──────────────────┐
│  调用通义千问 API  │
│  - System Prompt  │
│  - Context        │
│  - 用户消息       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  输出安全检查     │
│  - 医疗建议过滤   │
│  - 敏感词检测     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  返回给前端       │
│  + 存入数据库     │
│  + 更新缓存       │
└──────────────────┘
```

---

## 5. 项目结构

### 5.1 前端 (Next.js)

```
meal-muse-web/
├── app/                        # Next.js App Router
│   ├── (auth)/                 # 认证相关页面组
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (main)/                 # 主要页面组
│   │   ├── page.tsx            # 首页 - 今日餐食
│   │   ├── record/page.tsx     # 饮食记录
│   │   ├── plan/page.tsx       # 餐食计划
│   │   ├── chat/page.tsx       # AI 对话
│   │   ├── report/page.tsx     # 健康报告
│   │   └── profile/page.tsx    # 个人中心
│   ├── layout.tsx              # 根布局
│   └── globals.css
├── components/                 # 组件库
│   ├── ui/                     # shadcn/ui 基础组件
│   ├── meal-card.tsx           # 餐食卡片
│   ├── diet-input.tsx          # 饮食输入框
│   ├── chat-bubble.tsx         # 对话气泡
│   ├── nutrient-chart.tsx      # 营养图表
│   └── daily-summary.tsx       # 每日摘要
├── lib/                        # 工具库
│   ├── api.ts                  # API 请求封装
│   ├── auth.ts                 # 认证逻辑
│   └── utils.ts                # 工具函数
├── hooks/                      # 自定义 Hooks
│   ├── use-auth.ts
│   ├── use-diet.ts
│   └── use-chat.ts
├── stores/                     # 状态管理 (Zustand)
│   ├── auth-store.ts
│   └── diet-store.ts
└── types/                      # 类型定义
    ├── user.ts
    ├── diet.ts
    └── meal.ts
```

### 5.2 后端 (FastAPI)

```
meal-muse-api/
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   ├── api/                    # API 路由
│   │   ├── v1/
│   │   │   ├── auth.py         # 认证接口
│   │   │   ├── users.py        # 用户接口
│   │   │   ├── diet.py         # 饮食记录接口
│   │   │   ├── meals.py        # 餐食计划接口
│   │   │   ├── chat.py         # AI 对话接口
│   │   │   └── reports.py      # 报告接口
│   │   └── deps.py             # 依赖注入
│   ├── models/                 # 数据库模型
│   │   ├── user.py
│   │   ├── diet_record.py
│   │   ├── meal_plan.py
│   │   └── ai_chat.py
│   ├── schemas/                # Pydantic Schema
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── diet.py
│   │   ├── meal.py
│   │   └── chat.py
│   ├── services/               # 业务逻辑
│   │   ├── auth_service.py
│   │   ├── diet_service.py
│   │   ├── meal_service.py
│   │   ├── chat_service.py
│   │   └── ai_service.py       # AI 模型调用封装
│   ├── core/                   # 核心模块
│   │   ├── security.py         # JWT / 密码
│   │   ├── database.py         # 数据库连接
│   │   └── redis.py            # Redis 连接
│   └── utils/                  # 工具函数
│       ├── nutrition.py        # 营养计算
│       └── food_db.py          # 食物数据库
├── alembic/                    # 数据库迁移
├── tests/                      # 测试
├── Dockerfile
└── requirements.txt
```

---

## 6. 部署方案

### 6.1 架构

```
┌─────────────────────────────────────────────────────┐
│                  阿里云 ECS (2C4G)                   │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Nginx     │  │  Next.js    │  │   FastAPI   │ │
│  │  :80/:443   │  │   :3000     │  │   :8000     │ │
│  └──────┬──────┘  └─────────────┘  └──────┬──────┘ │
│         │                                  │        │
│         └──────────────┬───────────────────┘        │
│                        │                            │
│  ┌─────────────────────┼─────────────────────┐      │
│  │              Docker Network               │      │
│  │  ┌───────────┐  ┌───────────┐            │      │
│  │  │ PostgreSQL │  │   Redis   │            │      │
│  │  │   :5432   │  │   :6379   │            │      │
│  │  └───────────┘  └───────────┘            │      │
│  └───────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

### 6.2 Docker Compose

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

  frontend:
    build: ./meal-muse-web
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000

  backend:
    build: ./meal-muse-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/mealmuse
      - REDIS_URL=redis://redis:6379/0
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=mealmuse
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

---

## 7. 安全设计

| 层面 | 措施 |
|------|------|
| **传输** | 全站 HTTPS，TLS 1.3 |
| **认证** | JWT + Refresh Token，Access Token 30min 过期 |
| **数据** | 用户密码 bcrypt 加密，敏感字段 AES 加密 |
| **API** | 限流（60 次/分钟），CORS 白名单 |
| **AI** | 输出内容安全过滤，Prompt 注入防护 |
| **隐私** | 健康数据加密存储，数据脱敏日志 |

---

*文档版本：v1.0 | 创建日期：2026-06-07*
