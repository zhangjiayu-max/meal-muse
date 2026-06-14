"""Prompt 管理 API — 查看和管理所有 Agent 的 Prompt"""

from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/prompts", tags=["Prompt 管理"])


@router.get("/list")
async def list_prompts(
    current_user: User = Depends(get_current_user),
):
    """列出所有注册的 Prompt 模板"""
    from app.agents.base import PromptRegistry

    prompts = PromptRegistry.list_all()
    return {
        "prompts": [
            {
                "name": name,
                "description": template.description,
                "version": template.version,
                "tags": template.tags,
                "system_preview": template.system[:200] + "..." if len(template.system) > 200 else template.system,
                "user_template_preview": template.user_template[:200] + "..." if len(template.user_template) > 200 else template.user_template,
            }
            for name, template in prompts.items()
        ]
    }


@router.get("/{prompt_name}")
async def get_prompt(
    prompt_name: str,
    current_user: User = Depends(get_current_user),
):
    """获取指定 Prompt 的完整内容"""
    from app.agents.base import PromptRegistry

    template = PromptRegistry.get(prompt_name)
    if not template:
        return {"error": f"Prompt '{prompt_name}' not found"}

    return {
        "name": prompt_name,
        "description": template.description,
        "version": template.version,
        "tags": template.tags,
        "system": template.system,
        "user_template": template.user_template,
    }
