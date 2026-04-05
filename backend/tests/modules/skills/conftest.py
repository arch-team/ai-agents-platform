"""Skills 模块测试 fixtures。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.modules.skills.application.interfaces.skill_file_manager import ISkillFileManager
from src.modules.skills.application.services.skill_service import SkillService
from src.modules.skills.domain.entities.skill import Skill
from src.modules.skills.domain.repositories.skill_repository import ISkillRepository
from src.modules.skills.domain.value_objects.skill_category import SkillCategory
from src.modules.skills.domain.value_objects.skill_status import SkillStatus


def make_skill(
    *,
    skill_id: int = 1,
    name: str = "退货处理",
    description: str = "处理客户退货咨询",
    category: SkillCategory = SkillCategory.CUSTOMER_SERVICE,
    trigger_description: str = "客户提到退货、退款时使用",
    status: SkillStatus = SkillStatus.DRAFT,
    creator_id: int = 1,
    version: int = 1,
    usage_count: int = 0,
    file_path: str = "drafts/return-processing",
) -> Skill:
    """Skill 工厂函数。"""
    now = datetime.now(tz=UTC)
    skill = Skill(
        name=name,
        description=description,
        category=category,
        trigger_description=trigger_description,
        status=status,
        creator_id=creator_id,
        version=version,
        usage_count=usage_count,
        file_path=file_path,
    )
    object.__setattr__(skill, "id", skill_id)
    object.__setattr__(skill, "created_at", now)
    object.__setattr__(skill, "updated_at", now)
    return skill


@pytest.fixture
def mock_skill_repo() -> AsyncMock:
    """Mock ISkillRepository。"""
    return AsyncMock(spec=ISkillRepository)


@pytest.fixture
def mock_file_manager() -> AsyncMock:
    """Mock ISkillFileManager。"""
    return AsyncMock(spec=ISkillFileManager)


@pytest.fixture
def skill_service(mock_skill_repo: AsyncMock, mock_file_manager: AsyncMock) -> SkillService:
    """创建注入 mock 依赖的 SkillService。"""
    return SkillService(repository=mock_skill_repo, file_manager=mock_file_manager)


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    """Mock event_bus，避免事件副作用。"""
    with patch("src.modules.skills.application.services.skill_service.event_bus") as mock:
        mock.publish_async = AsyncMock()
        yield mock
