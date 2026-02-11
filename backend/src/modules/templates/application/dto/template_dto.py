"""Template 相关 DTO。"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CreateTemplateDTO:
    """创建模板请求数据。"""

    name: str
    description: str
    category: str
    system_prompt: str
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 4096
    tool_ids: list[int] = field(default_factory=list)
    knowledge_base_ids: list[int] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class UpdateTemplateDTO:
    """更新模板请求数据。"""

    name: str | None = None
    description: str | None = None
    category: str | None = None
    system_prompt: str | None = None
    model_id: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    tool_ids: list[int] | None = None
    knowledge_base_ids: list[int] | None = None
    tags: list[str] | None = None


@dataclass
class TemplateDTO:
    """模板响应数据。"""

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


@dataclass
class PagedTemplateDTO:
    """模板分页响应数据。"""

    items: list[TemplateDTO]
    total: int
    page: int
    page_size: int


@dataclass
class InstantiateTemplateDTO:
    """模板实例化请求数据 — 根据模板创建 Agent。"""

    template_id: int
    agent_name: str
