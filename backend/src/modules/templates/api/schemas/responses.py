"""Template API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class TemplateResponse(BaseModel):
    """模板响应。"""

    id: int
    name: str
    description: str
    category: str
    status: str
    creator_id: int
    system_prompt: str
    model_id: str
    temperature: float
    max_tokens: int
    tool_ids: list[int]
    knowledge_base_ids: list[int]
    tags: list[str]
    usage_count: int
    is_featured: bool
    created_at: datetime
    updated_at: datetime


class TemplateListResponse(BaseModel):
    """模板列表响应。"""

    items: list[TemplateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
