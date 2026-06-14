# MealMuse 开发规范

## 项目架构

```
meal-muse/                    # 根目录
├── meal-muse-api/            # 后端 — FastAPI + PostgreSQL
│   ├── app/
│   │   ├── api/v1/           # 路由层（参数校验 + 调 service）
│   │   ├── services/         # 业务逻辑层
│   │   ├── repositories/     # 数据访问层（泛型 CRUD）
│   │   ├── agents/           # Agent 架构（对话/推理）
│   │   ├── models/           # SQLAlchemy ORM
│   │   ├── schemas/          # Pydantic 校验
│   │   └── core/             # 基础设施（database/security/exceptions）
│   ├── scripts/              # 管理脚本
│   └── .env                  # 环境配置（不入库）
├── meal-muse-web/            # 前端 — Next.js 16 + React 19
│   ├── app/                  # App Router 页面
│   ├── components/ui/        # UI 组件库
│   ├── stores/               # Zustand 状态管理
│   ├── lib/                  # 通用工具（api.ts 等）
│   └── types/                # TypeScript 类型定义
└── docs/plans/               # 设计方案文档
```

## 后端规范

### 分层职责
- **路由层** (`api/v1/`)：只做参数校验、调用 service、返回 response。不写业务逻辑。
- **服务层** (`services/`)：业务逻辑编排。一个函数对应一个用例。
- **仓储层** (`repositories/`)：数据库查询封装，继承 `BaseRepository[ModelT]`。
- **Agent 层** (`agents/`)：AI 对话/推理流程，使用 PromptRegistry 管理 prompt。
- **模型层** (`models/`)：SQLAlchemy 声明式模型，只做表映射。

### 命名规范
- 路由函数：`create_record` / `list_records` / `get_record` / `update_record` / `delete_record`
- service 函数：动词 + 名词，如 `parse_food_text` / `chat_send`
- repository 类：`XxxRepository`，方法 `get_by_id` / `find_by_user` / `create` / `update`
- 文件/类/变量：全小写 + 下划线（snake_case）

### 错误处理
- 自定义异常在 `core/exceptions.py`：`AppException` / `NotFoundError` / `BadRequestError` / `UnauthorizedError` / `AIServiceError`
- 路由中不要写 try-catch，抛异常即可（`register_exception_handlers` 全局捕获）

### 日志
- 使用 `logging.getLogger(__name__)`，不用 print
- 关键操作（AI 调用、数据库变更）加 info 日志
- 异常在 service/agent 层记录，上层不需要重复记

### AI 调用
- 基础调用用 `ai_service.call_ai()`，结构化调用用 `call_ai_structured()`
- **对话走 Agent**（`ChatAgent`），包含 prompt 模板 + 历史 + 知识库检索
- **简单 AI 调用**（食物解析、餐食计划）直接调 `ai_service`，不走 agent
- 多提供商通过 .env 的 `AI_PROVIDER` 切换

## 前端规范

### 组件组织
- `components/ui/`：通用 UI 组件（button/modal/toast/confirm等）
- 页面组件放在 `app/(main)/xxx/page.tsx`
- 复杂页面抽局部组件到页面同级或 `components/` 下

### 状态管理
- 全局状态用 Zustand（`stores/` 目录）
- 局部状态用 React useState / useReducer
- API 调用通过 `lib/api.ts`（axios 实例，自动带 token + 401 跳转）

### UI 组件使用
- 弹窗：`components/ui/modal.tsx` 的 `<Modal>` 组件
- 确认框：`confirm({ title, message, type })` 替代 `window.confirm()`
- 提示：`toast("success", "消息")` 替代 `alert()`
- 按钮：`<Button variant="primary" size="md" loading>`
- 错误展示：`<ErrorMessage type="error" title="" message="" />`

### 样式
- Tailwind CSS v4（`@import "tailwindcss"`）
- CSS 变量在 `globals.css` 定义（`--primary`, `--text-primary` 等）
- 颜色用 CSS 变量或 Tailwind 内置色，尽量少用硬编码色值

## 提交规范

提交信息格式：`<type>: <简短描述>`

类型：
- `feat:` 新功能
- `fix:` 修复
- `refactor:` 重构
- `style:` UI/样式变更
- `docs:` 文档
- `chore:` 工具/配置变更

## 当前进度

项目处于早期开发阶段，主要功能：
- [x] 用户认证（短信验证码登录）
- [x] 饮食记录 + AI 营养解析
- [x] AI 对话（ChatAgent + 知识库）
- [x] 餐食计划生成
- [x] 身体数据追踪
- [x] 经期追踪
- [x] 家庭共享
- [x] 健康报告
- [x] 多模型 AI 支持（dashscope/xiaomi/openai/custom）
- [ ] 离线支持
- [ ] 桌面端 UI 布局增强
