"""Knowledge 模块 Repository 集成测试 (SQLite)。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# 导入 FK 引用的模型，确保 Base.metadata.create_all 能创建所有表
from src.modules.agents.infrastructure.persistence.models.agent_model import AgentModel  # noqa: F401
from src.modules.auth.infrastructure.persistence.models.user_model import UserModel  # noqa: F401
from src.modules.knowledge.domain.entities.document import Document
from src.modules.knowledge.domain.entities.knowledge_base import KnowledgeBase
from src.modules.knowledge.domain.value_objects.document_status import DocumentStatus
from src.modules.knowledge.domain.value_objects.knowledge_base_status import (
    KnowledgeBaseStatus,
)
from src.modules.knowledge.infrastructure.persistence.repositories.document_repository_impl import (
    DocumentRepositoryImpl,
)
from src.modules.knowledge.infrastructure.persistence.repositories.knowledge_base_repository_impl import (
    KnowledgeBaseRepositoryImpl,
)


# -- Fixture --


@pytest.fixture
def session(sqlite_session: AsyncSession) -> AsyncSession:
    return sqlite_session


@pytest.fixture
def kb_repo(session: AsyncSession) -> KnowledgeBaseRepositoryImpl:
    return KnowledgeBaseRepositoryImpl(session=session)


@pytest.fixture
def doc_repo(session: AsyncSession) -> DocumentRepositoryImpl:
    return DocumentRepositoryImpl(session=session)


# -- 工厂函数 --


def _make_kb(
    name: str = "测试知识库",
    owner_id: int = 1,
    description: str = "测试描述",
) -> KnowledgeBase:
    return KnowledgeBase(
        name=name,
        description=description,
        owner_id=owner_id,
    )


def _make_doc(
    knowledge_base_id: int = 1,
    filename: str = "test.pdf",
    file_size: int = 1024,
    content_type: str = "application/pdf",
) -> Document:
    return Document(
        knowledge_base_id=knowledge_base_id,
        filename=filename,
        file_size=file_size,
        content_type=content_type,
    )


# ── KnowledgeBaseRepositoryImpl 测试 ──


@pytest.mark.integration
class TestKnowledgeBaseRepositoryCreate:
    """知识库创建测试。"""

    @pytest.mark.asyncio
    async def test_create_knowledge_base(
        self,
        kb_repo: KnowledgeBaseRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """创建知识库，验证 id 非空、name/owner_id 正确。"""
        kb = _make_kb()
        created = await kb_repo.create(kb)
        await session.commit()

        assert created.id is not None
        assert created.name == "测试知识库"
        assert created.owner_id == 1
        assert created.description == "测试描述"
        assert created.status == KnowledgeBaseStatus.CREATING


@pytest.mark.integration
class TestKnowledgeBaseRepositoryGetById:
    """知识库按 ID 查询测试。"""

    @pytest.mark.asyncio
    async def test_get_by_id(
        self,
        kb_repo: KnowledgeBaseRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """创建后按 id 查询，验证返回正确实体。"""
        kb = _make_kb()
        created = await kb_repo.create(kb)
        await session.commit()

        found = await kb_repo.get_by_id(created.id)  # type: ignore[arg-type]
        assert found is not None
        assert found.id == created.id
        assert found.name == "测试知识库"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        kb_repo: KnowledgeBaseRepositoryImpl,
    ) -> None:
        """查询不存在的 id 返回 None。"""
        found = await kb_repo.get_by_id(9999)
        assert found is None


@pytest.mark.integration
class TestKnowledgeBaseRepositoryGetByNameAndOwner:
    """知识库按名称和 owner 查询测试。"""

    @pytest.mark.asyncio
    async def test_get_by_name_and_owner(
        self,
        kb_repo: KnowledgeBaseRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """按名称和 owner_id 查询，验证返回正确实体。"""
        kb = _make_kb(name="唯一名称", owner_id=42)
        await kb_repo.create(kb)
        await session.commit()

        found = await kb_repo.get_by_name_and_owner("唯一名称", owner_id=42)
        assert found is not None
        assert found.name == "唯一名称"
        assert found.owner_id == 42

    @pytest.mark.asyncio
    async def test_get_by_name_and_owner_not_found(
        self,
        kb_repo: KnowledgeBaseRepositoryImpl,
    ) -> None:
        """查询不存在的名称+owner 组合返回 None。"""
        found = await kb_repo.get_by_name_and_owner("不存在", owner_id=999)
        assert found is None


@pytest.mark.integration
class TestKnowledgeBaseRepositoryListByOwner:
    """知识库按 owner 列表查询测试。"""

    @pytest.mark.asyncio
    async def test_list_by_owner(
        self,
        kb_repo: KnowledgeBaseRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """创建 3 个 KB，按 owner 列表查询验证数量。"""
        owner_id = 10
        await kb_repo.create(_make_kb(name="KB-A", owner_id=owner_id))
        await kb_repo.create(_make_kb(name="KB-B", owner_id=owner_id))
        await kb_repo.create(_make_kb(name="KB-C", owner_id=owner_id))
        # 其他 owner 的 KB 不应被返回
        await kb_repo.create(_make_kb(name="KB-Other", owner_id=99))
        await session.commit()

        results = await kb_repo.list_by_owner(owner_id, offset=0, limit=20)
        assert len(results) == 3
        assert all(kb.owner_id == owner_id for kb in results)

    @pytest.mark.asyncio
    async def test_list_by_owner_with_pagination(
        self,
        kb_repo: KnowledgeBaseRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """offset/limit 分页验证。"""
        owner_id = 20
        await kb_repo.create(_make_kb(name="KB-1", owner_id=owner_id))
        await kb_repo.create(_make_kb(name="KB-2", owner_id=owner_id))
        await kb_repo.create(_make_kb(name="KB-3", owner_id=owner_id))
        await session.commit()

        page = await kb_repo.list_by_owner(owner_id, offset=0, limit=2)
        assert len(page) == 2


@pytest.mark.integration
class TestKnowledgeBaseRepositoryCountByOwner:
    """知识库按 owner 统计数量测试。"""

    @pytest.mark.asyncio
    async def test_count_by_owner(
        self,
        kb_repo: KnowledgeBaseRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """统计指定 owner 的知识库数量。"""
        owner_id = 30
        await kb_repo.create(_make_kb(name="KB-X", owner_id=owner_id))
        await kb_repo.create(_make_kb(name="KB-Y", owner_id=owner_id))
        # 其他 owner
        await kb_repo.create(_make_kb(name="KB-Z", owner_id=88))
        await session.commit()

        count = await kb_repo.count_by_owner(owner_id)
        assert count == 2


@pytest.mark.integration
class TestKnowledgeBaseRepositoryUpdate:
    """知识库更新测试。"""

    @pytest.mark.asyncio
    async def test_update_knowledge_base(
        self,
        kb_repo: KnowledgeBaseRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """修改 status，验证更新持久化。"""
        kb = _make_kb()
        created = await kb_repo.create(kb)
        await session.commit()

        # 通过实体方法将状态从 CREATING -> ACTIVE
        created.activate()
        updated = await kb_repo.update(created)
        await session.commit()

        assert updated.status == KnowledgeBaseStatus.ACTIVE
        assert updated.id == created.id

        # 重新查询验证持久化
        found = await kb_repo.get_by_id(created.id)  # type: ignore[arg-type]
        assert found is not None
        assert found.status == KnowledgeBaseStatus.ACTIVE


@pytest.mark.integration
class TestKnowledgeBaseRepositoryDelete:
    """知识库删除测试。"""

    @pytest.mark.asyncio
    async def test_delete_knowledge_base(
        self,
        kb_repo: KnowledgeBaseRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """删除后查询返回 None。"""
        kb = _make_kb()
        created = await kb_repo.create(kb)
        await session.commit()

        await kb_repo.delete(created.id)  # type: ignore[arg-type]
        await session.commit()

        found = await kb_repo.get_by_id(created.id)  # type: ignore[arg-type]
        assert found is None


# ── DocumentRepositoryImpl 测试 ──
# 注意: SQLite 默认不强制 FK 约束，可直接创建 Document 不创建 KB


@pytest.mark.integration
class TestDocumentRepositoryCreate:
    """文档创建测试。"""

    @pytest.mark.asyncio
    async def test_create_document(
        self,
        doc_repo: DocumentRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """创建文档，验证字段正确。"""
        doc = _make_doc(knowledge_base_id=1, filename="report.pdf", file_size=2048)
        created = await doc_repo.create(doc)
        await session.commit()

        assert created.id is not None
        assert created.knowledge_base_id == 1
        assert created.filename == "report.pdf"
        assert created.file_size == 2048
        assert created.status == DocumentStatus.UPLOADING
        assert created.content_type == "application/pdf"


@pytest.mark.integration
class TestDocumentRepositoryListByKnowledgeBase:
    """文档按知识库列表查询测试。"""

    @pytest.mark.asyncio
    async def test_list_by_knowledge_base(
        self,
        doc_repo: DocumentRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """按知识库 ID 查询文档列表。"""
        kb_id = 100
        await doc_repo.create(_make_doc(knowledge_base_id=kb_id, filename="a.pdf"))
        await doc_repo.create(_make_doc(knowledge_base_id=kb_id, filename="b.pdf"))
        await doc_repo.create(_make_doc(knowledge_base_id=kb_id, filename="c.pdf"))
        # 其他知识库的文档不应被返回
        await doc_repo.create(_make_doc(knowledge_base_id=999, filename="other.pdf"))
        await session.commit()

        results = await doc_repo.list_by_knowledge_base(kb_id, offset=0, limit=20)
        assert len(results) == 3
        assert all(d.knowledge_base_id == kb_id for d in results)


@pytest.mark.integration
class TestDocumentRepositoryCountByKnowledgeBase:
    """文档按知识库统计数量测试。"""

    @pytest.mark.asyncio
    async def test_count_by_knowledge_base(
        self,
        doc_repo: DocumentRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """按知识库 ID 统计文档数量。"""
        kb_id = 200
        await doc_repo.create(_make_doc(knowledge_base_id=kb_id, filename="x.pdf"))
        await doc_repo.create(_make_doc(knowledge_base_id=kb_id, filename="y.pdf"))
        # 其他知识库
        await doc_repo.create(_make_doc(knowledge_base_id=777, filename="z.pdf"))
        await session.commit()

        count = await doc_repo.count_by_knowledge_base(kb_id)
        assert count == 2


@pytest.mark.integration
class TestDocumentRepositoryUpdate:
    """文档更新测试。"""

    @pytest.mark.asyncio
    async def test_update_document(
        self,
        doc_repo: DocumentRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """修改 status，验证更新持久化。"""
        doc = _make_doc()
        created = await doc_repo.create(doc)
        await session.commit()

        # 通过实体方法将状态从 UPLOADING -> PROCESSING
        created.start_processing()
        updated = await doc_repo.update(created)
        await session.commit()

        assert updated.status == DocumentStatus.PROCESSING
        assert updated.id == created.id

        # 重新查询验证持久化
        found = await doc_repo.get_by_id(created.id)  # type: ignore[arg-type]
        assert found is not None
        assert found.status == DocumentStatus.PROCESSING


@pytest.mark.integration
class TestDocumentRepositoryDelete:
    """文档删除测试。"""

    @pytest.mark.asyncio
    async def test_delete_document(
        self,
        doc_repo: DocumentRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """删除后查询返回 None。"""
        doc = _make_doc()
        created = await doc_repo.create(doc)
        await session.commit()

        await doc_repo.delete(created.id)  # type: ignore[arg-type]
        await session.commit()

        found = await doc_repo.get_by_id(created.id)  # type: ignore[arg-type]
        assert found is None
