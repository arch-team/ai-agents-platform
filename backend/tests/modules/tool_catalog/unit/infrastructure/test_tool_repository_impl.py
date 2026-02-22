"""ToolRepositoryImpl 单元测试。"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.repositories.tool_repository import IToolRepository
from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.modules.tool_catalog.infrastructure.persistence.models.tool_model import ToolModel
from src.modules.tool_catalog.infrastructure.persistence.repositories.tool_repository_impl import (
    ToolRepositoryImpl,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


@pytest.mark.unit
class TestToolRepositoryImplStructure:
    def test_implements_itool_repository(self) -> None:
        assert issubclass(ToolRepositoryImpl, IToolRepository)

    def test_extends_pydantic_repository(self) -> None:
        assert issubclass(ToolRepositoryImpl, PydanticRepository)

    def test_entity_class_is_tool(self) -> None:
        assert ToolRepositoryImpl.entity_class is Tool

    def test_model_class_is_tool_model(self) -> None:
        assert ToolRepositoryImpl.model_class is ToolModel

    def test_updatable_fields_defined(self) -> None:
        expected = frozenset(
            {
                "name",
                "description",
                "version",
                "status",
                "server_url",
                "transport",
                "endpoint_url",
                "method",
                "headers",
                "runtime",
                "handler",
                "code_uri",
                "auth_type",
                "auth_config",
                "allowed_roles",
                "gateway_target_id",
                "reviewer_id",
                "review_comment",
                "reviewed_at",
            },
        )
        assert ToolRepositoryImpl._updatable_fields == expected


@pytest.mark.unit
class TestToolRepositoryImplToEntity:
    def test_to_entity_converts_model_with_default_config(self) -> None:
        now = datetime.now(UTC)
        model = ToolModel(
            id=1,
            name="测试 Tool",
            description="描述",
            tool_type="mcp_server",
            version="1.0.0",
            status="draft",
            creator_id=42,
            server_url="http://localhost:8080",
            transport="stdio",
            endpoint_url="",
            method="POST",
            headers="",
            runtime="",
            handler="",
            code_uri="",
            auth_type="none",
            auth_config="",
            allowed_roles='["admin","developer"]',
            gateway_target_id="",
            reviewer_id=None,
            review_comment="",
            reviewed_at=None,
            created_at=now,
            updated_at=now,
        )
        repo = ToolRepositoryImpl.__new__(ToolRepositoryImpl)
        entity = repo._to_entity(model)

        assert isinstance(entity, Tool)
        assert entity.id == 1
        assert entity.name == "测试 Tool"
        assert entity.description == "描述"
        assert entity.tool_type == ToolType.MCP_SERVER
        assert entity.version == "1.0.0"
        assert entity.status == ToolStatus.DRAFT
        assert entity.creator_id == 42
        assert entity.config.server_url == "http://localhost:8080"
        assert entity.config.transport == "stdio"
        assert entity.config.headers == ()
        assert entity.config.auth_type == "none"
        assert entity.config.auth_config == ()
        assert entity.allowed_roles == ("admin", "developer")
        assert entity.gateway_target_id == ""
        assert entity.reviewer_id is None
        assert entity.reviewed_at is None

    def test_to_entity_parses_json_fields(self) -> None:
        now = datetime.now(UTC)
        headers_json = json.dumps([["Content-Type", "application/json"], ["X-Api-Key", "key"]])
        auth_config_json = json.dumps([["api_key", "secret123"]])
        model = ToolModel(
            id=2,
            name="API Tool",
            description="API 工具",
            tool_type="api",
            version="2.0.0",
            status="approved",
            creator_id=1,
            server_url="",
            transport="stdio",
            endpoint_url="https://api.example.com/v1",
            method="GET",
            headers=headers_json,
            runtime="",
            handler="",
            code_uri="",
            auth_type="api_key",
            auth_config=auth_config_json,
            allowed_roles='["admin"]',
            gateway_target_id="",
            reviewer_id=10,
            review_comment="通过审批",
            reviewed_at=now,
            created_at=now,
            updated_at=now,
        )
        repo = ToolRepositoryImpl.__new__(ToolRepositoryImpl)
        entity = repo._to_entity(model)

        assert entity.tool_type == ToolType.API
        assert entity.status == ToolStatus.APPROVED
        assert entity.config.headers == (("Content-Type", "application/json"), ("X-Api-Key", "key"))
        assert entity.config.auth_config == (("api_key", "secret123"),)
        assert entity.allowed_roles == ("admin",)
        assert entity.reviewer_id == 10
        assert entity.review_comment == "通过审批"


@pytest.mark.unit
class TestToolRepositoryImplToModel:
    def test_to_model_converts_entity_with_default_config(self) -> None:
        tool = Tool(
            id=1,
            name="测试 Tool",
            description="描述",
            tool_type=ToolType.MCP_SERVER,
            version="1.0.0",
            status=ToolStatus.DRAFT,
            creator_id=42,
            config=ToolConfig(server_url="http://localhost:8080"),
        )
        repo = ToolRepositoryImpl.__new__(ToolRepositoryImpl)
        model = repo._to_model(tool)

        assert isinstance(model, ToolModel)
        assert model.name == "测试 Tool"
        assert model.tool_type == "mcp_server"
        assert model.status == "draft"
        assert model.creator_id == 42
        assert model.server_url == "http://localhost:8080"
        assert model.headers == ""
        assert model.auth_config == ""
        assert model.allowed_roles == '["admin", "developer"]'

    def test_to_model_serializes_json_fields(self) -> None:
        tool = Tool(
            id=2,
            name="API Tool",
            description="API 工具",
            tool_type=ToolType.API,
            status=ToolStatus.APPROVED,
            creator_id=1,
            config=ToolConfig(
                endpoint_url="https://api.example.com",
                headers=(("Content-Type", "application/json"),),
                auth_type="api_key",
                auth_config=(("api_key", "secret"),),
            ),
            allowed_roles=("admin",),
            reviewer_id=10,
        )
        repo = ToolRepositoryImpl.__new__(ToolRepositoryImpl)
        model = repo._to_model(tool)

        assert model.tool_type == "api"
        assert model.status == "approved"
        assert json.loads(model.headers) == [["Content-Type", "application/json"]]
        assert json.loads(model.auth_config) == [["api_key", "secret"]]
        assert json.loads(model.allowed_roles) == ["admin"]


@pytest.mark.unit
class TestToolRepositoryImplGetUpdateData:
    def test_get_update_data_flattens_config(self) -> None:
        tool = Tool(
            id=1,
            name="New Name",
            description="New Desc",
            tool_type=ToolType.FUNCTION,
            status=ToolStatus.DRAFT,
            creator_id=42,
            config=ToolConfig(
                runtime="python3.12",
                handler="index.handler",
                code_uri="s3://bucket/code.zip",
            ),
        )
        repo = ToolRepositoryImpl.__new__(ToolRepositoryImpl)
        data = repo._get_update_data(tool)

        assert data["name"] == "New Name"
        assert data["description"] == "New Desc"
        assert data["version"] == "1.0.0"
        assert data["status"] == "draft"
        assert data["runtime"] == "python3.12"
        assert data["handler"] == "index.handler"
        assert data["code_uri"] == "s3://bucket/code.zip"
        assert data["auth_type"] == "none"

    def test_get_update_data_only_includes_updatable_fields(self) -> None:
        tool = Tool(
            id=1,
            name="Name",
            description="",
            tool_type=ToolType.MCP_SERVER,
            status=ToolStatus.DRAFT,
            creator_id=42,
        )
        repo = ToolRepositoryImpl.__new__(ToolRepositoryImpl)
        data = repo._get_update_data(tool)

        # creator_id, tool_type 不在 _updatable_fields 中
        assert "creator_id" not in data
        assert "tool_type" not in data
        assert "id" not in data
        assert "created_at" not in data
        assert "updated_at" not in data

    def test_get_update_data_serializes_json_fields(self) -> None:
        tool = Tool(
            id=1,
            name="Tool",
            description="",
            tool_type=ToolType.API,
            status=ToolStatus.DRAFT,
            creator_id=1,
            config=ToolConfig(
                headers=(("X-Key", "val"),),
                auth_config=(("key", "secret"),),
            ),
            allowed_roles=("admin", "viewer"),
        )
        repo = ToolRepositoryImpl.__new__(ToolRepositoryImpl)
        data = repo._get_update_data(tool)

        assert json.loads(data["headers"]) == [["X-Key", "val"]]  # type: ignore[arg-type]
        assert json.loads(data["auth_config"]) == [["key", "secret"]]  # type: ignore[arg-type]
        assert json.loads(data["allowed_roles"]) == ["admin", "viewer"]  # type: ignore[arg-type]


@pytest.mark.unit
class TestToolRepositoryImplQueryMethods:
    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session: AsyncMock) -> ToolRepositoryImpl:
        return ToolRepositoryImpl(session=mock_session)

    @pytest.mark.asyncio
    async def test_get_by_name_and_creator_returns_none_when_not_found(
        self, repo: ToolRepositoryImpl, mock_session: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_name_and_creator("不存在", creator_id=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_name_and_creator_returns_tool_when_found(
        self, repo: ToolRepositoryImpl, mock_session: AsyncMock,
    ) -> None:
        now = datetime.now(UTC)
        mock_model = ToolModel(
            id=1,
            name="测试 Tool",
            description="描述",
            tool_type="mcp_server",
            version="1.0.0",
            status="draft",
            creator_id=42,
            server_url="http://localhost",
            transport="stdio",
            endpoint_url="",
            method="POST",
            headers="",
            runtime="",
            handler="",
            code_uri="",
            auth_type="none",
            auth_config="",
            allowed_roles='["admin","developer"]',
            gateway_target_id="",
            reviewer_id=None,
            review_comment="",
            reviewed_at=None,
            created_at=now,
            updated_at=now,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_name_and_creator("测试 Tool", creator_id=42)
        assert result is not None
        assert result.name == "测试 Tool"
        assert result.creator_id == 42

    @pytest.mark.asyncio
    async def test_count_by_creator_returns_count(
        self, repo: ToolRepositoryImpl, mock_session: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_result

        result = await repo.count_by_creator(creator_id=42)
        assert result == 5

    @pytest.mark.asyncio
    async def test_count_approved_returns_count(
        self, repo: ToolRepositoryImpl, mock_session: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 3
        mock_session.execute.return_value = mock_result

        result = await repo.count_approved()
        assert result == 3

    @pytest.mark.asyncio
    async def test_list_by_creator_returns_empty_list(
        self, repo: ToolRepositoryImpl, mock_session: AsyncMock,
    ) -> None:
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repo.list_by_creator(creator_id=42)
        assert result == []

    @pytest.mark.asyncio
    async def test_list_approved_returns_empty_list(
        self, repo: ToolRepositoryImpl, mock_session: AsyncMock,
    ) -> None:
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repo.list_approved()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_filtered_returns_empty_list(
        self, repo: ToolRepositoryImpl, mock_session: AsyncMock,
    ) -> None:
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repo.list_filtered(status=ToolStatus.APPROVED, tool_type=ToolType.API)
        assert result == []

    @pytest.mark.asyncio
    async def test_count_filtered_returns_count(
        self, repo: ToolRepositoryImpl, mock_session: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 7
        mock_session.execute.return_value = mock_result

        result = await repo.count_filtered(
            status=ToolStatus.DRAFT, keyword="test", creator_id=1,
        )
        assert result == 7
