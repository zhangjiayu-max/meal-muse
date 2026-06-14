#!/usr/bin/env python3
"""MealMuse 知识蒸馏脚本 — 将书籍/文档蒸馏为营养健康知识库。

完整流程：清理旧数据 → PDF → OCR → Markdown → 蒸馏 → 质量审核 → ChromaDB

用法：
    # 完整流程：PDF → OCR → Markdown → 蒸馏 → 入库
    python3 scripts/distill.py full /path/to/book.pdf --name 书名

    # 只做 OCR：PDF → Markdown
    python3 scripts/distill.py ocr /path/to/book.pdf --name 书名

    # 只做蒸馏：从已有 Markdown 文件
    python3 scripts/distill.py distill /path/to/book.md

    # 清理某书的旧数据
    python3 scripts/distill.py clean --name 书名

    # 查看已蒸馏书籍列表
    python3 scripts/distill.py list

    # 重建向量索引
    python3 scripts/distill.py reindex --name 书名
    python3 scripts/distill.py reindex  # 重建所有

    # 试运行（不写入数据库）
    python3 scripts/distill.py full /path/to/book.pdf --name 书名 --dry-run
"""

import sys
import json
import re
import time
import hashlib
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings

settings = get_settings()

# ===== 数据目录（与 investment-analyzer 完全隔离） =====
PROJECT_ROOT = Path(__file__).parent.parent.parent
BOOKS_DIR = PROJECT_ROOT / "data" / "books"
CHROMA_DIR = PROJECT_ROOT / "data" / "chromadb"

# 确保目录存在
BOOKS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════
# LLM 调用（使用通义千问）
# ══════════════════════════════════════════════════════════════

def call_llm(messages: list, temperature: float = 0.2, max_tokens: int = 4000) -> str:
    """调用通义千问 API"""
    import httpx

    api_key = settings.DASHSCOPE_API_KEY
    if not api_key:
        raise Exception("未配置 DASHSCOPE_API_KEY")

    api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    for attempt in range(3):
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "qwen-plus",
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < 2:
                time.sleep(1 + attempt)
            else:
                raise


# ══════════════════════════════════════════════════════════════
# OCR 模块：PDF → Markdown
# ══════════════════════════════════════════════════════════════

def detect_pdf_type(pdf_path: str) -> tuple[str, int]:
    """检测 PDF 类型，返回 (类型, 总页数)。"""
    from PyPDF2 import PdfReader

    reader = PdfReader(pdf_path)
    total = len(reader.pages)

    # 抽样检测
    sample_size = min(10, total)
    has_text = 0

    for i in range(sample_size):
        text = reader.pages[i].extract_text() or ""
        if len(text.strip()) > 100:
            has_text += 1

    ratio = has_text / sample_size if sample_size > 0 else 0

    if ratio > 0.5:
        return "text", total
    else:
        return "scanned", total


def extract_text_from_pdf(pdf_path: str) -> str:
    """从文字版 PDF 提取全文。"""
    from PyPDF2 import PdfReader

    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def pdf_to_markdown(pdf_path: str, book_title: str) -> str:
    """PDF 转 Markdown。"""
    pdf_path = Path(pdf_path)
    md_file = BOOKS_DIR / f"{book_title}.md"

    # 检查缓存
    if md_file.exists():
        existing = md_file.read_text(encoding="utf-8")
        if len(existing) > 1000:
            print(f"  发现已有 Markdown 文件: {md_file} ({len(existing)} 字)")
            return existing

    # 检测类型
    pdf_type, total_pages = detect_pdf_type(str(pdf_path))
    print(f"  PDF 类型: {pdf_type} ({total_pages} 页)")

    if pdf_type == "text":
        print(f"  提取文字...")
        raw_text = extract_text_from_pdf(str(pdf_path))
        print(f"  提取完成: {len(raw_text)} 字")
    else:
        # 扫描版 PDF 需要 OCR，这里简化处理
        print(f"  扫描版 PDF 需要 OCR，请使用其他工具先转换为文字版")
        print(f"  推荐工具：Adobe Acrobat、ABBYY FineReader、或在线 OCR 服务")
        sys.exit(1)

    # 保存 Markdown
    header = f"# {book_title}\n\n"
    header += f"> 由 MealMuse 蒸馏系统生成\n"
    header += f"> 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"

    md_file.write_text(header + raw_text, encoding="utf-8")
    print(f"  已保存 Markdown: {md_file} ({len(raw_text)} 字)")

    return raw_text


