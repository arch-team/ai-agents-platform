"""Builder 模块测试配置和 Fixture。"""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.modules.builder.application.interfaces.builder_llm_service import IBuilderLLMService
from src.modules.builder.application.services.builder_service import BuilderService
from src.modules.builder.domain.entities.builder_session import BuilderSession
from src.modules.builder.domain.repositories.builder_session_repository import IBuilderSessionRepository
from src.modules.builder.domain.value_objects.builder_status import BuilderStatus
from src.shared.domain.constants import MODEL_CLAUDE_SONNET_46
from src.shared.domain.interfaces.agent_creator import IAgentCreator
from src.shared.domain.interfaces.skill_creator import ISkillCreator
from src.shared.domain.interfaces.skill_querier import ISkillQuerier
from src.shared.domain.interfaces.tool_querier import IToolQuerier


def make_builder_session(
    *,
    session_id: int = 1,
    user_id: int = 100,
    prompt: str = "创建一个代码审查 Agent",
    status: BuilderStatus = BuilderStatus.PENDING,
    generated_config: dict[str, Any] | None = None,
    agent_name: str | None = None,
    created_agent_id: int | None = None,
    messages: list[dict[str, str]] | None = None,
    template_id: int | None = None,
    selected_skill_ids: list[int] | None = None,
    generated_blueprint: dict[str, Any] | None = None,
) -> BuilderSession:
    """创建测试用 BuilderSession 实体。"""
    session = BuilderSession(
        user_id=user_id,
        prompt=prompt,
        status=status,
        generated_config=generated_config,
        agent_name=agent_name,
        created_agent_id=created_agent_id,
        messages=messages or [],
        template_id=template_id,
        selected_skill_ids=selected_skill_ids or [],
        generated_blueprint=generated_blueprint,
    )
    object.__setattr__(session, "id", session_id)
    return session


SAMPLE_GENERATED_CONFIG: dict[str, Any] = {
    "name": "代码审查助手",
    "description": "帮助审查代码质量的 AI Agent",
    "system_prompt": "你是一个专业的代码审查助手",
    "model_id": MODEL_CLAUDE_SONNET_46,
    "temperature": 0.7,
    "max_tokens": 4096,
}


SAMPLE_GENERATED_BLUEPRINT: dict[str, Any] = {
    "persona": {"role": "安克售后客服", "background": "熟悉安克产品线", "tone": "professional_friendly"},
    "skills": [
        {"name": "return-processing", "trigger": "客户提到退货", "steps": ["1. 查询订单"], "rules": ["先安抚"]},
    ],
    "tool_bindings": [{"tool_id": 3, "display_name": "订单查询", "usage_hint": "查询时调用"}],
    "guardrails": [{"rule": "不得承诺超出政策的退款", "severity": "block"}],
}


@pytest.fixture
def mock_session_repo() -> AsyncMock:
    """BuilderSession 仓库 Mock。"""
    return AsyncMock(spec=IBuilderSessionRepository)


@pytest.fixture
def mock_llm_service() -> AsyncMock:
    """Builder LLM 服务 Mock。"""
    return AsyncMock(spec=IBuilderLLMService)


@pytest.fixture
def mock_agent_creator() -> AsyncMock:
    """IAgentCreator Mock。"""
    return AsyncMock(spec=IAgentCreator)


@pytest.fixture
def mock_skill_creator() -> AsyncMock:
    """ISkillCreator Mock。"""
    return AsyncMock(spec=ISkillCreator)


@pytest.fixture
def mock_tool_querier() -> AsyncMock:
    """IToolQuerier Mock。"""
    return AsyncMock(spec=IToolQuerier)


@pytest.fixture
def mock_skill_querier() -> AsyncMock:
    """ISkillQuerier Mock。"""
    return AsyncMock(spec=ISkillQuerier)


@pytest.fixture
def builder_service(
    mock_session_repo: AsyncMock,
    mock_llm_service: AsyncMock,
    mock_agent_creator: AsyncMock,
) -> BuilderService:
    """V1 BuilderService 实例（注入最小 mock 依赖，兼容旧测试）。"""
    return BuilderService(
        session_repo=mock_session_repo,
        llm_service=mock_llm_service,
        agent_creator=mock_agent_creator,
    )


@pytest.fixture
def builder_service_v2(
    mock_session_repo: AsyncMock,
    mock_llm_service: AsyncMock,
    mock_agent_creator: AsyncMock,
    mock_skill_creator: AsyncMock,
    mock_tool_querier: AsyncMock,
    mock_skill_querier: AsyncMock,
) -> BuilderService:
    """V2 BuilderService 实例（注入全部依赖）。"""
    return BuilderService(
        session_repo=mock_session_repo,
        llm_service=mock_llm_service,
        agent_creator=mock_agent_creator,
        skill_creator=mock_skill_creator,
        tool_querier=mock_tool_querier,
        skill_querier=mock_skill_querier,
    )
