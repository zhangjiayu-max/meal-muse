# MealMuse PWA 离线策略与多模态/状态设计稿

> 版本：v1.0 | 创建日期：2026-06-07 | 对应：ui-design.md 与 architecture.md 的扩展补充
>
> **设计目标：** (1) 让 MealMuse 在弱网/离线环境下核心功能可用；(2) 补充拍照/语音等多模态输入入口；(3) 完善深色模式、空态、错误态等边缘状态设计。

---

## 1. PWA 整体架构

### 1.1 PWA 能力矩阵

| 功能 | 在线 | 弱网 | 离线 | 同步时机 |
|------|------|------|------|----------|
| 查看今日餐食计划 | ✅ | ✅ (缓存) | ✅ (缓存) | 联网时自动刷新 |
| 自然语言饮食记录 | ✅ | ✅ (本地队列) | ✅ (本地队列) | 恢复网络后后台同步 |
| AI 营养分析 | ✅ | ❌ | ❌ | - |
| AI 对话 | ✅ | ❌ | ❌ | - |
| 查看历史记录 | ✅ | ✅ (IndexedDB) | ✅ (IndexedDB) | 已本地存储 |
| 查看健康报告 | ✅ | ✅ (缓存) | ⚠️ (截至上次缓存) | 联网时更新 |
| 修改个人资料 | ✅ | ✅ (本地队列) | ✅ (本地队列) | 恢复网络后同步 |

### 1.2 Web App Manifest

```json
// public/manifest.json
{
  "name": "MealMuse - AI 饮食健康助手",
  "short_name": "MealMuse",
  "description": "每一餐，都是对自己的善待",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FAFAFA",
  "theme_color": "#22C55E",
  "orientation": "portrait-primary",
  "scope": "/",
  "icons": [
    { "src": "/icons/icon-72x72.png", "sizes": "72x72", "type": "image/png", "purpose": "maskable any" },
    { "src": "/icons/icon-96x96.png", "sizes": "96x96", "type": "image/png", "purpose": "maskable any" },
    { "src": "/icons/icon-128x128.png", "sizes": "128x128", "type": "image/png", "purpose": "maskable any" },
    { "src": "/icons/icon-144x144.png", "sizes": "144x144", "type": "image/png", "purpose": "maskable any" },
    { "src": "/icons/icon-152x152.png", "sizes": "152x152", "type": "image/png", "purpose": "maskable any" },
    { "src": "/icons/icon-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable any" },
    { "src": "/icons/icon-384x384.png", "sizes": "384x384", "type": "image/png", "purpose": "maskable any" },
    { "src": "/icons/icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable any" }
  ],
  "screenshots": [
    { "src": "/screenshots/home-mobile.png", "sizes": "750x1334", "type": "image/png", "form_factor": "narrow" },
    { "src": "/screenshots/home-desktop.png", "sizes": "1920x1080", "type": "image/png", "form_factor": "wide" }
  ],
  "categories": ["health", "food", "lifestyle"],
  "lang": "zh-CN",
  "dir": "ltr",
  "shortcuts": [
    {
      "name": "快速记录",
      "short_name": "记录",
      "description": "快速记录今日饮食",
      "url": "/record?action=quick",
      "icons": [{ "src": "/icons/shortcut-record.png", "sizes": "96x96" }]
    },
    {
      "name": "今日计划",
      "short_name": "计划",
      "description": "查看今日三餐推荐",
      "url": "/plan",
      "icons": [{ "src": "/icons/shortcut-plan.png", "sizes": "96x96" }]
    }
  ]
}
```

### 1.3 Service Worker 缓存策略

