# MealMuse AI 服务插件化架构设计

> 版本：v1.0 | 创建日期：2026-06-07 | 对应：architecture.md 的 AI 集成方案扩展
>
> **设计目标：** 将单体 `ai_service.py` 改造为可插拔的多引擎架构，支持营养分析、中医体质、节气养生、备孕调理等独立领域，各自进化、互不干扰。

---

## 1. 现状问题

当前架构（`architecture.md` 4.1 节）：

```python
# 当前：一个 AI_SERVICE 字典 + 一个 ai_service.py 封装所有调用
AI_MODELS = { "primary": {...}, "fallback": {...} }
# 所有场景（食物解析、餐食生成、AI 对话）共用同一套 Prompt 模板和模型
```

**问题：**
| 问题 | 后果 |
|------|------|
| 所有场景的 System Prompt 混在一起 | 中医知识干扰营养计算，模型上下文利用率低 |
| 没有领域隔离 | 新增中医模块时，只能往现有代码里"打补丁" |
| 知识库耦合在 Prompt 里 | 无法做 RAG（检索增强生成），知识更新需改代码 |
| 单模型兜底 | 中医场景需要更强的中文古典理解能力，但用的是同一模型 |

---

## 2. 目标架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI API Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ /chat    │  │ /meals   │  │ /diet    │  │ /tcm     │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
└───────┼─────────────┼─────────────┼─────────────┼──────────────────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │
                    ┌────────┴────────┐
                    │  AI Engine      │
                    │  Router         │
                    │  (路由/编排)     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Nutrition     │  │ TCM           │  │ Seasonal      │
│ Engine        │  │ Engine        │  │ Engine        │
│ (营养分析)     │  │ (中医体质)     │  │ (节气养生)     │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ • 食物解析     │  │ • 体质测试     │  │ • 节气识别     │
│ • 餐食生成     │  │ • 食疗推荐     │  │ • 时令推荐     │
│ • 营养分析     │  │ • 食材属性     │  │ • 气候适配     │
│ • 热量计算     │  │ • 体质对话     │  │ • 节气对话     │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Prompt Manager                           │
│              (领域隔离的 Prompt 模板库)                       │
└─────────────────────────────────────────────────────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Model Gateway                            │
│         (统一封装：通义千问 / 文心 / 未来专用中医模型)           │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│              Knowledge RAG (向量数据库)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 营养知识库   │  │ 中医古籍库   │  │ 节气养生库   │         │
│  │ (食物营养)   │  │ (食疗方/体质)│  │ (时令/习俗)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 核心代码设计

### 3.1 目录结构

```
meal-muse-api/
├── app/
│   ├── services/
│   │   └── ai/                          # 【新增】AI 引擎模块
│   │       ├── __init__.py
│   │       ├── router.py                # 引擎路由器
│   │       ├── model_gateway.py         # 模型网关（统一调用 LLM）
│   │       ├── prompt_manager.py        # Prompt 管理器
│   │       ├── rag_service.py           # RAG 检索服务
│   │       ├── base_engine.py           # 抽象基类
│   │       ├── nutrition_engine.py      # 营养引擎
│   │       ├── tcm_engine.py            # 中医引擎【预留】
│   │       ├── seasonal_engine.py       # 节气引擎【预留】
│   │       ├── pregnancy_engine.py      # 备孕引擎【预留】
│   │       └── safety_filter.py         # 输出安全过滤
│   └── ...
```

### 3.2 抽象基类 `BaseEngine`

