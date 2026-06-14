"""后台管理 API — 用户管理、知识库统计"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.diet_record import DietRecord
from app.models.meal_plan import MealPlan
from app.models.menstrual_cycle import MenstrualCycle
from app.models.ai_chat_message import AiChatMessage

router = APIRouter(prefix="/admin", tags=["后台管理"])


def check_admin(user: User):
    """检查是否为管理员（简化版：手机号 13800000000 为管理员）"""
    if user.phone != "13800000000":
        raise HTTPException(status_code=403, detail="权限不足")
    return True


# ===== 用户管理 =====

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表"""
    check_admin(current_user)

    # 总数
    count_result = await db.execute(
        select(func.count(User.id)).where(User.deleted_at.is_(None))
    )
    total = count_result.scalar()

    # 分页查询
    offset = (page - 1) * page_size
    result = await db.execute(
        select(User)
        .where(User.deleted_at.is_(None))
        .order_by(desc(User.created_at))
        .offset(offset)
        .limit(page_size)
    )
    users = result.scalars().all()

    # 获取每个用户的统计信息
    user_list = []
    for user in users:
        # 饮食记录数
        diet_count_result = await db.execute(
            select(func.count(DietRecord.id))
            .where(DietRecord.user_id == user.id, DietRecord.deleted_at.is_(None))
        )
        diet_count = diet_count_result.scalar()

        # 最后登录时间
        user_list.append({
            "id": str(user.id),
            "phone": user.phone,
            "nickname": user.nickname,
            "height_cm": float(user.height_cm) if user.height_cm else None,
            "current_weight": float(user.current_weight) if user.current_weight else None,
            "target_weight": float(user.target_weight) if user.target_weight else None,
            "activity_level": user.activity_level,
            "daily_calorie_target": user.daily_calorie_target,
            "status": user.status,
            "diet_record_count": diet_count,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat(),
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "users": user_list,
    }


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户详情"""
    check_admin(current_user)

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取饮食记录统计
    diet_stats = await db.execute(
        select(
            func.count(DietRecord.id).label("count"),
            func.sum(DietRecord.total_calories).label("total_calories"),
            func.avg(DietRecord.total_calories).label("avg_calories"),
        )
        .where(DietRecord.user_id == user.id, DietRecord.deleted_at.is_(None))
    )
    stats = diet_stats.one()

    # 获取最近 7 天的饮食记录
    from datetime import date, timedelta
    week_ago = date.today() - timedelta(days=7)
    recent_records = await db.execute(
        select(DietRecord)
        .where(
            DietRecord.user_id == user.id,
            DietRecord.record_date >= week_ago,
            DietRecord.deleted_at.is_(None),
        )
        .order_by(desc(DietRecord.recorded_at))
        .limit(10)
    )
    records = recent_records.scalars().all()

    return {
        "user": {
            "id": str(user.id),
            "phone": user.phone,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "gender": user.gender,
            "birthday": user.birthday.isoformat() if user.birthday else None,
            "height_cm": float(user.height_cm) if user.height_cm else None,
            "current_weight": float(user.current_weight) if user.current_weight else None,
            "target_weight": float(user.target_weight) if user.target_weight else None,
            "activity_level": user.activity_level,
            "preferences": user.preferences,
            "daily_calorie_target": user.daily_calorie_target,
            "status": user.status,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat(),
        },
        "diet_stats": {
            "total_records": stats.count or 0,
            "total_calories": float(stats.total_calories or 0),
            "avg_calories_per_day": float(stats.avg_calories or 0),
        },
        "recent_records": [
            {
                "id": str(r.id),
                "meal_type": r.meal_type,
                "food_text": r.food_text,
                "total_calories": r.total_calories,
                "record_date": r.record_date.isoformat(),
            }
            for r in records
        ],
    }


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: uuid.UUID,
    status: str = Query(..., regex="^(active|disabled|banned)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户状态"""
    check_admin(current_user)

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.status = status
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": f"用户状态已更新为 {status}"}


# ===== 系统统计 =====

@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取系统统计数据"""
    check_admin(current_user)

    from datetime import date, timedelta

    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # 用户统计
    total_users = await db.execute(
        select(func.count(User.id)).where(User.deleted_at.is_(None))
    )
    new_users_week = await db.execute(
        select(func.count(User.id)).where(
            User.created_at >= datetime(week_ago.year, week_ago.month, week_ago.day, tzinfo=timezone.utc),
            User.deleted_at.is_(None),
        )
    )
    active_users_week = await db.execute(
        select(func.count(User.id)).where(
            User.last_login_at >= datetime(week_ago.year, week_ago.month, week_ago.day, tzinfo=timezone.utc),
            User.deleted_at.is_(None),
        )
    )

    # 饮食记录统计
    total_records = await db.execute(
        select(func.count(DietRecord.id)).where(DietRecord.deleted_at.is_(None))
    )
    records_today = await db.execute(
        select(func.count(DietRecord.id)).where(
            DietRecord.record_date == today,
            DietRecord.deleted_at.is_(None),
        )
    )
    records_week = await db.execute(
        select(func.count(DietRecord.id)).where(
            DietRecord.record_date >= week_ago,
            DietRecord.deleted_at.is_(None),
        )
    )

    # AI 对话统计
    total_chats = await db.execute(select(func.count(AiChatMessage.id)))
    chats_today = await db.execute(
        select(func.count(AiChatMessage.id)).where(
            AiChatMessage.created_at >= datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        )
    )

    # 餐食计划统计
    total_plans = await db.execute(select(func.count(MealPlan.id)))
    plans_today = await db.execute(
        select(func.count(MealPlan.id)).where(MealPlan.plan_date == today)
    )

    return {
        "users": {
            "total": total_users.scalar() or 0,
            "new_this_week": new_users_week.scalar() or 0,
            "active_this_week": active_users_week.scalar() or 0,
        },
        "diet_records": {
            "total": total_records.scalar() or 0,
            "today": records_today.scalar() or 0,
            "this_week": records_week.scalar() or 0,
        },
        "ai_chats": {
            "total": total_chats.scalar() or 0,
            "today": chats_today.scalar() or 0,
        },
        "meal_plans": {
            "total": total_plans.scalar() or 0,
            "today": plans_today.scalar() or 0,
        },
    }


# ===== 知识库管理 =====

@router.get("/knowledge/stats")
async def get_knowledge_stats(
    current_user: User = Depends(get_current_user),
):
    """获取知识库统计数据"""
    check_admin(current_user)

    # 尝试从 ChromaDB 获取统计
    try:
        import chromadb
        from pathlib import Path

        chroma_dir = Path(__file__).parent.parent.parent.parent / "data" / "chromadb"
        if chroma_dir.exists():
            client = chromadb.PersistentClient(path=str(chroma_dir))
            collections = client.list_collections()

            stats = {
                "collections": [],
                "total_documents": 0,
            }

            for col in collections:
                collection = client.get_collection(col.name)
                count = collection.count()
                stats["collections"].append({
                    "name": col.name,
                    "count": count,
                })
                stats["total_documents"] += count

            return stats
        else:
            return {
                "collections": [],
                "total_documents": 0,
                "message": "知识库尚未初始化",
            }
    except Exception as e:
        return {
            "collections": [],
            "total_documents": 0,
            "error": str(e),
        }


@router.get("/knowledge/list")
async def list_knowledge(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str = Query(None),
    current_user: User = Depends(get_current_user),
):
    """获取知识库内容列表"""
    check_admin(current_user)

    try:
        import chromadb
        from pathlib import Path

        chroma_dir = Path(__file__).parent.parent.parent.parent / "data" / "chromadb"
        if not chroma_dir.exists():
            return {"total": 0, "items": [], "message": "知识库尚未初始化"}

        client = chromadb.PersistentClient(path=str(chroma_dir))
        collection = client.get_or_create_collection("meal_muse_knowledge")

        # 获取所有文档
        results = collection.get(
            include=["documents", "metadatas"],
            limit=page_size,
            offset=(page - 1) * page_size,
        )

        items = []
        for i, doc_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i] if results["metadatas"] else {}
            document = results["documents"][i] if results["documents"] else ""

            # 如果指定了类别，过滤
            if category and metadata.get("category") != category:
                continue

            items.append({
                "id": doc_id,
                "content": document[:200] + "..." if len(document) > 200 else document,
                "metadata": metadata,
            })

        return {
            "total": collection.count(),
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    except Exception as e:
        return {"total": 0, "items": [], "error": str(e)}


@router.get("/knowledge/categories")
async def get_knowledge_categories(
    current_user: User = Depends(get_current_user),
):
    """获取知识库分类统计"""
    check_admin(current_user)

    try:
        import chromadb
        from pathlib import Path
        from collections import Counter

        chroma_dir = Path(__file__).parent.parent.parent.parent / "data" / "chromadb"
        if not chroma_dir.exists():
            return {"categories": []}

        client = chromadb.PersistentClient(path=str(chroma_dir))
        collection = client.get_or_create_collection("meal_muse_knowledge")

        # 获取所有 metadata
        results = collection.get(include=["metadatas"])

        # 统计分类
        category_counter = Counter()
        source_counter = Counter()

        for metadata in results["metadatas"]:
            if metadata:
                cat = metadata.get("category", "未分类")
                category_counter[cat] += 1

                source = metadata.get("source", "未知来源")
                source_counter[source] += 1

        return {
            "categories": [
                {"name": k, "count": v}
                for k, v in category_counter.most_common()
            ],
            "sources": [
                {"name": k, "count": v}
                for k, v in source_counter.most_common()
            ],
        }
    except Exception as e:
        return {"categories": [], "sources": [], "error": str(e)}
