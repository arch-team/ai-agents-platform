"""Builder 模块 DTO。"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.modules.builder.domain.entities.builder_session import BuilderSession


@dataclass
class TriggerBuilderDTO:
    """创建 Builder 会话请求数据。"""

    prompt: str
    template_id: int | None = None
    selected_skill_ids: list[int] = field(default_factory=list)


@dataclass
class RefineBuilderDTO:
    """多轮迭代请求数据。"""

    message: str


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
    # V2 字段
    messages: list[dict[str, str]] = field(default_factory=list)
    template_id: int | None = None
    selected_skill_ids: list[int] = field(default_factory=list)
    generated_blueprint: dict[str, Any] | None = None

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
            messages=entity.messages,
            template_id=entity.template_id,
            selected_skill_ids=entity.selected_skill_ids,
            generated_blueprint=entity.generated_blueprint,
        )
