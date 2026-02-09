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


@pytest.mark.unit
class TestCreateAgentRequest:
    """CreateAgentRequest 验证测试。"""

    def test_valid_request_with_defaults(self) -> None:
        req = CreateAgentRequest(name="test-agent")
        assert req.name == "test-agent"
        assert req.description == ""
        assert req.system_prompt == ""
        assert req.model_id == "anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert req.temperature == 0.7
        assert req.max_tokens == 2048

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


@pytest.mark.unit
class TestAgentConfigResponse:
    """AgentConfigResponse 序列化测试。"""

    def test_valid_response(self) -> None:
        resp = AgentConfigResponse(
            model_id="test-model", temperature=0.7, max_tokens=2048, top_p=1.0,
        )
        assert resp.model_id == "test-model"
        assert resp.top_p == 1.0


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
                model_id="model", temperature=0.7, max_tokens=2048, top_p=1.0,
            ),
            created_at=now,
            updated_at=now,
        )
        assert resp.id == 1
        assert resp.config.model_id == "model"


@pytest.mark.unit
class TestAgentListResponse:
    """AgentListResponse 序列化测试。"""

    def test_empty_list(self) -> None:
        resp = AgentListResponse(
            items=[], total=0, page=1, page_size=20, total_pages=0,
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
                model_id="m", temperature=0.7, max_tokens=2048, top_p=1.0,
            ),
            created_at=now,
            updated_at=now,
        )
        resp = AgentListResponse(
            items=[item], total=1, page=1, page_size=20, total_pages=1,
        )
        assert len(resp.items) == 1
        assert resp.total_pages == 1