```typescript
// public/sw.ts (Workbox 策略)
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { BackgroundSyncPlugin } from 'workbox-background-sync';

// 预缓存：构建时的静态资源
precacheAndRoute(self.__WB_MANIFEST);
cleanupOutdatedCaches();

// 策略 1：静态资源 (JS/CSS/字体) → Cache First + 后台更新
registerRoute(
  ({ request }) =>
    request.destination === 'script' ||
    request.destination === 'style' ||
    request.destination === 'font',
  new CacheFirst({
    cacheName: 'static-assets',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30天
      }),
    ],
  })
);

// 策略 2：页面路由 → Network First（保证内容最新，离线回退缓存）
registerRoute(
  ({ url }) => url.pathname.startsWith('/'),
  new NetworkFirst({
    cacheName: 'pages',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 7 * 24 * 60 * 60, // 7天
      }),
    ],
  })
);

// 策略 3：图片资源 → Stale While Revalidate
registerRoute(
  ({ request }) => request.destination === 'image',
  new StaleWhileRevalidate({
    cacheName: 'images',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 200,
        maxAgeSeconds: 30 * 24 * 60 * 60,
      }),
    ],
  })
);

// 策略 4：API 调用（饮食记录提交）→ 后台同步
const bgSyncPlugin = new BackgroundSyncPlugin('diet-record-queue', {
  maxRetentionTime: 24 * 60, // 24小时
  onSync: async ({ queue }) => {
    let entry;
    while ((entry = await queue.shiftRequest())) {
      try {
        await fetch(entry.request);
        // 成功后通知前端刷新
        const clients = await self.clients.matchAll({ type: 'window' });
        clients.forEach((client) =>
          client.postMessage({ type: 'SYNC_SUCCESS', url: entry.request.url })
        );
      } catch (error) {
        await queue.unshiftRequest(entry);
        throw error;
      }
    }
  },
});

registerRoute(
  ({ url }) => url.pathname.includes('/api/v1/diet/records'),
  new NetworkFirst({
    cacheName: 'api-diet-records',
    plugins: [bgSyncPlugin],
  }),
  'POST'
);

// 策略 5：API 调用（GET 请求）→ Stale While Revalidate
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/v1/'),
  new StaleWhileRevalidate({
    cacheName: 'api-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 1 * 24 * 60 * 60, // 1天
      }),
    ],
  }),
  'GET'
);
```

### 1.4 离线记录队列（前端层）

```typescript
// lib/offline-queue.ts
interface QueuedAction {
  id: string;
  type: 'diet_record' | 'profile_update' | 'body_metric';
  payload: unknown;
  timestamp: number;
  retryCount: number;
}

class OfflineQueue {
  private db: IDBDatabase | null = null;
  private readonly DB_NAME = 'MealMuseOffline';
  private readonly DB_VERSION = 1;
  private readonly STORE_NAME = 'action_queue';

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(this.STORE_NAME)) {
          const store = db.createObjectStore(this.STORE_NAME, { keyPath: 'id' });
          store.createIndex('type', 'type', { unique: false });
          store.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  async enqueue(action: Omit<QueuedAction, 'id' | 'timestamp' | 'retryCount'>): Promise<void> {
    const fullAction: QueuedAction = {
      ...action,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      retryCount: 0,
    };

    const tx = this.db!.transaction(this.STORE_NAME, 'readwrite');
    const store = tx.objectStore(this.STORE_NAME);
    await store.add(fullAction);

    // 如果在线，尝试立即同步
    if (navigator.onLine) {
      this.flush();
    }
  }

  async flush(): Promise<void> {
    if (!navigator.onLine) return;

    const tx = this.db!.transaction(this.STORE_NAME, 'readonly');
    const store = tx.objectStore(this.STORE_NAME);
    const request = store.openCursor();

    request.onsuccess = async (event) => {
      const cursor = (event.target as IDBRequest).result;
      if (!cursor) return;

      const action = cursor.value as QueuedAction;
      try {
        await this.processAction(action);
        // 成功则删除
        const deleteTx = this.db!.transaction(this.STORE_NAME, 'readwrite');
        await deleteTx.objectStore(this.STORE_NAME).delete(action.id);
      } catch (error) {
        // 失败则增加重试计数
        action.retryCount++;
        if (action.retryCount > 3) {
          // 标记为失败，通知用户
          this.notifyFailure(action);
        } else {
          const updateTx = this.db!.transaction(this.STORE_NAME, 'readwrite');
          await updateTx.objectStore(this.STORE_NAME).put(action);
        }
      }
      cursor.continue();
    };
  }

  private async processAction(action: QueuedAction): Promise<void> {
    switch (action.type) {
      case 'diet_record':
        await api.post('/diet/records', action.payload);
        break;
      case 'profile_update':
        await api.put('/users/profile', action.payload);
        break;
      case 'body_metric':
        await api.post('/body-metrics', action.payload);
        break;
    }
  }

  private notifyFailure(action: QueuedAction): void {
    // 触发本地通知或 Toast
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('MealMuse', {
        body: '有一条饮食记录同步失败，请稍后重试',
        icon: '/icons/icon-192x192.png',
      });
    }
  }
}

export const offlineQueue = new OfflineQueue();

// 网络状态监听
window.addEventListener('online', () => {
  offlineQueue.flush();
  // 显示 "已恢复网络，正在同步..." Toast
});

window.addEventListener('offline', () => {
  // 显示 "进入离线模式，数据将在恢复网络后同步" Toast
});
```

