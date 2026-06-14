#!/usr/bin/env python3
"""MealMuse 知识库种子数据填充脚本

直接从 LLM 生成基础营养健康知识点，写入 ChromaDB。

用法:
    python3 scripts/seed_knowledge.py        # 填充所有类别
    python3 scripts/seed_knowledge.py --list   # 查看当前知识库统计
    python3 scripts/seed_knowledge.py --clear # 清空知识库后重新填充
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.services.knowledge_service import add_knowledge, get_knowledge_stats, delete_knowledge_by_source

settings = get_settings()

PROJECT_ROOT = Path(__file__).parent.parent.parent
BOOKS_DIR = PROJECT_ROOT / "data" / "books"
BOOKS_DIR.mkdir(parents=True, exist_ok=True)


def call_llm(messages: list, temperature: float = 0.2, max_tokens: int = 4000) -> str:
    """调用通义千问 API（同步）"""
    import httpx

    api_key = settings.DASHSCOPE_API_KEY
    if not api_key:
        raise Exception("未配置 DASHSCOPE_API_KEY")

    api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

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


# 基础知识点类别
CATEGORIES = [
    {
        "category": "nutrition",
        "topic": "常见食物营养成分数据",
        "prompt": """请生成 20 条常见食物的营养成分知识点，每条包含：
- 食物名称
- 每 100g 的热量、蛋白质、脂肪、碳水化合物
- 关键营养素（如铁、钙、维生素等）
- 适合人群

请生成真实的营养数据，格式为 JSON 数组：
[
  {"title": "食物名", "content": "详细描述...", "keywords": ["关键词1", "关键词2"], "importance": 8, "source": "nutrition_data"},
  ...
]

食物包括：鸡胸肉、三文鱼、鸡蛋、牛奶、豆腐、燕麦、紫薯、菠菜、西兰花、胡萝卜、苹果、香蕉、橙子、杏仁、牛油果、蓝莓、藜麦、红薯、糙米、黑豆"""
    },
    {
        "category": "tcm_diet",
        "topic": "中医食疗与药膳配方",
        "prompt": """请生成 15 条中医食疗/药膳知识点，每条包含：
- 配方名称
- 配方组成（食材+用量）
- 制作方法（简要步骤）
- 功效说明
- 适合体质/症状
- 禁忌注意事项

请生成真实可用的食疗知识，格式为 JSON 数组：
[
  {"title": "配方名", "content": "详细描述...", "keywords": ["关键词1", "关键词2"], "importance": 9, "source": "tcm_diet"},
  ...
]

包括：红枣枸杞茶、四物汤、四君子汤、山药薏米粥、姜枣茶、桂圆红枣粥、百合银耳羹、黄芪当归汤、茯苓山药糊、玫瑰花茶、陈皮茯苓茶、莲子百合粥、赤小豆薏米汤、当归生姜羊肉汤、酸枣仁安神粥"""
    },
    {
        "category": "pregnancy",
        "topic": "备孕与孕期营养指南",
        "prompt": """请生成 15 条备孕/孕期营养知识点，每条包含：
- 标题
- 具体建议（需要包含数据，如"每日400μg叶酸"）
- 饮食原则
- 推荐食物
- 禁忌食物
- 注意事项

请生成循证医学建议，格式为 JSON 数组：
[
  {"title": "标题", "content": "详细描述...", "keywords": ["关键词1", "关键词2"], "importance": 10, "source": "pregnancy_guide"},
  ...
]

主题包括：叶酸补充、碘的需求、铁的需求、DHA补充、钙补充、备孕饮食禁忌、孕早期呕吐饮食调理、孕中期营养需求、孕晚期饮食注意、孕期体重管理、妊娠糖尿病饮食、孕期补血、孕期补钙、哺乳期营养、产后调理"""
    },
    {
        "category": "menstrual",
        "topic": "经期饮食调理指南",
        "prompt": """请生成 12 条经期饮食调理知识点，每条包含：