# ══════════════════════════════════════════════════════════════
# 蒸馏模块：Markdown → 知识点
# ══════════════════════════════════════════════════════════════

def split_into_chunks(text: str, max_chars: int = 3000) -> list[dict]:
    """将文本分割成适合 LLM 处理的块。"""
    sections = []
    current_title = "前言"
    current_lines = []

    for line in text.split('\n'):
        is_header = False
        if re.match(r'^#{1,4}\s+', line):
            is_header = True
            current_title = line.lstrip('#').strip()
        elif re.match(r'^[\s]*(第[一二三四五六七八九十百千\d]+[章部篇节].*)$', line):
            is_header = True
            current_title = line.strip()

        if is_header:
            if current_lines:
                sections.append({
                    "title": current_title,
                    "content": '\n'.join(current_lines)
                })
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({
            "title": current_title,
            "content": '\n'.join(current_lines)
        })

    # 如果没有章节结构，按段落块切分
    if len(sections) <= 1:
        sections = []
        paragraphs = text.split('\n\n')
        current_chunk = []
        current_len = 0
        chunk_idx = 1

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if current_len + len(para) > max_chars and current_chunk:
                sections.append({
                    "title": f"第 {chunk_idx} 部分",
                    "content": '\n\n'.join(current_chunk)
                })
                chunk_idx += 1
                current_chunk = []
                current_len = 0
            current_chunk.append(para)
            current_len += len(para)

        if current_chunk:
            sections.append({
                "title": f"第 {chunk_idx} 部分",
                "content": '\n\n'.join(current_chunk)
            })

    # 将大块再切分成小块
    chunks = []
    for section in sections:
        content = section["content"].strip()
        if len(content) < 100:
            continue

        if len(content) <= max_chars:
            chunks.append({
                "title": section["title"],
                "content": content
            })
        else:
            lines = content.split('\n')
            current_chunk = []
            current_len = 0

            for line in lines:
                if current_len + len(line) > max_chars and current_chunk:
                    chunks.append({
                        "title": section["title"],
                        "content": '\n'.join(current_chunk)
                    })
                    current_chunk = []
                    current_len = 0
                current_chunk.append(line)
                current_len += len(line)

            if current_chunk:
                chunks.append({
                    "title": section["title"],
                    "content": '\n'.join(current_chunk)
                })

    return chunks