```python
# app/services/ai/base_engine.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Dict, Any
from dataclasses import dataclass
import json


@dataclass
class AIContext:
    """统一的 AI 上下文数据包，各引擎按需取用"""
    user_id: str
    goal_type: Optional[str] = None           # weight_loss / pregnancy / health / muscle_gain
    body_info: Optional[Dict[str, Any]] = None  # 身高体重年龄等
    today_records: Optional[list] = None
    weekly_summary: Optional[Dict[str, Any]] = None
    # 【中医扩展】
    tcm_constitution: Optional[str] = None    # qi_deficiency / yang_deficiency ...
    solar_term: Optional[str] = None          # 当前节气
    menstrual_phase: Optional[str] = None     # menstrual / follicular / ovulation / luteal
    # 【家庭扩展】
    family_context: Optional[Dict[str, Any]] = None


@dataclass
class EngineResult:
    """引擎返回的统一结构"""
    content: str                              # 文本回复
    structured_data: Optional[Dict[str, Any]] = None  # 结构化数据（JSON）
    sources: Optional[list] = None            # RAG 引用的知识来源
    engine_name: str = "unknown"
    model_used: str = "unknown"
    tokens_used: int = 0
    cost_yuan: float = 0.0
    response_time_ms: int = 0


class BaseEngine(ABC):
    """AI 引擎抽象基类。所有领域引擎必须继承此类。"""

    name: str = "base"
    description: str = ""
    # 默认使用的模型，子类可覆盖
    default_model: str = "qwen-plus"
    # 该引擎是否支持流式输出
    supports_streaming: bool = True

    def __init__(
        self,
        model_gateway,
        prompt_manager,
        rag_service: Optional[Any] = None,
    ):
        self.model_gateway = model_gateway
        self.prompt_manager = prompt_manager
        self.rag_service = rag_service

    @abstractmethod
    def can_handle(self, intent: str, context: AIContext) -> float:
        """
        判断本引擎是否能处理该意图。
        返回 0.0 ~ 1.0 的置信度分数。
        """
        pass

    @abstractmethod
    async def execute(
        self,
        query: str,
        context: AIContext,
        stream: bool = False,
    ) -> EngineResult | AsyncGenerator[str, None]:
        """
        执行核心逻辑。
        如果 stream=True，返回 AsyncGenerator（逐字流式输出）。
        如果 stream=False，返回 EngineResult（完整结果）。
        """
        pass

    async def _retrieve_knowledge(self, query: str, filters: Optional[Dict] = None) -> list:
        """从 RAG 知识库检索相关知识"""
        if not self.rag_service:
            return []
        return await self.rag_service.search(
            query=query,
            namespace=self.name,   # 按引擎名隔离知识库
            filters=filters,
            top_k=5,
        )

    def _build_system_prompt(self, context: AIContext, extra_context: Optional[str] = None) -> str:
        """使用 PromptManager 构建系统提示词"""
        return self.prompt_manager.render(
            template_name=f"{self.name}/system",
            context=context,
            extra=extra_context,
        )
```

### 3.3 模型网关 `ModelGateway`

```python
# app/services/ai/model_gateway.py
import os
import time
from typing import AsyncGenerator, Optional
import openai


class ModelGateway:
    """
    统一模型调用网关。
    封装通义千问、文心一言等模型的差异，支持多模型路由和降级。
    """

    MODEL_CONFIGS = {
        "qwen-plus": {
            "provider": "alibaba",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model_id": "qwen-plus",
            "max_tokens": 8192,
            "cost_per_1k_input": 0.004,
            "cost_per_1k_output": 0.012,
        },
        "qwen-turbo": {
            "provider": "alibaba",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model_id": "qwen-turbo",
            "max_tokens": 8192,
            "cost_per_1k_input": 0.001,
            "cost_per_1k_output": 0.002,
        },
        "ernie-3.5": {
            "provider": "baidu",
            "base_url": "https://qianfan.baidubce.com/v2",
            "model_id": "ernie-3.5-8k",
            "max_tokens": 8192,
            "cost_per_1k_input": 0.008,
            "cost_per_1k_output": 0.008,
        },
        # 【预留】未来接入中医专用模型或微调模型
        "qwen-tcm-finetune": {
            "provider": "alibaba",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model_id": "qwen-tcm-finetune",  # 假设的微调模型
            "max_tokens": 8192,
            "cost_per_1k_input": 0.006,
            "cost_per_1k_output": 0.018,
        },
    }

    def __init__(self):
        self._clients = {}

    def _get_client(self, model_name: str):
        """获取或创建模型客户端（懒加载）"""
        if model_name not in self._clients:
            config = self.MODEL_CONFIGS[model_name]
            api_key = self._get_api_key(config["provider"])
            self._clients[model_name] = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=config["base_url"],
            )
        return self._clients[model_name]

    def _get_api_key(self, provider: str) -> str:
        key_map = {
            "alibaba": os.getenv("DASHSCOPE_API_KEY"),
            "baidu": os.getenv("BAIDIAN_API_KEY"),
        }
        return key_map.get(provider, "")

    async def chat(
        self,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        response_format: Optional[dict] = None,
    ) -> dict | AsyncGenerator[str, None]:
        """
        统一聊天接口。
        返回完整响应 dict，或流式的 AsyncGenerator。
        """
        config = self.MODEL_CONFIGS[model]
        client = self._get_client(model)

        start_time = time.time()

        try:
            response = await client.chat.completions.create(
                model=config["model_id"],
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or config["max_tokens"],
                stream=stream,
                response_format=response_format,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            if stream:
                return self._wrap_streaming(response, model, elapsed_ms)

            # 计算成本
            usage = response.usage
            cost = self._calculate_cost(model, usage.prompt_tokens, usage.completion_tokens)

            return {
                "content": response.choices[0].message.content,
                "model": model,
                "tokens": usage.total_tokens,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "cost_yuan": cost,
                "response_time_ms": elapsed_ms,
            }

        except Exception as e:
            # 失败时尝试 fallback 模型
            if model == "qwen-plus":
                return await self.chat("ernie-3.5", messages, temperature, max_tokens, stream, response_format)
            raise

    async def _wrap_streaming(self, response, model: str, start_time_ms: int):
        """包装流式响应，附加元数据"""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        config = self.MODEL_CONFIGS[model]
        input_cost = (prompt_tokens / 1000) * config["cost_per_1k_input"]
        output_cost = (completion_tokens / 1000) * config["cost_per_1k_output"]
        return round(input_cost + output_cost, 6)
```