### 1.5 离线 UI 状态指示

```
┌─────────────────────────────────────────┐
│  🌿 MealMuse              ⚡ 离线模式    │  <- 顶部栏显示离线徽章
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  📝 饮食记录                      │   │
│  │                                  │   │
│  │  💬 说说你吃了什么...             │   │
│  │  [📷] [🎤]              [📤]     │   │
│  │                                  │   │
│  │  ⚠️ 当前处于离线模式              │   │
│  │  记录已保存，将在联网后自动同步   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ── 待同步 (2) ──────────────────────   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  ⏳ 午餐记录  12:30              │   │
│  │  牛肉面 1 碗                     │   │
│  │  [等待同步]                      │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**离线状态设计规范：**

| 元素 | 表现 |
|------|------|
| 顶部栏 | 右侧显示 "⚡ 离线" 黄色徽章，点击展开详情 |
| 输入区域 | 底部显示半透明提示条："离线模式 — 记录将在联网后同步" |
| 待同步列表 | 首页或记录页显示 "待同步 (N)" 折叠面板 |
| 同步中 | 待同步项显示旋转图标 + "同步中..." |
| 同步成功 | Toast："✅ 3 条记录已同步" |
| 同步失败 | Toast："❌ 同步失败，已保存，将自动重试" |

---

## 2. 多模态输入设计

### 2.1 饮食记录页输入区增强

**Mobile 版：**
```
┌─────────────────────────────────────────┐
│                                         │
│  💬 说说你吃了什么...                    │
│                                         │
│  例如：中午吃了一碗牛肉面...            │
│                                         │
│  [🎤 语音]  [📷 拍照]      [发送 📤]   │
│                                         │
└─────────────────────────────────────────┘
```

**Desktop 版：**
```
┌─────────────────────────────────────────────────────────┐
│  💬 说说你吃了什么...                                    │
│                                                         │
│  例如：中午吃了一碗牛肉面，一个苹果，一杯酸奶           │
│                                                         │
│  [🎤 语音输入]  [📷 拍照识别]  [📎 上传图片]   [发送 📤] │
└─────────────────────────────────────────────────────────┘
```

**交互说明：**

| 按钮 | 触发 | 后续流程 |
|------|------|---------|
| 🎤 语音 | 长按（Mobile）/ 点击（Desktop） | 调用 Web Speech API 或上传音频文件 → 后端语音转文字 → 进入常规解析流程 |
| 📷 拍照 | 唤起摄像头（Mobile）/ 文件选择器（Desktop） | 拍摄/选择图片 → 前端预览 → 上传至 `/api/v1/diet/photo-analyze` → AI 视觉识别食物 |
| 📎 上传图片 | 文件选择器 | 同上，支持多图上传 |

### 2.2 拍照识别结果展示

```
┌─────────────────────────────────────────┐
│  ← 返回         识别结果                 │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  [📷 图片预览]                   │   │
│  │  红烧牛肉面 + 凉拌黄瓜           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  AI 识别到以下食物：                    │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ☑️ 红烧牛肉面    1碗   520 kcal │   │
│  │    [调整份量 ▼]                  │   │
│  ├─────────────────────────────────┤   │
│  │ ☑️ 凉拌黄瓜      1份    30 kcal │   │
│  │    [调整份量 ▼]                  │   │
│  ├─────────────────────────────────┤   │
│  │ ☐  煎蛋          1个   ？kcal   │   │  <- AI 不确定的项，默认未勾选
│  │    [确认添加]                    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [+ 手动添加遗漏的食物]                  │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │       确认并记录 (550 kcal)      │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**关键交互原则：**
- AI 识别不确定的食物用 `?` 标记，默认不勾选，让用户确认
- 支持左右滑动/点击切换多张图片的识别结果
- 用户可即时调整份量，热量实时重算
- 保留 "这不是我要找的" 反馈入口，用于改进模型

### 2.3 语音输入状态

