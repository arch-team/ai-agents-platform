"""Agents API schemas 单元测试。"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.modules.agents.api.schemas.requests import CreateAgentRequest, UpdateAgentRequest
from src.modules.agents.api.schemas.responses import (
    AgentConfigResponse,
    AgentListResponse,
    AgentResponse,
)
from src.shared.domain.constants import MODEL_CLAUDE_HAIKU_45


@pytest.mark.unit
class TestCreateAgentRequest:
    """CreateAgentRequest 验证测试。"""

    def test_valid_request_with_defaults(self) -> None:
        req = CreateAgentRequest(name="test-agent")
        assert req.name == "test-agent"
        assert req.description == ""
        assert req.system_prompt == ""
        assert req.model_id == MODEL_CLAUDE_HAIKU_45
        assert req.temperature == 0.7
        assert req.max_tokens == 2048
        assert req.runtime_type == "agent"

    def test_valid_request_with_all_fields(self) -> None:
        req = CreateAgentRequest(
            name="my-agent",
            description="A test agent",
            system_prompt="You are helpful.",
            model_id="custom-model",
            temperature=0.5,
            max_tokens=1024,
        )
        assert req.name == "my-agent"
        assert req.description == "A test agent"
        assert req.temperature == 0.5

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateAgentRequest(name="")

    def test_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateAgentRequest(name="a" * 101)

    def test_description_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="description"):
            CreateAgentRequest(name="test", description="a" * 501)

    def test_temperature_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError, match="temperature"):
            CreateAgentRequest(name="test", temperature=-0.1)

    def test_temperature_above_one_raises(self) -> None:
        with pytest.raises(ValidationError, match="temperature"):
            CreateAgentRequest(name="test", temperature=1.1)

    def test_max_tokens_zero_raises(self) -> None:
        with pytest.raises(ValidationError, match="max_tokens"):
            CreateAgentRequest(name="test", max_tokens=0)

    def test_max_tokens_above_limit_raises(self) -> None:
        with pytest.raises(ValidationError, match="max_tokens"):
            CreateAgentRequest(name="test", max_tokens=4097)

    def test_runtime_type_agent(self) -> None:
        req = CreateAgentRequest(name="test", runtime_type="agent")
        assert req.runtime_type == "agent"

    def test_runtime_type_basic(self) -> None:
        req = CreateAgentRequest(name="test", runtime_type="basic")
        assert req.runtime_type == "basic"

    def test_runtime_type_invalid_raises(self) -> None:
        with pytest.raises(ValidationError, match="runtime_type"):
            CreateAgentRequest(name="test", runtime_type="invalid")

    def test_tool_ids_default_empty(self) -> None:
        req = CreateAgentRequest(name="test")
        assert req.tool_ids == []

    def test_tool_ids_with_values(self) -> None:
        req = CreateAgentRequest(name="test", tool_ids=[1, 2, 3])
        assert req.tool_ids == [1, 2, 3]

    def test_tool_ids_exceeds_max_length_raises(self) -> None:
        with pytest.raises(ValidationError, match="tool_ids"):
            CreateAgentRequest(name="test", tool_ids=list(range(51)))


@pytest.mark.unit
class TestUpdateAgentRequest:
    """UpdateAgentRequest 验证测试。"""

    def test_all_none_by_default(self) -> None:
        req = UpdateAgentRequest()
        assert req.name is None
        assert req.description is None
        assert req.system_prompt is None
        assert req.model_id is None
        assert req.temperature is None
        assert req.max_tokens is None
        assert req.runtime_type is None

    def test_partial_update(self) -> None:
        req = UpdateAgentRequest(name="new-name", temperature=0.3)
        assert req.name == "new-name"
        assert req.temperature == 0.3
        assert req.description is None

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            UpdateAgentRequest(name="")

    def test_temperature_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError, match="temperature"):
            UpdateAgentRequest(temperature=2.0)

    def test_update_runtime_type_valid(self) -> None:
        req = UpdateAgentRequest(runtime_type="basic")
        assert req.runtime_type == "basic"

    def test_update_runtime_type_invalid_raises(self) -> None:
        with pytest.raises(ValidationError, match="runtime_type"):
            UpdateAgentRequest(runtime_type="invalid")

    def test_update_tool_ids_default_none(self) -> None:
        req = UpdateAgentRequest()
        assert req.tool_ids is None

    def test_update_tool_ids_with_values(self) -> None:
        req = UpdateAgentRequest(tool_ids=[5, 10])
        assert req.tool_ids == [5, 10]

    def test_update_tool_ids_exceeds_max_length_raises(self) -> None:
        with pytest.raises(ValidationError, match="tool_ids"):
            UpdateAgentRequest(tool_ids=list(range(51)))


@pytest.mark.unit
class TestAgentConfigResponse:
    """AgentConfigResponse 序列化测试。"""

    def test_valid_response(self) -> None:
        resp = AgentConfigResponse(
            model_id="test-model",
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0,
            runtime_type="agent",
            enable_teams=False,
        )
        assert resp.model_id == "test-model"
        assert resp.top_p == 1.0
        assert resp.runtime_type == "agent"
        assert resp.tool_ids == []

    def test_response_with_tool_ids(self) -> None:
        resp = AgentConfigResponse(
            model_id="test-model",
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0,
            runtime_type="agent",
            enable_teams=False,
            tool_ids=[1, 2, 3],
        )
        assert resp.tool_ids == [1, 2, 3]


@pytest.mark.unit
class TestAgentResponse:
    """AgentResponse 序列化测试。"""

    def test_valid_response(self) -> None:
        now = datetime.now()
        resp = AgentResponse(
            id=1,
            name="test-agent",
            description="desc",
            system_prompt="prompt",
            status="draft",
            owner_id=10,
            config=AgentConfigResponse(
                model_id="model",
                temperature=0.7,
                max_tokens=2048,
                top_p=1.0,
                runtime_type="agent",
                enable_teams=False,
            ),
            created_at=now,
            updated_at=now,
        )
        assert resp.id == 1
        assert resp.config.model_id == "model"
        assert resp.config.runtime_type == "agent"


@pytest.mark.unit
class TestAgentListResponse:
    """AgentListResponse 序列化测试。"""

    def test_empty_list(self) -> None:
        resp = AgentListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )
        assert resp.items == []
        assert resp.total == 0

    def test_with_items(self) -> None:
        now = datetime.now()
        item = AgentResponse(
            id=1,
            name="agent",
            description="",
            system_prompt="",
            status="draft",
            owner_id=1,
            config=AgentConfigResponse(
                model_id="m",
                temperature=0.7,
                max_tokens=2048,
                top_p=1.0,
                runtime_type="agent",
                enable_teams=False,
            ),
            created_at=now,
            updated_at=now,
        )
        resp = AgentListResponse(
            items=[item],
            total=1,
            page=1,
            page_size=20,
            total_pages=1,
        )
        assert len(resp.items) == 1
        assert resp.total_pages == 1
