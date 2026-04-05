"""BuilderSession 仓储实现。"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.builder.domain.entities.builder_session import BuilderSession
from src.modules.builder.domain.repositories.builder_session_repository import IBuilderSessionRepository
from src.modules.builder.domain.value_objects.builder_status import BuilderStatus
from src.modules.builder.infrastructure.persistence.models.builder_session_model import BuilderSessionModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class BuilderSessionRepositoryImpl(
    PydanticRepository[BuilderSession, BuilderSessionModel, int],
    IBuilderSessionRepository,
):
    """BuilderSession 仓储的 SQLAlchemy 实现。"""

    entity_class = BuilderSession
    model_class = BuilderSessionModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "status",
            "generated_config",
            "agent_name",
            "created_agent_id",
            "messages",
            "template_id",
            "selected_skill_ids",
            "generated_blueprint",
            "updated_at",
        },
    )

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    def _to_model(self, entity: BuilderSession) -> BuilderSessionModel:
        return BuilderSessionModel(
            id=entity.id,
            user_id=entity.user_id,
            prompt=entity.prompt,
            status=entity.status.value,
            generated_config=entity.generated_config,
            agent_name=entity.agent_name,
            created_agent_id=entity.created_agent_id,
            messages=entity.messages or None,
            template_id=entity.template_id,
            selected_skill_ids=entity.selected_skill_ids or None,
            generated_blueprint=entity.generated_blueprint,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, model: BuilderSessionModel) -> BuilderSession:
        return BuilderSession(
            id=model.id,
            user_id=model.user_id,
            prompt=model.prompt,
            status=BuilderStatus(model.status),
            generated_config=model.generated_config,
            agent_name=model.agent_name,
            created_agent_id=model.created_agent_id,
            messages=model.messages or [],
            template_id=model.template_id,
            selected_skill_ids=model.selected_skill_ids or [],
            generated_blueprint=model.generated_blueprint,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_by_user(self, user_id: int, *, offset: int = 0, limit: int = 20) -> list[BuilderSession]:
        return await self._list_where(
            BuilderSessionModel.user_id == user_id,
            offset=offset,
            limit=limit,
        )
