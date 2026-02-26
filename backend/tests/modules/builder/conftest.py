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


def make_builder_session(
    *,
    session_id: int = 1,
    user_id: int = 100,
    prompt: str = "创建一个代码审查 Agent",
    status: BuilderStatus = BuilderStatus.PENDING,
    generated_config: dict[str, Any] | None = None,
    agent_name: str | None = None,
    created_agent_id: int | None = None,
) -> BuilderSession:
    """创建测试用 BuilderSession 实体。"""
    session = BuilderSession(
        user_id=user_id,
        prompt=prompt,
        status=status,
        generated_config=generated_config,
        agent_name=agent_name,
        created_agent_id=created_agent_id,
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
def builder_service(
    mock_session_repo: AsyncMock,
    mock_llm_service: AsyncMock,
    mock_agent_creator: AsyncMock,
) -> BuilderService:
    """BuilderService 实例（注入 mock 依赖）。"""
    return BuilderService(
        session_repo=mock_session_repo,
        llm_service=mock_llm_service,
        agent_creator=mock_agent_creator,
    )
