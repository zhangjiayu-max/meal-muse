"""知识库服务 — 向量检索和知识管理"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ChromaDB 目录（与 investment-analyzer 隔离）
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CHROMA_DIR = PROJECT_ROOT / "data" / "chromadb"


def get_chroma_collection():
    """获取 ChromaDB collection"""
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name="meal_muse_knowledge",
        metadata={"hnsw:space": "cosine"},
    )
    return client, collection


def get_embedding(text: str) -> list[float]:
    """获取文本的 embedding 向量"""
    import httpx
    from app.config import get_settings

    settings = get_settings()
    api_key = settings.DASHSCOPE_API_KEY

    if not api_key:
        raise Exception("未配置 DASHSCOPE_API_KEY")

    api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

    resp = httpx.post(
        api_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "text-embedding-v3",
            "input": text,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["embedding"]


async def search_knowledge(
    query: str,
    top_k: int = 5,
    category: str = None,
) -> list[dict]:
    """检索相关知识"""
    try:
        client, collection = get_chroma_collection()

        # 检查 collection 是否为空
        if collection.count() == 0:
            logger.info("知识库为空，请先运行蒸馏脚本导入知识")
            return []

        # 获取查询的 embedding
        query_embedding = get_embedding(query)

        # 构建过滤条件
        where = None
        if category:
            where = {"category": category}

        # 查询
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        knowledge = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0

                # 转换为相似度（余弦距离越小越相似）
                similarity = 1 - distance

                # 只返回相似度大于 0.3 的结果
                if similarity > 0.3:
                    knowledge.append({
                        "content": doc,
                        "source": metadata.get("source", "未知来源"),
                        "category": metadata.get("category", "general"),
                        "title": metadata.get("title", ""),
                        "similarity": round(similarity, 3),
                    })

        return knowledge

    except Exception as e:
        logger.warning(f"知识库检索失败: {e}")
        return []


async def add_knowledge(
    title: str,
    content: str,
    source: str,
    category: str = "general",
    metadata: dict = None,
) -> str:
    """添加知识到向量库"""
    import hashlib

    client, collection = get_chroma_collection()

    # 生成唯一 ID
    knowledge_id = hashlib.md5(f"{source}_{title}".encode()).hexdigest()

    # 获取 embedding
    embedding = get_embedding(content)

    # 构建 metadata
    meta = {
        "title": title,
        "source": source,
        "category": category,
    }
    if metadata:
        meta.update(metadata)

    # 写入
    collection.upsert(
        ids=[knowledge_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[meta],
    )

    logger.info(f"添加知识: {title} (id={knowledge_id})")
    return knowledge_id


async def delete_knowledge_by_source(source: str) -> int:
    """删除指定来源的所有知识"""
    try:
        client, collection = get_chroma_collection()

        results = collection.get(
            where={"source": source},
            include=[],
        )

        if results["ids"]:
            collection.delete(ids=results["ids"])
            return len(results["ids"])
        return 0
    except Exception as e:
        logger.warning(f"删除知识失败: {e}")
        return 0


async def get_knowledge_stats() -> dict:
    """获取知识库统计"""
    try:
        client, collection = get_chroma_collection()

        count = collection.count()

        # 获取所有 metadata 统计分类
        if count > 0:
            results = collection.get(include=["metadatas"])

            categories = {}
            sources = {}
            for metadata in results["metadatas"]:
                cat = metadata.get("category", "未分类")
                source = metadata.get("source", "未知来源")
                categories[cat] = categories.get(cat, 0) + 1
                sources[source] = sources.get(source, 0) + 1

            return {
                "total": count,
                "categories": categories,
                "sources": sources,
            }

        return {"total": 0, "categories": {}, "sources": {}}
    except Exception as e:
        logger.warning(f"获取知识库统计失败: {e}")
        return {"total": 0, "categories": {}, "sources": {}}