def extract_knowledge(chunk: str, chapter_title: str, book_title: str) -> list[dict]:
    """用 LLM 从文本块中提取高质量知识点。"""
    prompt = f"""你是营养健康知识提取专家。请从以下书籍内容中提取**最核心、最有实用价值**的营养健康知识点。

## 书名：{book_title}
## 章节：{chapter_title}

## 提取原则（严格遵守）

**宁缺毋滥**：宁可少提，不可滥提。每个知识点必须有**独特的实用价值**。

### 必须提取的内容（至少满足一项）
- 有具体数据的营养知识（如"每100g菠菜含铁2.9mg"）
- 有明确功效的食疗方案（如"红枣枸杞茶可以补气养血"）
- 有科学依据的饮食建议（如"孕期每日需补充400μg叶酸"）
- 有具体步骤的烹饪/食疗方法
- 中医食疗的具体配方和功效

### 必须排除的内容（发现即删除）
- ❌ 纯概念定义（如"什么是蛋白质"）
- ❌ 常识性内容（如"要多吃蔬菜"）
- ❌ 笼统建议（如"注意饮食均衡"）
- ❌ 广告/营销内容
- ❌ 与其他知识点重复的内容

### 分类标签
- nutrition: 营养成分、食物营养数据
- tcm_diet: 中医食疗、药膳
- pregnancy: 备孕/孕期营养
- menstrual: 经期饮食调理
- fitness: 健身/运动营养
- weight_loss: 减脂/减重饮食
- chronic: 慢性病饮食管理
- recipe: 食谱/烹饪方法

### 输出格式（JSON 数组）
[
  {{"title": "精炼的标题（10-20字）", "category": "分类标签", "content": "200-500字的详细内容，必须包含具体数据/配方/步骤", "keywords": ["关键词1", "关键词2", "关键词3"], "importance": 1-10, "source": "引用来源（如页码、章节）"}},
  ...
]

**重要**：如果本段内容没有值得提取的高质量知识点，直接返回空数组 []。

## 文本内容：
{chunk}

只输出 JSON 数组，无其他文字。"""

    try:
        response = call_llm(
            messages=[
                {"role": "system", "content": "你是营养健康知识提取专家，只输出 JSON。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=4000,
        )

        # 解析 JSON
        content = response.strip()
        if content.startswith("```"):
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

        result = json.loads(content)

        if not isinstance(result, list):
            return []

        # 质量过滤
        valid = []
        for item in result:
            if not isinstance(item, dict):
                continue
            if not item.get("title") or not item.get("content"):
                continue
            if len(item["content"]) < 100:
                continue
            if len(item["title"]) < 3:
                continue
            item["source"] = book_title
            valid.append(item)

        return valid

    except Exception as e:
        print(f"  LLM 提取失败: {e}")
        return []


def deduplicate(knowledge: list[dict]) -> list[dict]:
    """基于标题+关键词去重。"""
    if not knowledge:
        return []

    unique = []
    seen_keys = set()

    for k in knowledge:
        title = k["title"].strip()
        keywords = k.get("keywords", [])
        keyword_str = "|".join(sorted(keywords[:3])) if keywords else ""
        key = f"{title[:20]}|{keyword_str}"

        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique.append(k)

    return unique


# ══════════════════════════════════════════════════════════════
# ChromaDB 操作
# ══════════════════════════════════════════════════════════════

def get_chroma_collection():
    """获取 ChromaDB collection（MealMuse 专用，数据隔离）"""
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name="meal_muse_knowledge",
        metadata={"hnsw:space": "cosine"},
    )
    return client, collection


def get_embedding(text: str) -> list[float]:
    """获取文本的 embedding 向量"""
    # 使用通义千问 embedding API
    import httpx

    api_key = settings.DASHSCOPE_API_KEY
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


def index_to_chroma(
    knowledge_id: str,
    title: str,
    content: str,
    source: str,
    category: str = "general",
):
    """将知识点写入 ChromaDB"""
    client, collection = get_chroma_collection()

    # 获取 embedding
    embedding = get_embedding(content)

    # 写入
    collection.upsert(
        ids=[knowledge_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{
            "title": title,
            "source": source,
            "category": category,
        }],
    )


def delete_chroma_by_source(source: str):
    """删除指定来源的所有向量"""
    try:
        client, collection = get_chroma_collection()

        # 获取该来源的所有文档
        results = collection.get(
            where={"source": source},
            include=[],
        )

        if results["ids"]:
            collection.delete(ids=results["ids"])
            return len(results["ids"])
        return 0
    except Exception as e:
        print(f"  删除向量失败: {e}")
        return 0


# ══════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════

def distill_from_text(
    text: str,
    book_title: str,
    dry_run: bool = False,
    concurrency: int = 2,
) -> int:
    """从文本进行蒸馏，返回保存条数。"""
    # 分块
    chunks = split_into_chunks(text)
    print(f"  分割为 {len(chunks)} 个文本块")

    # 过滤太短的块
    valid_chunks = [(i, c) for i, c in enumerate(chunks) if len(c["content"].strip()) >= 100]
    skipped = len(chunks) - len(valid_chunks)
    if skipped:
        print(f"  跳过 {skipped} 个过短的块")

    # 第一阶段：提取知识点
    print(f"\n  [第一阶段] 提取知识点（并发数: {concurrency}）...")
    all_knowledge = []
    completed = 0

    def _extract_one(args):
        idx, chunk = args
        knowledge = extract_knowledge(chunk["content"], chunk["title"], book_title)
        return idx, chunk["title"], knowledge

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(_extract_one, item): item for item in valid_chunks}
        for future in as_completed(futures):
            idx, title, knowledge = future.result()
            completed += 1
            all_knowledge.extend(knowledge)
            print(f"  [{completed}/{len(valid_chunks)}] {title[:40]}... → {len(knowledge)} 个知识点")

    print(f"\n  第一阶段提取完成: 共 {len(all_knowledge)} 个原始知识点")

    # 第二阶段：去重
    print(f"\n  [第二阶段] 去重处理...")
    deduplicated = deduplicate(all_knowledge)
    print(f"  去重: {len(all_knowledge)} → {len(deduplicated)} 条")

    # 存储
    if dry_run:
        print(f"\n  [DRY RUN] 以下是将要保存的 {len(deduplicated)} 条知识点：")
        for k in deduplicated:
            print(f"    [{k.get('category', '?')}] {k['title']}")
            print(f"      {k['content'][:100]}...")
        return 0

    print(f"\n  存储到知识库...")

    # 先清理旧数据
    print(f"  清理旧数据: {book_title}")
    deleted = delete_chroma_by_source(book_title)
    print(f"  已删除旧向量: {deleted} 条")

    saved = 0
    for i, k in enumerate(deduplicated):
        try:
            knowledge_id = hashlib.md5(f"{book_title}_{k['title']}_{i}".encode()).hexdigest()
            index_to_chroma(
                knowledge_id=knowledge_id,
                title=k["title"],
                content=k["content"],
                source=book_title,
                category=k.get("category", "general"),
            )
            saved += 1
        except Exception as e:
            print(f"  保存失败: {k['title']} - {e}")

    return saved