### 3.4 Prompt 管理器 `PromptManager`

```python
# app/services/ai/prompt_manager.py
from typing import Optional, Dict, Any
import jinja2


class PromptManager:
    """
    领域隔离的 Prompt 模板管理器。
    每个引擎拥有独立的模板目录，避免互相污染。
    """

    def __init__(self, template_dir: str = "app/services/ai/prompts"):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # 预加载所有模板
        self._templates = {}

    def render(self, template_name: str, context: Any, extra: Optional[str] = None) -> str:
        """渲染指定模板"""
        template = self.env.get_template(f"{template_name}.j2")
        ctx = self._context_to_dict(context)
        if extra:
            ctx["extra_context"] = extra
        return template.render(**ctx)

    def _context_to_dict(self, context: Any) -> Dict[str, Any]:
        """将 AIContext dataclass 转为字典"""
        if hasattr(context, "__dataclass_fields__"):
            return {k: v for k, v in context.__dict__.items() if v is not None}
        return context if isinstance(context, dict) else {}

    def register_template(self, name: str, content: str):
        """运行时注册模板（用于动态更新的 Prompt）"""
        self.env.from_string(content)
        # 存入数据库或缓存，实现 Prompt A/B 测试和热更新
```

**目录结构示例：**
```
prompts/
├── nutrition/
│   ├── system.j2          # 营养引擎系统提示
│   ├── parse_food.j2      # 食物解析
│   ├── generate_meal.j2   # 餐食生成
│   └── analyze_diet.j2    # 饮食分析
├── tcm/
│   ├── system.j2          # 中医引擎系统提示【预留】
│   ├── constitution_test.j2   # 体质测试问卷生成
│   ├── food_property.j2   # 食材属性查询
│   └── diet_recommend.j2  # 食疗推荐
├── seasonal/
│   ├── system.j2          # 节气引擎系统提示【预留】
│   └── term_advice.j2     # 节气建议
└── common/
    └── safety_rules.j2    # 所有引擎共用的安全规则
```

**`prompts/tcm/system.j2` 示例：**
```jinja2
你是 MealMuse 中医食疗顾问，一位精通中医食疗学的专业助手。

你的职责：
1. 根据用户的中医体质，提供个性化的食疗建议
2. 结合当前节气，推荐应季食材和食谱
3. 回答中医饮食养生相关问题
4. 帮助用户理解食物的中医属性（寒热温凉、归经）

当前用户信息：
- 体质：{{ tcm_constitution or '未测试' }}
- 健康目标：{{ goal_type or '未设置' }}
- 今日饮食记录：{{ today_records or '暂无' }}
- 当前节气：{{ solar_term or '未知' }}

重要规则：
1. 只提供食疗和饮食养生建议，不提供疾病诊断和处方
2. 如果用户询问医疗问题，建议咨询专业中医师
3. 推荐食材时需说明中医原理，增强用户信任
4. 考虑用户实际生活场景，推荐简单易得的食材
5. 尊重现代科学，不传播伪科学，可中西医结合表达

{% include 'common/safety_rules.j2' %}
```

### 3.5 引擎路由器 `EngineRouter`

