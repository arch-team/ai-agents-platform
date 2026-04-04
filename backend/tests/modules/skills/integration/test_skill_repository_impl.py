"""SkillRepositoryImpl 集成测试 — SQLite 内存数据库。"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.persistence.models.user_model import UserModel
from src.modules.skills.domain.entities.skill import Skill
from src.modules.skills.domain.value_objects.skill_category import SkillCategory
from src.modules.skills.domain.value_objects.skill_status import SkillStatus
from src.modules.skills.infrastructure.persistence.repositories.skill_repository_impl import SkillRepositoryImpl


@pytest.fixture
def session(sqlite_session: AsyncSession) -> AsyncSession:
    return sqlite_session


@pytest_asyncio.fixture
async def repo(session: AsyncSession) -> SkillRepositoryImpl:
    return SkillRepositoryImpl(session=session)


def _make_skill(
    *,
    name: str = "退货处理",
    description: str = "处理退货咨询",
    category: SkillCategory = SkillCategory.CUSTOMER_SERVICE,
    creator_id: int = 1,
    trigger_description: str = "退货时使用",
    file_path: str = "drafts/return-processing",
) -> Skill:
    return Skill(
        name=name,
        description=description,
        category=category,
        trigger_description=trigger_description,
        creator_id=creator_id,
        file_path=file_path,
    )


async def _seed_user(session: AsyncSession, user_id: int = 1) -> None:
    """创建测试用户 (skills 外键依赖)。"""

    user = UserModel(
        id=user_id, email=f"user{user_id}@test.com", name="测试用户", hashed_password="x", role="developer",
    )
    session.add(user)
    await session.flush()


@pytest.mark.integration
class TestSkillRepositoryCRUD:
    """基本 CRUD 操作。"""

    @pytest.mark.asyncio
    async def test_create_and_get(self, repo: SkillRepositoryImpl, session: AsyncSession) -> None:
        await _seed_user(session)
        skill = _make_skill()
        created = await repo.create(skill)
        await session.commit()

        assert created.id is not None
        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.name == "退货处理"
        assert fetched.status == SkillStatus.DRAFT
        assert fetched.category == SkillCategory.CUSTOMER_SERVICE

    @pytest.mark.asyncio
    async def test_update(self, repo: SkillRepositoryImpl, session: AsyncSession) -> None:
        await _seed_user(session)
        skill = _make_skill()
        created = await repo.create(skill)
        await session.commit()

        created.description = "更新后的描述"
        created.touch()
        updated = await repo.update(created)
        await session.commit()

        assert updated.description == "更新后的描述"

    @pytest.mark.asyncio
    async def test_delete(self, repo: SkillRepositoryImpl, session: AsyncSession) -> None:
        await _seed_user(session)
        skill = _make_skill()
        created = await repo.create(skill)
        await session.commit()
        assert created.id is not None

        await repo.delete(created.id)
        await session.commit()

        result = await repo.get_by_id(created.id)
        assert result is None


@pytest.mark.integration
class TestSkillRepositoryQueries:
    """查询方法。"""

    @pytest.mark.asyncio
    async def test_get_by_name(self, repo: SkillRepositoryImpl, session: AsyncSession) -> None:
        await _seed_user(session)
        await repo.create(_make_skill(name="order-inquiry"))
        await session.commit()

        result = await repo.get_by_name("order-inquiry")
        assert result is not None
        assert result.name == "order-inquiry"

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, repo: SkillRepositoryImpl) -> None:
        result = await repo.get_by_name("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_by_creator(self, repo: SkillRepositoryImpl, session: AsyncSession) -> None:
        await _seed_user(session, user_id=1)
        await _seed_user(session, user_id=2)
        await repo.create(_make_skill(name="skill-a", creator_id=1))
        await repo.create(_make_skill(name="skill-b", creator_id=1))
        await repo.create(_make_skill(name="skill-c", creator_id=2))
        await session.commit()

        results = await repo.list_by_creator(1)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_published(self, repo: SkillRepositoryImpl, session: AsyncSession) -> None:
        await _seed_user(session)
        # 创建 DRAFT 和 PUBLISHED 各一个
        draft = _make_skill(name="draft-skill")
        await repo.create(draft)

        published = _make_skill(name="published-skill")
        published.publish()
        await repo.create(published)
        await session.commit()

        results = await repo.list_published()
        assert len(results) == 1
        assert results[0].name == "published-skill"

    @pytest.mark.asyncio
    async def test_count_by_creator(self, repo: SkillRepositoryImpl, session: AsyncSession) -> None:
        await _seed_user(session)
        await repo.create(_make_skill(name="skill-1"))
        await repo.create(_make_skill(name="skill-2"))
        await session.commit()

        count = await repo.count_by_creator(1)
        assert count == 2

    @pytest.mark.asyncio
    async def test_list_by_category(self, repo: SkillRepositoryImpl, session: AsyncSession) -> None:
        await _seed_user(session)
        cs_skill = _make_skill(name="cs-skill", category=SkillCategory.CUSTOMER_SERVICE)
        cs_skill.publish()
        await repo.create(cs_skill)

        da_skill = _make_skill(name="da-skill", category=SkillCategory.DATA_ANALYSIS)
        da_skill.publish()
        await repo.create(da_skill)
        await session.commit()

        results = await repo.list_by_category(SkillCategory.CUSTOMER_SERVICE)
        assert len(results) == 1
        assert results[0].category == SkillCategory.CUSTOMER_SERVICE

    @pytest.mark.asyncio
    async def test_search(self, repo: SkillRepositoryImpl, session: AsyncSession) -> None:
        await _seed_user(session)
        skill = _make_skill(name="退货处理", description="处理客户退货")
        skill.publish()
        await repo.create(skill)
        await session.commit()

        results = await repo.search("退货")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_increment_usage_count(self, repo: SkillRepositoryImpl, session: AsyncSession) -> None:
        await _seed_user(session)
        created = await repo.create(_make_skill())
        await session.commit()
        assert created.id is not None

        await repo.increment_usage_count(created.id)
        await session.commit()

        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.usage_count == 1
