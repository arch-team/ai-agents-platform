"""Template API 请求模型。"""

from pydantic import BaseModel, Field

from src.shared.domain.constants import TEMPLATE_DEFAULT_MAX_TOKENS, TEMPLATE_DEFAULT_TEMPERATURE


class CreateTemplateRequest(BaseModel):
    """创建模板请求。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    category: str = "general"
    system_prompt: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    temperature: float = Field(default=TEMPLATE_DEFAULT_TEMPERATURE, ge=0.0, le=1.0)
    max_tokens: int = Field(default=TEMPLATE_DEFAULT_MAX_TOKENS, ge=1)
    tool_ids: list[int] = Field(default_factory=list)
    knowledge_base_ids: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class UpdateTemplateRequest(BaseModel):
    """更新模板请求。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    category: str | None = None
    system_prompt: str | None = Field(default=None, min_length=1)
    model_id: str | None = Field(default=None, min_length=1)
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(default=None, ge=1)
    tool_ids: list[int] | None = None
    knowledge_base_ids: list[int] | None = None
    tags: list[str] | None = None


class InstantiateTemplateRequest(BaseModel):
    """模板实例化请求。"""

    agent_name: str = Field(min_length=1, max_length=100)
