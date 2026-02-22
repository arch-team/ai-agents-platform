"""Builder 模块 DTO。"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.modules.builder.domain.entities.builder_session import BuilderSession


@dataclass
class TriggerBuilderDTO:
    """创建 Builder 会话请求数据。"""

    prompt: str


@dataclass
class BuilderSessionDTO:
    """Builder 会话响应数据。"""

    id: int
    user_id: int
    prompt: str
    status: str
    generated_config: dict[str, Any] | None
    agent_name: str | None
    created_agent_id: int | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: BuilderSession) -> "BuilderSessionDTO":
        """从领域实体创建 DTO。"""
        id_, created_at, updated_at = entity.require_persisted()
        return cls(
            id=id_,
            user_id=entity.user_id,
            prompt=entity.prompt,
            status=entity.status.value,
            generated_config=entity.generated_config,
            agent_name=entity.agent_name,
            created_agent_id=entity.created_agent_id,
            created_at=created_at,
            updated_at=updated_at,
        )