- 标题
- 适合阶段（月经期/卵泡期/排卵期/黄体期）
- 饮食原则
- 推荐食物（具体食物名称）
- 禁忌食物
- 食疗方案（可选）

请生成实用建议，格式为 JSON 数组：
[
  {"title": "标题", "content": "详细描述...", "keywords": ["关键词1", "关键词2"], "importance": 9, "source": "menstrual_guide"},
  ...
]

主题包括：月经期温补饮食、经期补铁、经期腹痛饮食调理、经期水肿、姨妈走后补血、排卵期饮食、黄体期PMS调理、经期禁忌、生姜红糖水、桂圆红枣茶、经期后四物汤、经期运动与饮食"""
    },
    {
        "category": "weight_loss",
        "topic": "减脂减重饮食指南",
        "prompt": """请生成 15 条减脂减重饮食知识点，每条包含：
- 标题
- 具体方法/原则
- 推荐食物
- 应避免食物
- 热量数据（如果有）
- 适用人群

请生成科学可执行的建议，格式为 JSON 数组：
[
  {"title": "标题", "content": "详细描述...", "keywords": ["关键词1", "关键词2"], "importance": 9, "source": "weight_loss_guide"},
  ...
]

主题包括：基础代谢率计算、热量缺口原则、高蛋白饮食、碳水循环、低GI饮食、轻断食、减脂期食物选择、蛋白质计算、优质脂肪、运动后饮食、代餐选择、减肥期欺骗餐、平台期突破、减脂期常见错误、产后减脂"""
    },
    {
        "category": "chronic",
        "topic": "慢性病饮食管理",
        "prompt": """请生成 12 条慢性病饮食管理知识点，每条包含：
- 病种
- 饮食原则
- 推荐食物
- 禁忌食物
- 具体数据（如"每日盐摄入<5g"）
- 注意事项

请生成临床可用的建议，格式为 JSON 数组：
[
  {"title": "标题", "content": "详细描述...", "keywords": ["关键词1", "关键词2"], "importance": 10, "source": "chronic_disease"},
  ...
]

病种包括：糖尿病饮食、高血压饮食、高血脂饮食、痛风饮食、胃溃疡饮食、慢性肾病饮食、甲状腺饮食、胆囊炎饮食、冠心病饮食、脂肪肝饮食"""
    },
    {
        "category": "recipe",
        "topic": "健康食谱与烹饪方法",
        "prompt": """请生成 10 条健康食谱，每条包含：
- 菜名
- 适合场景（早餐/午餐/晚餐/加餐）
- 主要食材（列出具体用量）
- 制作步骤（简要 3-5 步）
- 营养亮点（热量估算、主要营养素）
- 适合人群

请生成家常可做的食谱，格式为 JSON 数组：
[
  {"title": "菜名", "content": "详细描述...", "keywords": ["关键词1", "关键词2"], "importance": 8, "source": "healthy_recipe"},
  ...
]