```
┌─────────────────────────────────────────┐
│                                         │
│  ┌─────────────────────────────────┐   │
│  │                                 │   │
│  │      🎤  正在聆听...            │   │
│  │                                 │   │
│  │      ~~~~ 波形动画 ~~~~         │   │
│  │                                 │   │
│  │      "中午吃了一碗牛肉面..."    │   │
│  │                                 │   │
│  │      [松开结束]                 │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

## 3. 深色模式完整方案

### 3.1 扩展后的色彩系统

```
浅色模式（已有）
┌──────────────────────────────────────────┐
│  Bg         #FAFAFA  ████████████        │
│  Surface    #FFFFFF  ████████████        │
│  Text-1     #111827  ████████████        │
│  Text-2     #6B7280  ████████████        │
│  Border     #E5E7EB  ████████████        │
└──────────────────────────────────────────┘

深色模式（完整版）
┌──────────────────────────────────────────┐
│  Bg         #0F172A  ████████████        │  深蓝灰（降低 OLED 烧屏）
│  Surface    #1E293B  ████████████        │  卡片背景
│  Surface-H  #334155  ████████████        │  悬浮态/选中态
│  Text-1     #F1F5F9  ████████████        │  主文字
│  Text-2     #94A3B8  ████████████        │  次要文字
│  Border     #334155  ████████████        │  边框
│  Primary    #4ADE80  ████████████        │  主色调提亮（深色背景上增强对比）
│  Primary-D  #22C55E  ████████████        │  深色模式下的默认绿色
│  Accent     #FBBF24  ████████████        │  CTA 按钮提亮
│  Warning    #F87171  ████████████        │  警告色提亮
│  Info       #60A5FA  ████████████        │  信息色提亮
└──────────────────────────────────────────┘
```

### 3.2 Tailwind 配置

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class", // 通过 class 控制，支持系统级 + 手动切换
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: "hsl(var(--background))",
          dark: "hsl(var(--background-dark))",
        },
        surface: {
          DEFAULT: "hsl(var(--surface))",
          hover: "hsl(var(--surface-hover))",
          dark: {
            DEFAULT: "hsl(var(--surface-dark))",
            hover: "hsl(var(--surface-dark-hover))",
          },
        },
        primary: {
          DEFAULT: "#22C55E",
          light: "#86EFAC",
          dark: "#15803D",
          // 深色模式下自动提亮
          "dark-mode": "#4ADE80",
        },
        // ... 其他颜色
      },
    },
  },
};
```

```css
/* globals.css */
@layer base {
  :root {
    --background: 0 0% 98%;           /* #FAFAFA */
    --background-dark: 222 47% 11%;   /* #0F172A */
    --surface: 0 0% 100%;             /* #FFFFFF */
    --surface-hover: 210 20% 96%;     /* #F8FAFC */
    --surface-dark: 217 33% 17%;      /* #1E293B */
    --surface-dark-hover: 215 25% 27%;/* #334155 */
    /* ... */
  }

  .dark {
    --background: 222 47% 11%;
    --surface: 217 33% 17%;
    --surface-hover: 215 25% 27%;
    /* 文字颜色自动反转由 Tailwind 处理 */
  }
}
```

### 3.3 各组件深色模式变体

| 组件 | 浅色模式 | 深色模式 |
|------|---------|---------|
| **页面背景** | `bg-[#FAFAFA]` | `dark:bg-[#0F172A]` |
| **卡片** | `bg-white border-gray-200` | `dark:bg-[#1E293B] dark:border-[#334155]` |
| **卡片悬浮** | `hover:bg-gray-50` | `dark:hover:bg-[#334155]` |
| **主按钮** | `bg-[#22C55E] text-white` | `dark:bg-[#22C55E] dark:text-white`（保持） |
| **次要按钮** | `bg-gray-100 text-gray-700` | `dark:bg-[#334155] dark:text-[#94A3B8]` |
| **输入框** | `bg-white border-gray-300` | `dark:bg-[#0F172A] dark:border-[#334155] dark:text-white` |
| **AI 助手气泡** | `bg-[#F0FDF4] border-[#BBF7D0]` | `dark:bg-[#064E3B] dark:border-[#166534]` |
| **用户气泡** | `bg-[#22C55E] text-white` | `dark:bg-[#15803D] dark:text-white` |
| **警告提示** | `bg-red-50 text-red-700` | `dark:bg-red-950 dark:text-red-300` |
| **图表网格** | `stroke-gray-200` | `dark:stroke-[#334155]` |
| **图表文字** | `fill-gray-600` | `dark:fill-[#94A3B8]` |
| **日历选中** | `bg-[#22C55E] text-white` | `dark:bg-[#22C55E] dark:text-white` |
| **离线徽章** | `bg-yellow-100 text-yellow-800` | `dark:bg-yellow-900 dark:text-yellow-200` |