def cmd_distill(args):
    """只做蒸馏：从已有 Markdown 文件。"""
    input_path = Path(args.input)

    print(f"{'=' * 60}")
    print(f"知识蒸馏: {args.name or input_path.stem}")
    print(f"输入文件: {input_path}")
    print(f"{'=' * 60}")

    if not input_path.exists():
        print(f"错误: 文件不存在 {input_path}")
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")
    book_title = args.name or input_path.stem
    print(f"  文本长度: {len(text)} 字")

    saved = distill_from_text(
        text, book_title,
        dry_run=args.dry_run,
        concurrency=args.concurrency,
    )

    print(f"\n{'=' * 60}")
    print(f"蒸馏完成!")
    print(f"  书名: {book_title}")
    print(f"  成功保存: {saved} 条")
    print(f"{'=' * 60}")


def cmd_full(args):
    """完整流程：PDF → Markdown → 蒸馏 → 入库。"""
    input_path = Path(args.input)

    print(f"{'=' * 60}")
    print(f"完整蒸馏流程: {args.name}")
    print(f"输入文件: {input_path}")
    print(f"{'=' * 60}")

    if not input_path.exists():
        print(f"错误: 文件不存在 {input_path}")
        sys.exit(1)

    # 第一步：清理旧数据
    if not args.dry_run:
        print(f"\n[1/3] 清理旧数据...")
        deleted = delete_chroma_by_source(args.name)
        md_file = BOOKS_DIR / f"{args.name}.md"
        if md_file.exists():
            md_file.unlink()
            print(f"  已删除旧 Markdown: {md_file}")
        print(f"  已清理: {deleted} 条旧向量")

    # 第二步：PDF → Markdown
    print(f"\n[2/3] PDF → Markdown...")
    if input_path.suffix.lower() == '.pdf':
        text = pdf_to_markdown(str(input_path), args.name)
    elif input_path.suffix.lower() in ('.md', '.txt'):
        text = input_path.read_text(encoding="utf-8")
    else:
        print(f"错误: 不支持的文件格式 {input_path.suffix}")
        sys.exit(1)

    # 第三步：蒸馏
    print(f"\n[3/3] 知识蒸馏...")
    saved = distill_from_text(
        text, args.name,
        dry_run=args.dry_run,
        concurrency=args.concurrency,
    )

    print(f"\n{'=' * 60}")
    print(f"完整流程完成!")
    print(f"  书名: {args.name}")
    print(f"  Markdown: {BOOKS_DIR / f'{args.name}.md'}")
    print(f"  成功保存: {saved} 条知识点")
    print(f"{'=' * 60}")


