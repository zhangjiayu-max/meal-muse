# 📚 RAG 知识库实现方案

> MealMuse AI 对话专业知识库建设方案

---

## 📋 概述

当前 AI 对话依赖 Prompt 注入专业知识，存在以下局限：
- 知识量受 token 限制（约 4000 字）
- 无法引用具体书籍/文献来源
- 知识更新需要修改代码

RAG（Retrieval-Augmented Generation）方案可以解决这些问题。

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        用户提问                              │
│                  "备孕期间应该吃什么？"                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    向量化 (Embedding)                         │
│              将用户问题转为向量表示                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 向量数据库检索 (Top 5)                        │
│    在知识库中找到最相关的 5 个知识片段                         │
│                                                             │
│    命中：                                                   │
│    1. 《孕产妇膳食指南》P23: "备孕女性每日需补充叶酸400μg..."   │
│    2. 《中医饮食营养学》P156: "备孕宜食黑豆、黑芝麻..."        │
│    3. 《中国食物成分表》: "菠菜叶酸含量..."                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Prompt 组装                               │
│                                                             │
│    System: 你是 MealMuse...                                 │
│    Context: [检索到的知识片段]                                │
│    User: 用户问题                                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    通义千问生成                               │
│                                                             │
│    "备孕期间建议补充以下营养素：                               │
│     1. 叶酸：每天400μg，可从菠菜、豆类获取...                  │
│     2. 铁：每天20mg，推荐红肉、猪肝...                        │
│     （参考：《孕产妇膳食指南》《中医饮食营养学》）"              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 知识库内容规划

### 第一批（核心知识）

| 序号 | 类别 | 资料来源 | 内容量 | 优先级 |
|------|------|----------|--------|--------|
| 1 | 食物营养 | 《中国食物成分表》 | ~2000 种食物 | P0 |
| 2 | 中医食疗 | 《中医饮食营养学》 | ~300 条食疗方 | P0 |
| 3 | 经期饮食 | 《女性营养学》 | ~100 条建议 | P0 |
| 4 | 备孕营养 | 《孕产妇膳食指南》 | ~100 条建议 | P0 |

### 第二批（扩展知识）

| 序号 | 类别 | 资料来源 | 内容量 | 优先级 |
|------|------|----------|--------|--------|
| 5 | 体质养生 | 《中医体质学》 | ~200 条建议 | P1 |
| 6 | 运动营养 | 《运动营养学》 | ~150 条建议 | P1 |
| 7 | 减脂饮食 | 《临床营养学》 | ~100 条建议 | P1 |
| 8 | 节气养生 | 《二十四节气养生》 | ~100 条建议 | P2 |

---

## 🛠️ 技术选型

### 向量数据库

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **Chroma** | 轻量、Python 原生、易上手 | 性能一般 | ⭐⭐⭐⭐⭐ (MVP) |
| **Milvus** | 高性能、分布式 | 部署复杂 | ⭐⭐⭐ (生产) |
| **Qdrant** | 高性能、Rust 实现 | 社区较小 | ⭐⭐⭐⭐ |
| **Pinecone** | 全托管、无需运维 | 收费 | ⭐⭐⭐ |

**推荐**：MVP 阶段使用 **Chroma**（本地部署、零成本）

### Embedding 模型

| 方案 | 维度 | 价格 | 推荐度 |
|------|------|------|--------|
| **通义千问 text-embedding-v3** | 1024 | 0.0007元/千tokens | ⭐⭐⭐⭐⭐ |
| **OpenAI text-embedding-3-small** | 1536 | $0.02/1M tokens | ⭐⭐⭐⭐ |
| **BGE-M3 (本地)** | 1024 | 免费 | ⭐⭐⭐ |

**推荐**：使用 **通义千问 text-embedding-v3**（已有 API Key）

---

## 📁 数据处理流程

### 1. 知识文档准备

```
knowledge/
├── raw/                    # 原始文档
│   ├── food_nutrition/     # 食物营养
│   │   ├── china_food_composition.csv
│   │   └── common_foods.json
│   ├── tcm_diet/           # 中医食疗
│   │   ├── tcm_diet_therapy.md
│   │   └── constitution_diet.md
│   ├── pregnancy/          # 备孕营养
│   │   └── pregnancy_nutrition.md
│   └── menstrual/          # 经期饮食
│       └── menstrual_diet.md
├── processed/              # 处理后的文档
│   ├── chunks/             # 分块后的文档
│   └── embeddings/         # 向量化后的数据
└── scripts/                # 处理脚本
    ├── ingest.py           # 数据导入
    └── chunk.py            # 文档分块
```