### 3.4 深色模式切换设计

```
┌─────────────────────────────────────────┐
│  🌙 深色模式                   [开关]   │  <- 个人中心设置项
│     跟随系统                   [开关]   │  <- 默认开启
└─────────────────────────────────────────┘
```

**优先级逻辑：**
1. 用户手动设置 > 系统偏好 > 默认浅色
2. 切换时添加 300ms 的 CSS transition，避免闪变
3. 使用 `localStorage` 持久化用户偏好
4. 在 `html` 标签上动态添加/移除 `dark` class

---

## 4. 状态设计（空态 / 加载 / 错误）

### 4.1 空态（Empty State）

**首页 — 无餐食计划：**
```
┌─────────────────────────────────────────┐
│                                         │
│              🍽️                         │
│                                         │
│         还没有今日餐食计划              │
│                                         │
│    让 AI 为你生成专属三餐方案           │
│                                         │
│       [生成今日餐食计划]                │
│                                         │
└─────────────────────────────────────────┘
```

**记录页 — 无历史记录：**
```
┌─────────────────────────────────────────┐
│                                         │
│              📝                         │
│                                         │
│         还没有饮食记录                  │
│                                         │
│    记录第一餐，开启健康追踪之旅         │
│                                         │
│         [开始记录]                      │
│                                         │
└─────────────────────────────────────────┘
```

**报告页 — 数据不足：**
```
┌─────────────────────────────────────────┐
│                                         │
│              📊                         │
│                                         │
│         数据还不足以生成报告            │
│                                         │
│    连续记录 3 天饮食后，AI 将为你       │
│    生成个性化的营养分析报告             │
│                                         │
│      当前进度：███░░░░░░░  1/3 天       │
│                                         │
└─────────────────────────────────────────┘
```

**空态设计规范：**

| 元素 | 规范 |
|------|------|
| 图标 | 使用 Lucide 图标，size: 64px，颜色: Text-2（`#6B7280` / `#94A3B8`） |
| 标题 | H3 字号（18px），Semibold，颜色: Text-1 |
| 描述 | Body 字号（16px），Regular，颜色: Text-2，最大宽度 320px 居中 |
| 按钮 | Primary 按钮，引导用户执行核心动作 |
| 动画 | 图标轻微上下浮动（`animate-bounce-subtle`），增加活力 |

### 4.2 加载态（Loading State）

**骨架屏规范：**
```
浅色：bg-gray-200 → animate-pulse
深色：dark:bg-[#334155] → animate-pulse
```

**各页面骨架屏：**

**首页骨架屏：**
```
┌─────────────────────────────────────────┐
│  ░░░░░░░░░                              │  <- 顶部栏
├─────────────────────────────────────────┤
│  ░░░░░░░░░░░░░░                         │  <- 问候语
│  ░░░░░░░░░░░░░░░░░░░                    │  <- 目标热量
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  ░░░░░░░░░  ░░░░░░░░░░░░░░░░░  │   │  <- 营养进度骨架
│  │  ░░░░░░░░░  ░░░░░░░░░░░░░░░░░  │   │
│  │  ░░░░░░░░░  ░░░░░░░░░░░░░░░░░  │   │
│  │  ░░░░░░░░░  ░░░░░░░░░░░░░░░░░  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  ░░░░  ░░░░░░░░░░░░░░░░░░░░░   │   │  <- 餐食卡片骨架
│  │       ░░░░░░░░░░░░░░░░░░░░░    │   │
│  │       ░░░░░░░░░                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  ░░░░  ░░░░░░░░░░░░░░░░░░░░░   │   │
│  │       ░░░░░░░░░░░░░░░░░░░░░    │   │
│  │       ░░░░░░░░░                 │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**AI 对话加载态：**
```
┌─────────────────────────────────────────┐
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 🤖 AI                          │   │
│  │  ● ● ●  （脉冲动画）            │   │
│  │                                 │   │
│  │  正在分析你的饮食数据...        │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**加载态层级：**