菜谱包括：鸡胸肉沙拉、蒜蓉西兰花、三文鱼刺身、藜麦能量碗、紫薯代餐奶昔、山药排骨汤、豆腐蒸蛋、清蒸鲈鱼、蔬菜smoothie、燕麦隔夜杯"""
    },
]


def generate_knowledge(category_info: dict) -> list[dict]:
    """为一个类别生成知识点（同步，调用 LLM）"""
    category = category_info["category"]
    topic = category_info["topic"]
    prompt = category_info["prompt"]

    print(f"  生成 {category} ({topic}) 知识点...")

    try:
        response = call_llm(
            messages=[
                {"role": "system", "content": "你是营养健康知识专家，只输出 JSON 数组，不要任何其他文字。"},
                {"role": "user", "content": prompt},
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
            print(f"  [{category}] 解析失败（非数组），跳过")
            return []

        # 质量过滤
        valid = []
        for item in result:
            if not isinstance(item, dict):
                continue
            if not item.get("title") or not item.get("content"):
                continue
            if len(item["content"]) < 80:
                continue
            item["category"] = category
            item["source"] = item.get("source", "meal_muse_seed")
            valid.append(item)

        print(f"  [{category}] 生成 {len(valid)} 条有效知识点")
        return valid

    except json.JSONDecodeError as e:
        print(f"  [{category}] JSON 解析失败: {e}")
        # 保存原始响应便于调试
        debug_path = BOOKS_DIR / f"debug_{category}_raw.txt"
        debug_path.write_text(response[:2000], encoding="utf-8")
        print(f"  原始响应已保存到: {debug_path}")
        return []
    except Exception as e:
        print(f"  [{category}] 生成失败: {e}")
        return []


async def save_knowledge(knowledge_list: list[dict]) -> int:
    """保存知识点到知识库（异步）"""
    saved = 0
    failed = 0
    for i, k in enumerate(knowledge_list, 1):
        try:
            await add_knowledge(
                title=k["title"],
                content=k["content"],
                source=k["source"],
                category=k.get("category", "general"),
                metadata={
                    "keywords": json.dumps(k.get("keywords", []), ensure_ascii=False),
                    "importance": str(k.get("importance", 5)),
                },
            )
            saved += 1
            if saved % 10 == 0:
                print(f"    已保存 {saved}/{len(knowledge_list)} 条...")
        except Exception as e:
            failed += 1
            if failed <= 3:
                print(f"    保存失败: {k['title'][:30]} - {e}")
            elif failed == 4:
                print(f"    ... 还有更多失败项，已省略")

    if failed > 0:
        print(f"    保存失败: {failed} 条")
    return saved


async def clear_knowledge():
    """清空知识库"""
    print("清空知识库...")
    sources = [
        "nutrition_data", "tcm_diet", "pregnancy_guide", "menstrual_guide",
        "weight_loss_guide", "chronic_disease", "healthy_recipe", "meal_muse_seed",
    ]
    total_deleted = 0
    for source in sources:
        deleted = await delete_knowledge_by_source(source)
        print(f"  已删除 {source}: {deleted} 条")
        total_deleted += deleted
    print(f"共删除 {total_deleted} 条")


async def run(args):
    """主逻辑（异步）"""
    if args.list:
        stats = await get_knowledge_stats()
        print("知识库统计:")
        print(f"  总计: {stats['total']} 条")
        for cat, count in stats.get("categories", {}).items():
            print(f"  - {cat}: {count} 条")
        for source, count in stats.get("sources", {}).items():
            print(f"  来源 {source}: {count} 条")
        return

    if args.clear:
        await clear_knowledge()

    print("=" * 60)
    print("MealMuse 知识库填充")
    print("=" * 60)

    # 阶段 1: 生成知识点（LLM 调用是同步的，逐类生成）
    print("\n[阶段 1] 生成知识点...")
    all_knowledge = []
    for cat_info in CATEGORIES:
        knowledge = generate_knowledge(cat_info)
        all_knowledge.extend(knowledge)

    print(f"\n共生成 {len(all_knowledge)} 条知识点")

    if not all_knowledge:
        print("没有生成任何知识点，退出")
        return

    # 阶段 2: 保存到知识库（异步写入 ChromaDB）
    print("\n[阶段 2] 保存到知识库...")
    saved = await save_knowledge(all_knowledge)
    print(f"成功保存 {saved}/{len(all_knowledge)} 条")

    # 最终统计
    print("\n[完成] 知识库统计:")
    stats = await get_knowledge_stats()
    print(f"  总计: {stats['total']} 条")
    for cat, count in stats.get("categories", {}).items():
        print(f"  - {cat}: {count} 条")


def main():
    parser = argparse.ArgumentParser(description="MealMuse 知识库种子数据填充")
    parser.add_argument("--clear", action="store_true", help="清空知识库后重新填充")
    parser.add_argument("--list", action="store_true", help="查看知识库统计")
    args = parser.parse_args()

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
