# MealMuse UI 页面风格增强设计稿

> 版本：v1.0 | 日期：2026-06-13 | 基于项目全量扫描

---

## 1. 色彩体系重构

### 1.1 6 色调色板

```
主色     #22c55e  品牌绿（仅 CTA 按钮/Logo）
暖色     #f59e0b  橙黄（热量/食物相关）
紫色     #8b5cf6  强调（AI/智能相关）
蓝色     #3b82f6  信息（数据/图表）
警告     #ef4444  红色（禁忌/超标）
中性     #6b7280  灰色（文字/边框）
```

**使用规则**：
- 绿色只用于：品牌 Logo、主 CTA（记录/发送/生成）、成功状态
- 暖橙色用于：食物热量标签、餐食卡片背景色、营养数值
- 紫色用于：AI 回复气泡、AI 标签、智能推荐
- 蓝色用于：数据指标、图表填充、进度条

### 1.2 三餐配色方案

| 餐次 | 标题色 | 背景色 | 边框色 |
|------|--------|--------|--------|
| 早餐 | text-orange-500 | bg-orange-50 | border-orange-100 |
| 午餐 | text-amber-500 | bg-amber-50 | border-amber-100 |
| 晚餐 | text-indigo-500 | bg-indigo-50 | border-indigo-100 |

### 1.3 Tailwind CSS 配置

```typescript
// tailwind.config.ts 扩展
colors: {
  brand: {
    DEFAULT: '#22c55e',
    light: '#86efac',
    dark: '#15803d',
  },
  warm: {
    DEFAULT: '#f59e0b',
    light: '#fde68a',
    dark: '#d97706',
  },
  ai: {
    DEFAULT: '#8b5cf6',
    light: '#c4b5fd',
    dark: '#6d28d9',
  },
}
```

---

## 2. 卡片差异化设计

### 2.1 卡片类型规范

**首页概览卡（营养进度）**
```css
/* 渐变背景，视觉层次最高 */
background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
border: 1px solid #dcfce7;
```

**餐食卡片（三餐）**
```css
/* 每餐不同暖色，标题区背景色深浅区分 */
breakfast: bg-orange-50 border-orange-100
lunch: bg-amber-50 border-amber-100
dinner: bg-indigo-50 border-indigo-100
```

**AI 对话气泡**
```css
/* AI 回复：浅紫色背景 */
background: #f5f3ff;  /* purple-50 */
border: 1px solid #ddd6fe;
border-radius: 16px 16px 16px 4px;
```

**经期卡片**
```css
/* 粉色系保留，区别于其他功能 */
background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%);
border: 1px solid #fbcfe8;
```

**数据统计卡片（KPI）**
```css
/* 数字突出，标题次要 */
background: white;
数字: text-2xl font-bold text-brand
标签: text-xs text-gray-500
```

---

## 3. 首页改造

### 3.1 热量圆环（改用 Recharts）

```tsx
// components/calorie-ring.tsx
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const COLORS = ['#22c55e', '#e5e7eb']; // 已完成 vs 剩余

export function CalorieRing({ consumed, target }: {
  consumed: number;
  target: number;
}) {
  const percent = Math.min((consumed / target) * 100, 100);
  const data = [
    { name: '已摄入', value: consumed },
    { name: '剩余', value: Math.max(target - consumed, 0) },
  ];

  return (
    <ResponsiveContainer width={120} height={120}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={40}
          outerRadius={56}
          startAngle={90}
          endAngle={-270}
          dataKey="value"
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i]} />
          ))}
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  );
}
```

### 3.2 三餐卡片增加状态图标

```
已记录：✅ 绿色勾号
未记录：○ 空心圆
计划中：🍽️ 餐盘图标
```

### 3.3 问候语动态化

```tsx
const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 6) return { text: '夜深了', icon: '🌙' };
  if (hour < 9) return { text: '早上好', icon: '🌅' };
  if (hour < 12) return { text: '上午好', icon: '☀️' };
  if (hour < 14) return { text: '中午好', icon: '🌞' };
  if (hour < 18) return { text: '下午好', icon: '🌤️' };
  if (hour < 21) return { text: '晚上好', icon: '🌆' };
  return { text: '夜安', icon: '🌙' };
};
```

---

## 4. 报告页图表升级

### 4.1 营养雷达图（Recharts RadarChart）

```tsx
// components/nutrition-radar.tsx
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';

const COLORS = {
  protein: '#8b5cf6',
  fat: '#f59e0b',
  carbs: '#3b82f6',
  fiber: '#22c55e',
  calorie: '#ef4444',
};

export function NutritionRadar({ scores }: {
  scores: { protein: number; fat: number; carbs: number; fiber: number; calorie: number }
}) {
  const data = [
    { subject: '蛋白质', value: scores.protein, fill: COLORS.protein },
    { subject: '脂肪', value: scores.fat, fill: COLORS.fat },
    { subject: '碳水', value: scores.carbs, fill: COLORS.carbs },
    { subject: '纤维', value: scores.fiber, fill: COLORS.fiber },
    { subject: '热量', value: scores.calorie, fill: COLORS.calorie },
  ];

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 12 }} />
        <Radar
          name="营养"
          dataKey="value"
          stroke="#8b5cf6"
          fill="#8b5cf6"
          fillOpacity={0.3}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
```