| 场景 | 加载方式 | 说明 |
|------|---------|------|
| 页面首次加载 | 骨架屏 | 全页骨架，保持布局结构 |
| 下拉刷新 | 顶部旋转指示器 | 保留现有内容，顶部显示刷新动画 |
| 按钮点击 | 按钮内旋转图标 | 按钮文字变为 "加载中..."，禁用点击 |
| AI 生成 | 打字机效果 + 骨架 | 首 token 返回前显示脉冲点，之后逐字输出 |
| 图片上传 | 进度条 | 显示上传百分比，支持取消 |

### 4.3 错误态（Error State）

**网络错误：**
```
┌─────────────────────────────────────────┐
│                                         │
│              📡                         │
│                                         │
│         网络连接失败                    │
│                                         │
│    请检查网络设置，或尝试以下操作：     │
│                                         │
│    • 刷新页面                           │
│    • 稍后重试                           │
│    • 使用离线模式继续记录               │
│                                         │
│       [刷新页面]  [进入离线模式]        │
│                                         │
└─────────────────────────────────────────┘
```

**API 错误（带错误码）：**
```
┌─────────────────────────────────────────┐
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  ⚠️  暂时无法生成餐食计划        │   │
│  │                                 │   │
│  │  错误码：ERR_AI_TIMEOUT         │   │
│  │  AI 服务响应超时，请稍后重试。   │   │
│  │                                 │   │
│  │  [重试]  [查看昨日计划]          │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**数据加载失败（局部）：**
```
┌─────────────────────────────────────────┐
│  📊 本周营养概览                         │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │                                 │   │
│  │      ⚠️  图表加载失败           │   │
│  │                                 │   │
│  │  点击重试或稍后查看             │   │
│  │                                 │   │
│  │        [重新加载]               │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**错误态设计规范：**

| 元素 | 规范 |
|------|------|
| 图标 | 使用错误相关图标（`WifiOff`, `AlertTriangle`, `ServerCrash`），size: 48px，颜色: Warning `#EF4444` |
| 标题 | 说明发生了什么，不使用技术术语（"网络连接失败" 而非 "HTTP 503"） |
| 描述 | 给出可操作的建议（2-3 条） |
| 按钮 | 主按钮：解决问题的动作；次按钮：替代方案或退出 |
| 错误码 | 小字显示在底部，方便用户反馈时提供 |

### 4.4 操作成功反馈（Success State）

| 操作 | 反馈方式 | 内容 |
|------|---------|------|
| 记录饮食 | Toast | "✅ 早餐已记录 · 290 kcal" |
| 生成餐食 | Toast | "✅ 今日三餐已生成" |
| 替换餐食 | Toast | "🔄 午餐已替换为清蒸鲈鱼套餐" |
| 保存设置 | Toast | "✅ 设置已保存" |
| 退出登录 | 页面跳转 + Toast | "已安全退出" |
| 同步完成 | Toast | "✅ 3 条记录已同步" |

**Toast 设计：**
```
浅色：bg-gray-900 text-white rounded-lg shadow-lg px-4 py-3
深色：dark:bg-white dark:text-gray-900 rounded-lg shadow-lg px-4 py-3
位置：Mobile 底部居中，Desktop 顶部居中
时长：2 秒自动消失，支持手动划走
动画：从下方滑入 + 淡入（Mobile），从顶部滑入（Desktop）
```

---

## 5. 状态汇总表

| 状态 | 触发条件 | 视觉表现 | 用户可执行操作 |
|------|---------|---------|--------------|
| **初始加载** | 进入页面 | 骨架屏 | 等待 |
| **数据为空** | 无历史数据 | 空态插图 + 引导按钮 | 执行核心动作 |
| **数据加载中** | 下拉刷新/分页加载 | 顶部/底部旋转指示器 | 等待或取消 |
| **AI 思考中** | 发送 AI 消息 | 脉冲动画 + "分析中..." | 等待或取消 |
| **AI 流式输出** | 收到首 token | 逐字显示 + 停止按钮 | 等待完成或停止 |
| **操作成功** | 提交/保存成功 | Toast 提示 | 自动消失 |
| **网络异常** | 请求失败 | 错误态卡片 | 重试/离线模式 |
| **离线模式** | 网络断开 | 顶部离线徽章 + 本地队列 | 继续记录 |
| **同步中** | 恢复网络 | 待同步项显示旋转图标 | 等待 |
| **同步失败** | 后台同步失败 | Toast + 待同步项标记 | 手动重试 |

---

*文档版本：v1.0 | 创建日期：2026-06-07*