### 2. 文档分块策略

```python
# 分块参数
CHUNK_SIZE = 500        # 每块约 500 字
CHUNK_OVERLAP = 50      # 重叠 50 字
SEPARATORS = ["\n\n", "\n", "。", "；", " "]

# 分块示例
原文: "备孕期间需要补充叶酸。叶酸可以预防胎儿神经管缺陷。建议每日摄入400μg叶酸。
      富含叶酸的食物包括：菠菜、芦笋、豆类、柑橘类水果。
      如果饮食中无法获取足够的叶酸，可以考虑服用叶酸补充剂。"

分块1: "备孕期间需要补充叶酸。叶酸可以预防胎儿神经管缺陷。建议每日摄入400μg叶酸。"
分块2: "叶酸可以预防胎儿神经管缺陷。建议每日摄入400μg叶酸。富含叶酸的食物包括：菠菜、芦笋、豆类、柑橘类水果。"
分块3: "富含叶酸的食物包括：菠菜、芦笋、豆类、柑橘类水果。如果饮食中无法获取足够的叶酸，可以考虑服用叶酸补充剂。"
```

### 3. 元数据设计

```python
{
    "chunk_id": "chunk_001",
    "content": "备孕期间需要补充叶酸...",
    "metadata": {
        "source": "《孕产妇膳食指南》",
        "chapter": "第三章 孕前营养",
        "page": 23,
        "category": "pregnancy",      # pregnancy/tcm/menstrual/nutrition
        "tags": ["叶酸", "备孕", "营养素"],
        "created_at": "2026-06-13"
    },
    "embedding": [0.123, -0.456, ...]  # 1024 维向量
}
```

---

## 💻 代码实现

### 1. 安装依赖

```bash
pip install chromadb dashscope
```

### 2. 知识库服务

```python
# app/services/knowledge_service.py

import chromadb
from chromadb.config import Settings
from dashscope import TextEmbedding
from app.config import get_settings

settings = get_settings()

# 初始化 ChromaDB
chroma_client = chromadb.PersistentClient(path="./data/chromadb")

# 获取或创建集合
knowledge_collection = chroma_client.get_or_create_collection(
    name="meal_muse_knowledge",
    metadata={"hnsw:space": "cosine"}
)


async def embed_text(text: str) -> list[float]:
    """调用通义千问 Embedding API"""
    response = TextEmbedding.call(
        model="text-embedding-v3",
        input=text,
        api_key=settings.DASHSCOPE_API_KEY,
    )
    return response.output["embeddings"][0]["embedding"]


async def search_knowledge(query: str, top_k: int = 5) -> list[dict]:
    """检索相关知识"""
    query_embedding = await embed_text(query)

    results = knowledge_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    knowledge = []
    for i, doc in enumerate(results["documents"][0]):
        knowledge.append({
            "content": doc,
            "source": results["metadatas"][0][i].get("source", "未知来源"),
            "category": results["metadatas"][0][i].get("category", "general"),
            "relevance": 1 - results["distances"][0][i],  # 转换为相似度
        })

    return knowledge


async def add_knowledge(content: str, metadata: dict):
    """添加知识到向量库"""
    embedding = await embed_text(content)
    doc_id = f"doc_{knowledge_collection.count() + 1}"

    knowledge_collection.add(
        ids=[doc_id],
        documents=[content],
        embeddings=[embedding],
        metadatas=[metadata],
    )
```

### 3. 修改对话服务