```python
# app/services/ai/router.py
from typing import List, Optional, AsyncGenerator
import re

from .base_engine import BaseEngine, AIContext, EngineResult


class EngineRouter:
    """
    AI 引擎路由器。
    根据用户查询的意图和上下文，选择最合适的引擎或编排多个引擎。
    """

    def __init__(self):
        self.engines: List[BaseEngine] = []
        self.intent_patterns = self._build_intent_patterns()

    def register(self, engine: BaseEngine):
        """注册引擎"""
        self.engines.append(engine)

    def _build_intent_patterns(self) -> dict:
        """构建意图匹配正则"""
        return {
            "tcm": re.compile(
                r"(体质|中医|食疗|气虚|阳虚|阴虚|湿热|痰湿|血瘀|气郁|平和|"
                r"寒热|温凉|归经|养生|调理|上火|湿气|补血|补气|补肾)"
            ),
            "seasonal": re.compile(
                r"(节气|立春|立夏|立秋|立冬|春分|夏至|秋分|冬至|"
                r"时令|应季|冬天吃什么|夏天吃什么)"
            ),
            "pregnancy": re.compile(
                r"(备孕|怀孕|孕期|叶酸|孕妇|产妇|哺乳期|产后)"
            ),
            "nutrition": re.compile(
                r"(热量|卡路里|蛋白质|脂肪|碳水|减肥|减重|增肌|营养)"
            ),
        }

    def _classify_intent(self, query: str, context: AIContext) -> List[tuple]:
        """
        意图分类，返回 (intent_name, confidence) 列表，按置信度排序。
        """
        scores = []
        query_lower = query.lower()

        for intent_name, pattern in self.intent_patterns.items():
            matches = len(pattern.findall(query_lower))
            score = min(matches * 0.3, 0.9)  # 每个关键词 +0.3，最高 0.9
            scores.append((intent_name, score))

        # 上下文增强：如果用户有中医体质档案，tcm 意图加分
        if context.tcm_constitution:
            for i, (intent, score) in enumerate(scores):
                if intent == "tcm":
                    scores[i] = (intent, min(score + 0.2, 1.0))

        # 按置信度降序
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    async def route(
        self,
        query: str,
        context: AIContext,
        preferred_engine: Optional[str] = None,
        stream: bool = False,
    ) -> EngineResult | AsyncGenerator[str, None]:
        """
        路由主入口。
        1. 如果指定了 preferred_engine，直接使用
        2. 否则进行意图识别 + 引擎匹配
        3. 支持多引擎编排（如：中医+节气联合推荐）
        """
        # 1. 指定引擎优先
        if preferred_engine:
            engine = self._get_engine(preferred_engine)
            if engine:
                return await engine.execute(query, context, stream)
            raise ValueError(f"Unknown engine: {preferred_engine}")

        # 2. 意图分类
        intents = self._classify_intent(query, context)

        # 3. 引擎匹配：取置信度最高的意图，找到能处理的引擎
        best_engine = None
        best_score = 0.0

        for intent_name, intent_score in intents:
            for engine in self.engines:
                engine_score = engine.can_handle(intent_name, context)
                combined_score = intent_score * engine_score
                if combined_score > best_score:
                    best_score = combined_score
                    best_engine = engine

        # 4. 兜底：如果没有任何引擎高置信度匹配，使用 NutritionEngine
        if not best_engine or best_score < 0.3:
            best_engine = self._get_engine("nutrition")

        # 5. 执行（未来可扩展为并行执行多个引擎再合并结果）
        return await best_engine.execute(query, context, stream)

    def _get_engine(self, name: str) -> Optional[BaseEngine]:
        for engine in self.engines:
            if engine.name == name:
                return engine
        return None

    async def multi_engine_compose(
        self,
        query: str,
        context: AIContext,
        engines: List[str],
    ) -> EngineResult:
        """
        【高级功能】多引擎编排。
        例如：用户问"冬天气虚体质该吃什么？"
        → 同时调用 TCM Engine + Seasonal Engine，合并结果。
        """
        results = []
        for engine_name in engines:
            engine = self._get_engine(engine_name)
            if engine:
                result = await engine.execute(query, context, stream=False)
                results.append(result)

        # 合并逻辑（简化版：以第一个引擎为主，其余作为补充）
        primary = results[0]
        supplementary = [r.content for r in results[1:]]

        composed_content = (
            f"{primary.content}\n\n"
            f"【补充建议】\n"
            + "\n".join(f"- {s[:200]}" for s in supplementary)
        )

        return EngineResult(
            content=composed_content,
            structured_data=primary.structured_data,
            engine_name="composed",
            model_used=primary.model_used,
            tokens_used=sum(r.tokens_used for r in results),
            cost_yuan=sum(r.cost_yuan for r in results),
        )
```

