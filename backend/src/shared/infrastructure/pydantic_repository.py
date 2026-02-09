"""PydanticRepository - IRepository 的通用 SQLAlchemy 实现。"""

from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.base_entity import PydanticEntity
from src.shared.domain.exceptions import EntityNotFoundError
from src.shared.domain.repositories import IRepository
from src.shared.infrastructure.database import Base


EntityT = TypeVar("EntityT", bound=PydanticEntity)
ModelT = TypeVar("ModelT", bound=Base)
IDT = TypeVar("IDT")


class PydanticRepository(IRepository[EntityT, IDT], Generic[EntityT, ModelT, IDT]):
    """IRepository 的通用 SQLAlchemy 实现，处理 Entity 与 ORM Model 转换。"""

    entity_class: type[EntityT]
    model_class: type[ModelT]
    _updatable_fields: frozenset[str] = frozenset()

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_model(self, entity: EntityT) -> ModelT:
        """Entity -> ORM Model 转换。"""
        data = entity.model_dump(exclude_none=False)
        column_keys = {c.key for c in self.model_class.__table__.columns}
        return self.model_class(**{k: v for k, v in data.items() if k in column_keys})

    def _to_entity(self, model: ModelT) -> EntityT:
        """ORM Model -> Entity 转换。"""
        data = {c.key: getattr(model, c.key) for c in model.__table__.columns}
        return self.entity_class.model_validate(data)

    def _get_update_data(self, entity: EntityT) -> dict[str, object]:
        """提取可更新字段数据。"""
        data = entity.model_dump()
        return {k: v for k, v in data.items() if k in self._updatable_fields}

    async def _get_model_or_raise(self, entity_id: object) -> ModelT:
        """根据 ID 获取 ORM Model，不存在则抛出 EntityNotFoundError。"""
        model = await self._find_model(entity_id)
        if model is None:
            raise EntityNotFoundError(
                entity_type=self.entity_class.__name__,
                entity_id=entity_id,  # type: ignore[arg-type]
            )
        return model

    async def _find_model(self, entity_id: object) -> ModelT | None:
        """根据 ID 查询 ORM Model，不存在返回 None。"""
        stmt = select(self.model_class).where(self.model_class.id == entity_id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, entity_id: IDT) -> EntityT | None:
        """根据 ID 获取实体。"""
        model = await self._find_model(entity_id)
        return self._to_entity(model) if model else None

    async def list(self, *, offset: int = 0, limit: int = 20) -> list[EntityT]:
        """分页获取实体列表。"""
        stmt = select(self.model_class).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self) -> int:
        """获取实体总数。"""
        stmt = select(func.count()).select_from(self.model_class)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def create(self, entity: EntityT) -> EntityT:
        """创建实体。"""
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: EntityT) -> EntityT:
        """更新实体。

        Raises:
            EntityNotFoundError: 实体不存在
        """
        model = await self._get_model_or_raise(entity.id)
        for field, value in self._get_update_data(entity).items():
            setattr(model, field, value)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, entity_id: IDT) -> None:
        """删除实体。

        Raises:
            EntityNotFoundError: 实体不存在
        """
        model = await self._get_model_or_raise(entity_id)
        await self._session.delete(model)
        await self._session.flush()
