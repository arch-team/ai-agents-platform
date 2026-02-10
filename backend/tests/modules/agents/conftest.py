"""Agents 模块测试配置和 Fixture。"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.agents.application.services.agent_service import AgentService
from src.modules.agents.domain.entities.agent import Agent
from src.modules.agents.domain.repositories.agent_repository import IAgentRepository
from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus


def make_agent(
    *,
    agent_id: int = 1,
    name: str = "测试 Agent",
    description: str = "描述",
    system_prompt: str = "",
    status: AgentStatus = AgentStatus.DRAFT,
    owner_id: int = 100,
    config: AgentConfig | None = None,
) -> Agent:
    """创建测试用 Agent 实体。"""
    return Agent(
        id=agent_id,
        name=name,
        description=description,
        system_prompt=system_prompt,
        status=status,
        owner_id=owner_id,
        config=config or AgentConfig(),
    )


@pytest.fixture
def mock_agent_repo() -> AsyncMock:
    """Agent 仓库 Mock。"""
    return AsyncMock(spec=IAgentRepository)


@pytest.fixture
def agent_service(mock_agent_repo: AsyncMock) -> AgentService:
    """AgentService 实例（注入 mock 仓库）。"""
    return AgentService(mock_agent_repo)


@pytest.fixture
def mock_event_bus():
    """Mock event_bus，自动 patch AgentService 中的 event_bus。"""
    with patch(
        "src.modules.agents.application.services.agent_service.event_bus"
    ) as mock_bus:
        mock_bus.publish_async = AsyncMock()
        yield mock_bus