def cmd_clean(args):
    """清理某书的旧数据。"""
    if not args.name:
        print("错误: 必须指定 --name 参数")
        sys.exit(1)

    print(f"{'=' * 60}")
    print(f"清理数据: {args.name}")
    print(f"{'=' * 60}")

    deleted = delete_chroma_by_source(args.name)
    print(f"  已删除 ChromaDB {deleted} 条向量")

    md_file = BOOKS_DIR / f"{args.name}.md"
    if md_file.exists():
        md_file.unlink()
        print(f"  已删除 Markdown 文件: {md_file}")

    print(f"\n清理完成!")


def cmd_list(args):
    """查看已蒸馏书籍列表。"""
    try:
        client, collection = get_chroma_collection()

        # 获取所有文档
        results = collection.get(include=["metadatas"])

        # 统计来源
        sources = {}
        for metadata in results["metadatas"]:
            source = metadata.get("source", "未知")
            cat = metadata.get("category", "未分类")
            if source not in sources:
                sources[source] = {"count": 0, "categories": set()}
            sources[source]["count"] += 1
            sources[source]["categories"].add(cat)

        if not sources:
            print("暂无已蒸馏的书籍")
            return

        print(f"{'=' * 60}")
        print(f"已蒸馏书籍列表（共 {len(sources)} 本）")
        print(f"{'=' * 60}")
        print(f"{'书名':<30} {'知识点数':>8} {'分类':<30}")
        print(f"{'-' * 60}")

        for source, info in sources.items():
            cats = ", ".join(info["categories"])
            print(f"{source:<30} {info['count']:>8} {cats:<30}")

        print(f"{'=' * 60}")
        print(f"总计: {sum(s['count'] for s in sources.values())} 条知识点")

    except Exception as e:
        print(f"获取列表失败: {e}")


def cmd_reindex(args):
    """重建向量索引。"""
    print(f"{'=' * 60}")
    print(f"重建向量索引: {args.name or '所有书籍'}")
    print(f"{'=' * 60}")

    # 这里简化处理，实际应该从某个地方读取知识点
    print("请使用 distill 命令重新蒸馏以重建索引")


def main():
    parser = argparse.ArgumentParser(
        description="MealMuse 知识蒸馏脚本 — 将书籍蒸馏为营养健康知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s full /path/to/book.pdf --name 书名        # 完整流程
  %(prog)s distill /path/to/book.md                   # 只做蒸馏
  %(prog)s clean --name 书名                          # 清理旧数据
  %(prog)s list                                       # 查看已蒸馏书籍
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # distill 子命令
    p_distill = subparsers.add_parser("distill", help="Markdown → 知识点（蒸馏）")
    p_distill.add_argument("input", help="Markdown 或文本文件路径")
    p_distill.add_argument("--name", help="书名（默认从文件名推断）")
    p_distill.add_argument("--dry-run", action="store_true", help="试运行，不写入数据库")
    p_distill.add_argument("--concurrency", type=int, default=2, help="并发提取数（默认 2）")

    # full 子命令
    p_full = subparsers.add_parser("full", help="完整流程：PDF → Markdown → 蒸馏 → 入库")
    p_full.add_argument("input", help="PDF 文件路径")
    p_full.add_argument("--name", required=True, help="书名")
    p_full.add_argument("--dry-run", action="store_true", help="试运行，不写入数据库")
    p_full.add_argument("--concurrency", type=int, default=2, help="并发数（默认 2）")

    # clean 子命令
    p_clean = subparsers.add_parser("clean", help="清理某书的旧数据")
    p_clean.add_argument("--name", required=True, help="书名")

    # list 子命令
    p_list = subparsers.add_parser("list", help="查看已蒸馏书籍列表")

    # reindex 子命令
    p_reindex = subparsers.add_parser("reindex", help="重建向量索引")
    p_reindex.add_argument("--name", help="书名（不指定则重建所有）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "distill":
        cmd_distill(args)
    elif args.command == "full":
        cmd_full(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "reindex":
        cmd_reindex(args)


if __name__ == "__main__":
    main()
