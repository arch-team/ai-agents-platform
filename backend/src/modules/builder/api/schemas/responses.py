"""Builder API 响应模型。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BuilderSessionResponse(BaseModel):
    """Builder 会话响应。"""

    id: int
    user_id: int
    prompt: str
    status: str
    generated_config: dict[str, Any] | None = None
    agent_name: str | None = None
    created_agent_id: int | None = None
    created_at: datetime
    updated_at: datetime
    # V2 字段
    messages: list[dict[str, str]] = []
    template_id: int | None = None
    selected_skill_ids: list[int] = []
    generated_blueprint: dict[str, Any] | None = None


class AvailableToolResponse(BaseModel):
    """平台可用工具响应。"""

    id: int
    name: str
    description: str
    tool_type: str


class AvailableSkillResponse(BaseModel):
    """平台可用 Skill 响应。"""

    id: int
    name: str
    description: str
    category: str
