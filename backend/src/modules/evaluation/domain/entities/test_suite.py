"""测试集领域实体。"""

from pydantic import Field

from src.modules.evaluation.domain.value_objects.test_suite_status import TestSuiteStatus
from src.shared.domain.base_entity import PydanticEntity


class TestSuite(PydanticEntity):
    """测试集实体，管理一组测试用例。"""

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    agent_id: int
    status: TestSuiteStatus = TestSuiteStatus.DRAFT
    owner_id: int

    def activate(self) -> None:
        """激活测试集。DRAFT -> ACTIVE。

        注意: 需至少关联 1 个 TestCase，由 Service 层校验。
        """
        self._require_status(self.status, TestSuiteStatus.DRAFT, TestSuiteStatus.ACTIVE.value)
        self.status = TestSuiteStatus.ACTIVE
        self.touch()

    def archive(self) -> None:
        """归档测试集。DRAFT/ACTIVE -> ARCHIVED。"""
        self._require_status(
            self.status,
            frozenset({TestSuiteStatus.DRAFT, TestSuiteStatus.ACTIVE}),
            TestSuiteStatus.ARCHIVED.value,
        )
        self.status = TestSuiteStatus.ARCHIVED
        self.touch()

    def can_delete(self) -> bool:
        """仅 DRAFT 状态可物理删除。"""
        return self.status == TestSuiteStatus.DRAFT