### 4.2 热量趋势折线图

```tsx
// components/calorie-trend.tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export function CalorieTrend({ data, target }: {
  data: Array<{ date: string; calories: number }>;
  target: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#9ca3af' }} />
        <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} width={40} />
        <Tooltip
          contentStyle={{
            background: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <ReferenceLine y={target} stroke="#22c55e" strokeDasharray="4 4" label="目标" />
        <Line
          type="monotone"
          dataKey="calories"
          stroke="#8b5cf6"
          strokeWidth={2}
          dot={{ fill: '#8b5cf6', r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### 4.3 营养达标日历热力图

```
类似 GitHub contributions，绿色深浅表示当日热量控制达标程度：
深绿：超额达标（≥100%）
中绿：达标（80-99%）
浅绿：不足（50-79%）
浅灰：未记录
```

---

## 5. 全局体验增强

### 5.1 Toast 通知组件

```tsx
// components/ui/toast.tsx
interface ToastProps {
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number; // 默认 3000ms
}

const CONFIG = {
  success: { icon: '✅', bg: 'bg-gray-900', text: 'text-white' },
  error: { icon: '❌', bg: 'bg-red-600', text: 'text-white' },
  info: { icon: '💡', bg: 'bg-blue-600', text: 'text-white' },
  warning: { icon: '⚠️', bg: 'bg-amber-500', text: 'text-white' },
};
```

### 5.2 Skeleton Loading 组件

```tsx
// components/ui/skeleton.tsx
export function CardSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4" />
      <div className="h-3 bg-gray-100 rounded w-1/2" />
      <div className="h-3 bg-gray-100 rounded w-5/6" />
    </div>
  );
}
```

各页面骨架屏规范：
- 首页：热量圆环骨架 + 三餐卡片骨架 + 营养进度骨架
- 记录页：输入框骨架 + 记录列表骨架
- 报告页：KPI 卡片骨架 + 图表骨架

### 5.3 AI 打字机效果

```tsx
// hooks/useTypewriter.ts
export function useTypewriter(text: string, speed: number = 30) {
  const [displayed, setDisplayed] = useState('');
  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      setDisplayed(text.slice(0, i + 1));
      i++;
      if (i >= text.length) clearInterval(interval);
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);
  return displayed;
}
```

### 5.4 页面过渡动画

```tsx
// app/(main)/layout.tsx 增强
import { motion, AnimatePresence } from 'framer-motion';

const pageVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
};

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{ duration: 0.2 }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
```

---

## 6. 登录页优化

### 6.1 问题
- 微信登录按钮纯 UI，无功能
- 缺少品牌价值主张

### 6.2 改造

```
┌─────────────────────────────────────────────┐
│                                             │
│           🌿                                │
│         MealMuse                            │
│     每一餐，都是对自己的善待                  │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  📱 手机号                            │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │ +86  138 **** 8888            │ │ │
│  │  └─────────────────────────────────┘ │ │
│  │                                       │ │
│  │  🔢 验证码                            │ │
│  │  ┌─────────────────┐ ┌────────────┐ │ │
│  │  │ 6位验证码        │ │ 获取验证码  │ │ │
│  │  └─────────────────┘ └────────────┘ │ │
│  │                                       │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │        登录 / 注册               │ │ │
│  │  └─────────────────────────────────┘ │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ─────────── 或 ───────────                │
│                                             │
│  [🔍 微信登录（即将上线）]  <- 置灰/去掉   │
│                                             │
│  登录即表示同意《用户协议》和《隐私政策》   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 7. 深色模式 CSS 变量

```css
/* globals.css */
:root {
  --background: 0 0% 98%;
  --surface: 0 0% 100%;
  --surface-hover: 210 20% 96%;
  --border: 220 13% 91%;
  --text-primary: 222 47% 11%;
  --text-secondary: 215 16% 47%;
  --brand: 142 71% 45%;
  --brand-light: 142 76% 90%;
  --warm: 38 92% 50%;
  --ai: 262 83% 58%;
  --warning: 0 84% 60%;
}

.dark {
  --background: 222 47% 11%;
  --surface: 217 33% 17%;
  --surface-hover: 215 25% 27%;
  --border: 215 25% 27%;
  --text-primary: 210 40% 98%;
  --text-secondary: 215 20% 65%;
  --brand: 142 76% 49%;
  --brand-light: 142 76% 20%;
  --ai: 262 83% 70%;
}
```

---

## 8. 执行清单

| 序号 | 任务 | 状态 |
|------|------|------|
| 1 | 色彩体系重构（tailwind.config.ts） | 待做 |
| 2 | 登录页优化（去掉微信按钮+品牌文案） | 待做 |
| 3 | Toast 组件实现 | 待做 |
| 4 | Skeleton Loading 组件实现 | 待做 |
| 5 | CalorieRing 替换 SVG（Recharts） | 待做 |
| 6 | NutritionRadar 替换进度条（Recharts） | 待做 |
| 7 | CalorieTrend 折线图实现 | 待做 |
| 8 | 三餐卡片差异化配色 | 待做 |
| 9 | AI 打字机效果 | 待做 |
| 10 | 页面过渡动画 | 待做 |
| 11 | 深色模式 CSS 变量 + 适配 | 待做 |

---

*文档版本：v1.0 | 日期：2026-06-13*
