"""Skills API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class SkillResponse(BaseModel):
    """Skill 详情响应。"""

    id: int
    name: str
    description: str
    category: str
    trigger_description: str
    status: str
    creator_id: int
    version: int
    usage_count: int
    file_path: str
    created_at: datetime
    updated_at: datetime


class SkillDetailResponse(SkillResponse):
    """Skill 详情 + SKILL.md 内容。"""

    skill_md_content: str = ""


class SkillListResponse(BaseModel):
    """Skill 列表响应。"""

    items: list[SkillResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
