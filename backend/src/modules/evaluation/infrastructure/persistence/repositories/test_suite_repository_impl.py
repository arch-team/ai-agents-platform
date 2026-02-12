"""TestSuite 仓库实现。"""

from src.modules.evaluation.domain.entities.test_suite import TestSuite
from src.modules.evaluation.domain.repositories.test_suite_repository import ITestSuiteRepository
from src.modules.evaluation.domain.value_objects.test_suite_status import TestSuiteStatus
from src.modules.evaluation.infrastructure.persistence.models.test_suite_model import TestSuiteModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class TestSuiteRepositoryImpl(
    PydanticRepository[TestSuite, TestSuiteModel, int],
    ITestSuiteRepository,
):
    """TestSuite 仓库的 SQLAlchemy 实现。"""

    entity_class = TestSuite
    model_class = TestSuiteModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "name",
            "description",
            "status",
            "updated_at",
        },
    )

    def _to_entity(self, model: TestSuiteModel) -> TestSuite:
        """ORM Model -> Entity 转换。"""
        return TestSuite(
            id=model.id,
            name=model.name,
            description=model.description,
            agent_id=model.agent_id,
            status=TestSuiteStatus(model.status),
            owner_id=model.owner_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _get_update_data(self, entity: TestSuite) -> dict[str, object]:
        """提取可更新字段数据。"""
        data: dict[str, object] = {
            "name": entity.name,
            "description": entity.description,
            "status": entity.status.value,
            "updated_at": entity.updated_at,
        }
        return {k: v for k, v in data.items() if k in self._updatable_fields}

    async def list_by_agent(
        self,
        agent_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TestSuite]:
        """按 Agent ID 查询测试集列表。"""
        return await self._list_where(
            TestSuiteModel.agent_id == agent_id,
            offset=offset,
            limit=limit,
        )

    async def count_by_agent(self, agent_id: int) -> int:
        """按 Agent ID 统计测试集数量。"""
        return await self._count_where(TestSuiteModel.agent_id == agent_id)

    async def list_by_owner(
        self,
        owner_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TestSuite]:
        """按 owner_id 查询测试集列表。"""
        return await self._list_where(
            TestSuiteModel.owner_id == owner_id,
            offset=offset,
            limit=limit,
        )

    async def count_by_owner(self, owner_id: int) -> int:
        """按 owner_id 统计测试集数量。"""
        return await self._count_where(TestSuiteModel.owner_id == owner_id)