### 3.6 具体引擎实现示例

#### `NutritionEngine`（现有功能迁移）

```python
# app/services/ai/nutrition_engine.py
from .base_engine import BaseEngine, AIContext, EngineResult


class NutritionEngine(BaseEngine):
    name = "nutrition"
    description = "营养分析与餐食生成引擎"
    default_model = "qwen-plus"

    def can_handle(self, intent: str, context: AIContext) -> float:
        if intent == "nutrition":
            return 1.0
        if intent == "pregnancy":
            return 0.6  # 也能处理，但不如专用引擎
        return 0.3

    async def execute(self, query, context, stream=False):
        # 1. 构建系统提示
        system_prompt = self._build_system_prompt(context)

        # 2. 根据查询类型选择模板
        if "生成" in query or "计划" in query or "吃什么" in query:
            user_prompt = self.prompt_manager.render(
                "nutrition/generate_meal", context
            )
        elif "解析" in query or "热量" in query:
            user_prompt = self.prompt_manager.render(
                "nutrition/parse_food", context, extra=query
            )
        else:
            user_prompt = query

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # 3. 调用模型
        if stream:
            return self.model_gateway.chat(
                model=self.default_model,
                messages=messages,
                stream=True,
            )

        result = await self.model_gateway.chat(
            model=self.default_model,
            messages=messages,
            stream=False,
            response_format={"type": "json_object"} if "json" in query.lower() else None,
        )

        # 4. 安全过滤
        filtered_content = self._safety_check(result["content"])

        return EngineResult(
            content=filtered_content,
            structured_data=self._try_parse_json(filtered_content),
            engine_name=self.name,
            model_used=result["model"],
            tokens_used=result["tokens"],
            cost_yuan=result["cost_yuan"],
            response_time_ms=result["response_time_ms"],
        )

    def _safety_check(self, content: str) -> str:
        from .safety_filter import SafetyFilter
        return SafetyFilter.filter(content)

    def _try_parse_json(self, content: str) -> Optional[dict]:
        import json
        try:
            return json.loads(content)
        except:
            return None
```

#### `TCMEngine`（中医引擎【预留实现】）

```python
# app/services/ai/tcm_engine.py
from .base_engine import BaseEngine, AIContext, EngineResult


class TCMEngine(BaseEngine):
    name = "tcm"
    description = "中医体质辨识与食疗推荐引擎"
    # 中医场景用更强的模型，未来可切换为微调模型
    default_model = "qwen-plus"

    def can_handle(self, intent: str, context: AIContext) -> float:
        if intent == "tcm":
            return 1.0
        # 如果用户有中医体质，对养生/健康类查询也提高权重
        if context.tcm_constitution and intent in ("nutrition", "health"):
            return 0.4
        return 0.1

    async def execute(self, query, context, context, stream=False):
        # 1. RAG 检索中医知识
        knowledge = await self._retrieve_knowledge(query)
        knowledge_text = "\n".join(
            f"[知识库] {k['content']}" for k in knowledge
        ) if knowledge else ""

        # 2. 构建系统提示（包含用户体质信息）
        system_prompt = self._build_system_prompt(context, extra_context=knowledge_text)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        # 3. 调用模型
        result = await self.model_gateway.chat(
            model=self.default_model,
            messages=messages,
            temperature=0.5,  # 中医建议需要更严谨，降低随机性
            stream=stream,
        )

        if stream:
            return result

        return EngineResult(
            content=result["content"],
            sources=[k["source"] for k in knowledge],
            engine_name=self.name,
            model_used=result["model"],
            tokens_used=result["tokens"],
            cost_yuan=result["cost_yuan"],
            response_time_ms=result["response_time_ms"],
        )
```

### 3.7 FastAPI 集成方式