```python
# app/services/chat_service.py (修改)

from app.services.knowledge_service import search_knowledge

async def chat_send(
    db: AsyncSession,
    current_user: User,
    content: str,
    session_id: uuid.UUID | None = None,
) -> dict:
    session_id = session_id or uuid.uuid4()

    # 1. 获取用户上下文
    context = await get_user_context(db, current_user)

    # 2. 检索相关知识
    knowledge = await search_knowledge(content, top_k=3)
    knowledge_text = ""
    if knowledge:
        knowledge_text = "\n\n【参考知识】\n"
        for k in knowledge:
            knowledge_text += f"- {k['content']}（来源：{k['source']}）\n"

    # 3. 加载历史对话
    history_messages = await load_history(db, current_user.id, session_id)

    # 4. 组装消息（加入检索到的知识）
    messages = [{"role": "system", "content": SYSTEM_PROMPT + knowledge_text + "\n\n" + context}]
    messages.extend(history_messages)
    messages.append({"role": "user", "content": content})

    # 5. 调用 AI
    ai_response, tokens = await call_ai(messages)

    # ... 后续保存逻辑不变
```

---

## 📊 数据导入脚本

```python
# scripts/ingest_knowledge.py

import asyncio
import json
from app.services.knowledge_service import add_knowledge


async def ingest_food_nutrition():
    """导入食物营养数据"""
    with open("knowledge/raw/food_nutrition/common_foods.json", "r") as f:
        foods = json.load(f)

    for food in foods:
        content = f"{food['name']}：每100g含{food['calories']}kcal，蛋白质{food['protein']}g，脂肪{food['fat']}g，碳水{food['carbs']}g"
        await add_knowledge(content, {
            "source": "中国食物成分表",
            "category": "nutrition",
            "tags": [food["name"], "营养成分"],
        })

    print(f"导入 {len(foods)} 条食物营养数据")


async def ingest_tcm_diet():
    """导入中医食疗数据"""
    with open("knowledge/raw/tcm_diet/tcm_diet_therapy.md", "r") as f:
        content = f.read()

    # 按段落分块
    chunks = content.split("\n\n")
    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) > 50:  # 过滤太短的段落
            await add_knowledge(chunk.strip(), {
                "source": "中医饮食营养学",
                "category": "tcm",
                "tags": ["中医", "食疗"],
            })

    print(f"导入 {len(chunks)} 条中医食疗数据")


async def main():
    await ingest_food_nutrition()
    await ingest_tcm_diet()
    # ... 导入其他数据


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📅 实施计划

| 阶段 | 任务 | 时间 | 产出 |
|------|------|------|------|
| **Phase 1** | Prompt 优化（已完成） | 1 天 | AI 回复质量提升 |
| **Phase 2** | 准备知识文档 | 3-5 天 | 2000+ 条结构化知识 |
| **Phase 3** | 实现 RAG 服务 | 3-5 天 | 向量检索功能 |
| **Phase 4** | 数据导入 | 1-2 天 | 知识库上线 |
| **Phase 5** | 测试优化 | 2-3 天 | 质量评估、调优 |

**预计总时间**：2-3 周

---

## 🎯 效果对比

### 优化前（纯 Prompt）

```
用户: 备孕期间应该吃什么？

AI: 备孕期间建议补充叶酸、铁、DHA等营养素...
    （通用建议，无具体来源）
```

### 优化后（Prompt + 知识库）

```
用户: 备孕期间应该吃什么？

AI: 备孕期间建议重点补充以下营养素：

    1. 叶酸：每天400μg
       - 推荐食物：菠菜（每100g含叶酸110μg）、芦笋、豆类
       - 建议：孕前3个月开始补充
       （参考：《孕产妇膳食指南》P23）

    2. 铁：每天20mg
       - 推荐食物：红肉、猪肝、黑木耳
       - 搭配维C促进吸收
       （参考：《中国食物成分表》）

    3. DHA：每周2-3次深海鱼
       - 推荐：三文鱼、鳕鱼
       （参考：《孕产妇膳食指南》P45）

    🌿 中医食疗建议：
    - 黑豆、黑芝麻：补肾益精
    - 红枣、枸杞：养血安神
    （参考：《中医饮食营养学》P156）
```

---

## 📝 注意事项

1. **版权问题**：确保使用的知识文档有合法授权
2. **数据质量**：人工审核导入的知识，避免错误信息
3. **更新机制**：建立知识库定期更新流程
4. **监控告警**：监控检索质量，低相关度时 fallback 到纯 Prompt
5. **成本控制**：Embedding API 调用费用，批量处理降低成本

---

*文档版本：v1.0*
*创建时间：2026-06-13*
