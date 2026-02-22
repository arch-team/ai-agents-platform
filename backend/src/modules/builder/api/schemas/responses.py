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