```python
# app/api/v1/chat.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.services.ai.router import EngineRouter
from app.services.ai.base_engine import AIContext

router = APIRouter()

# 全局单例（实际用依赖注入管理生命周期）
ai_router = EngineRouter()


def get_ai_router() -> EngineRouter:
    return ai_router


@router.post("/chat/send")
async def send_message(
    req: ChatRequest,
    router: EngineRouter = Depends(get_ai_router),
    current_user: User = Depends(get_current_user),
):
    """
    统一对话接口。
    根据用户查询内容自动路由到最合适的 AI 引擎。
    """
    # 构建上下文
    context = await _build_ai_context(current_user.id)

    if req.stream:
        async def stream_generator():
            gen = await router.route(
                query=req.message,
                context=context,
                preferred_engine=req.engine,  # 可选强制指定引擎
                stream=True,
            )
            async for chunk in gen:
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
        )

    # 非流式
    result = await router.route(
        query=req.message,
        context=context,
        preferred_engine=req.engine,
        stream=False,
    )

    # 存入数据库
    await _save_chat_message(current_user.id, req.message, result)

    return {
        "content": result.content,
        "structured_data": result.structured_data,
        "engine": result.engine_name,
        "model": result.model_used,
        "tokens": result.tokens_used,
    }


async def _build_ai_context(user_id: str) -> AIContext:
    """从数据库组装用户上下文"""
    # 查询用户基本信息
    user = await get_user_by_id(user_id)
    # 查询今日饮食记录
    today_records = await get_today_diet(user_id)
    # 查询近7天摘要
    weekly = await get_weekly_summary(user_id)
    # 查询当前中医体质
    tcm = await get_current_tcm_profile(user_id)
    # 查询当前节气
    solar_term = get_current_solar_term()

    return AIContext(
        user_id=user_id,
        goal_type=user.goal_type,
        body_info={
            "height": user.height_cm,
            "weight": user.current_weight,
            "age": user.age,
            "gender": user.gender,
        },
        today_records=today_records,
        weekly_summary=weekly,
        tcm_constitution=tcm.primary_constitution if tcm else None,
        solar_term=solar_term,
        menstrual_phase=await get_menstrual_phase(user_id),
    )
```

---

## 4. RAG 知识库设计（扩展）

### 4.1 向量数据库选型

| 方案 | 推荐度 | 说明 |
|------|--------|------|
| **PGVector** | ⭐⭐⭐⭐⭐ | 与现有 PostgreSQL 同库，零额外运维 |
| Milvus | ⭐⭐⭐ | 独立向量库，性能好但增加复杂度 |
| Redis Stack | ⭐⭐⭐ | 如果已有 Redis，可考虑 |

### 4.2 知识库表设计（PGVector）

```sql
-- 扩展：安装 pgvector
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    namespace       VARCHAR(50) NOT NULL,           -- 知识库命名空间
    -- namespace: nutrition / tcm / seasonal / pregnancy
    source_type     VARCHAR(30) NOT NULL,           -- 来源类型
    -- source_type: classical_text / expert_entry / ai_generated / medical_reference
    source_id       VARCHAR(100),                   -- 来源标识（如书名+章节）
    title           VARCHAR(200),                   -- 标题
    content         TEXT NOT NULL,                  -- 文本内容
    content_vector  vector(1536),                   -- 向量（使用通义千问嵌入模型）
    metadata        JSONB DEFAULT '{}',             -- 附加元数据
    -- metadata: {"constitution": "qi_deficiency", "season": "winter", ...}
    verified        BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_knowledge_namespace ON knowledge_chunks(namespace);
CREATE INDEX idx_knowledge_vector ON knowledge_chunks USING ivfflat (content_vector vector_cosine_ops)
    WITH (lists = 100);
```

### 4.3 知识填充策略

| 阶段 | 内容 | 方式 |
|------|------|------|
| MVP | 中医体质定义、20 个食疗方 | 专家录入 + 向量化 |
| V1.1 | 《食疗本草》经典方剂 | OCR + AI 清洗 + 专家审核 + 向量化 |
| V1.2 | 用户高频问题 → 优质回答 | AI 生成 + 专家审核后入库 |
| V2.0 | 自动从对话中抽取新知识 | 自动抽取 + 人工审核流水线 |

---

## 5. 迁移路线图

| 阶段 | 工作 | 对现有代码的影响 |
|------|------|-----------------|
| **Phase 0（当前）** | 保留现有 `ai_service.py`，保持不变 | 零影响 |
| **Phase 1** | 新建 `services/ai/` 目录，实现 `BaseEngine` + `ModelGateway` + `NutritionEngine` | 并行开发，API 层切换调用入口 |
| **Phase 2** | 迁移食物解析、餐食生成、AI 对话至新架构 | 废弃旧 `ai_service.py` |
| **Phase 3** | 实现 `TCMEngine` + 中医数据库 + Prompt 模板 | 新增，不影响既有功能 |
| **Phase 4** | 实现 `SeasonalEngine`、`PregnancyEngine` | 新增 |
| **Phase 5** | RAG 向量库接入 | 所有引擎增强 |

---

*文档版本：v1.0 | 创建日期：2026-06-07*
