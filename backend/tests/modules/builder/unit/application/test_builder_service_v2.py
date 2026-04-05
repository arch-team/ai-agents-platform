"""BuilderService V2 单元测试 — 多轮迭代 + Blueprint 确认 + 平台查询。"""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest

from src.modules.builder.application.dto.builder_dto import RefineBuilderDTO
from src.modules.builder.application.services.builder_service import BuilderService
from src.modules.builder.domain.value_objects.builder_status import BuilderStatus
from src.shared.domain.exceptions import InvalidStateTransitionError
from src.shared.domain.interfaces.agent_creator import CreatedAgentInfo
from src.shared.domain.interfaces.skill_creator import CreatedSkillInfo
from src.shared.domain.interfaces.skill_querier import SkillSummary
from src.shared.domain.interfaces.tool_querier import ApprovedToolInfo
from tests.modules.builder.conftest import (
    SAMPLE_GENERATED_BLUEPRINT,
    make_builder_session,
)


@pytest.mark.unit
class TestBuilderServiceRefine:
    """refine_session 多轮迭代测试。"""

    @pytest.mark.asyncio
    async def test_refine_session_triggers_generation(
        self,
        builder_service_v2: BuilderService,
        mock_session_repo: AsyncMock,
        mock_llm_service: AsyncMock,
        mock_tool_querier: AsyncMock,
        mock_skill_querier: AsyncMock,
    ) -> None:
        """确认状态 + 用户追加消息 → 触发 LLM 生成。"""
        session = make_builder_session(
            session_id=1,
            user_id=100,
            status=BuilderStatus.CONFIRMED,
            generated_config={},
            generated_blueprint=SAMPLE_GENERATED_BLUEPRINT,
            messages=[{"role": "user", "content": "初始请求"}],
        )
        mock_session_repo.get_by_id.return_value = session

        # LLM 返回更新后的 Blueprint
        llm_output = """
[PERSONA]
role: 安克售后客服v2
background: 更新后的描述
tone: casual
[/PERSONA]

[GUARDRAILS]
- rule: 新护栏规则, severity: warn
[/GUARDRAILS]
"""

        async def mock_generate(*_args: object, **_kwargs: object) -> AsyncIterator[str]:
            yield llm_output

        mock_llm_service.generate_blueprint.return_value = mock_generate()
        mock_tool_querier.list_approved_tools.return_value = []
        mock_skill_querier.list_published_skills.return_value = []

        # 模拟 update 返回更新后的 session
        updated_session = make_builder_session(
            session_id=1,
            user_id=100,
            status=BuilderStatus.CONFIRMED,
            generated_config={},
            generated_blueprint={"persona": {"role": "安克售后客服v2"}},
        )
        mock_session_repo.update.return_value = updated_session

        chunks: list[str] = []
        async for chunk in builder_service_v2.refine_session(
            session_id=1,
            user_id=100,
            dto=RefineBuilderDTO(message="请改为更休闲的风格"),
        ):
            chunks.append(chunk)

        assert len(chunks) >= 1
        # 确认 start_refinement 被调用 (session 状态变化)
        assert mock_session_repo.update.call_count >= 1

    @pytest.mark.asyncio
    async def test_refine_session_pending_raises(
        self,
        builder_service_v2: BuilderService,
        mock_session_repo: AsyncMock,
    ) -> None:
        """PENDING 状态不能 refine。"""
        session = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.PENDING)
        mock_session_repo.get_by_id.return_value = session

        with pytest.raises(InvalidStateTransitionError):
            async for _ in builder_service_v2.refine_session(
                1,
                100,
                dto=RefineBuilderDTO(message="修改"),
            ):
                pass


@pytest.mark.unit
class TestBuilderServiceConfirmV2:
    """V2 confirm_session — Blueprint 解析 + Skill 创建 + Agent 创建。"""

    @pytest.mark.asyncio
    async def test_confirm_with_blueprint_creates_agent(
        self,
        builder_service_v2: BuilderService,
        mock_session_repo: AsyncMock,
        mock_agent_creator: AsyncMock,
        mock_skill_creator: AsyncMock,
    ) -> None:
        """V2 确认: 解析 Blueprint → 创建 Skills → 创建 Agent。"""
        session = make_builder_session(
            session_id=1,
            user_id=100,
            status=BuilderStatus.CONFIRMED,
            generated_config={},
            agent_name="安克客服",
            generated_blueprint=SAMPLE_GENERATED_BLUEPRINT,
        )
        mock_session_repo.get_by_id.return_value = session

        # Skill 创建成功
        mock_skill_creator.create_skill.return_value = CreatedSkillInfo(
            id=10,
            name="return-processing",
            file_path="drafts/return-processing",
        )
        mock_skill_creator.publish_skill.return_value = CreatedSkillInfo(
            id=10,
            name="return-processing",
            file_path="published/return-processing/v1",
        )

        # Agent 创建成功
        agent_info = CreatedAgentInfo(id=42, name="安克客服", status="draft")
        mock_agent_creator.create_agent_with_blueprint.return_value = agent_info

        confirmed = make_builder_session(
            session_id=1,
            user_id=100,
            status=BuilderStatus.CONFIRMED,
            generated_config={},
            agent_name="安克客服",
            generated_blueprint=SAMPLE_GENERATED_BLUEPRINT,
            created_agent_id=42,
        )
        mock_session_repo.update.return_value = confirmed

        result = await builder_service_v2.confirm_session(1, 100)

        assert result.created_agent_id == 42
        mock_skill_creator.create_skill.assert_called_once()
        mock_skill_creator.publish_skill.assert_called_once()
        mock_agent_creator.create_agent_with_blueprint.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_v1_fallback_without_blueprint(
        self,
        builder_service_v2: BuilderService,
        mock_session_repo: AsyncMock,
        mock_agent_creator: AsyncMock,
    ) -> None:
        """V1 兼容: 无 Blueprint 时走旧的 JSON 配置路径。"""
        from tests.modules.builder.conftest import SAMPLE_GENERATED_CONFIG

        session = make_builder_session(
            session_id=1,
            user_id=100,
            status=BuilderStatus.CONFIRMED,
            generated_config=SAMPLE_GENERATED_CONFIG,
            agent_name="代码审查助手",
            generated_blueprint=None,
        )
        mock_session_repo.get_by_id.return_value = session

        agent_info = CreatedAgentInfo(id=42, name="代码审查助手", status="draft")
        mock_agent_creator.create_agent.return_value = agent_info

        confirmed = make_builder_session(
            session_id=1,
            user_id=100,
            status=BuilderStatus.CONFIRMED,
            generated_config=SAMPLE_GENERATED_CONFIG,
            agent_name="代码审查助手",
            created_agent_id=42,
        )
        mock_session_repo.update.return_value = confirmed

        result = await builder_service_v2.confirm_session(1, 100)

        assert result.created_agent_id == 42
        mock_agent_creator.create_agent.assert_called_once()


@pytest.mark.unit
class TestBuilderServicePlatformQueries:
    """平台能力查询测试。"""

    @pytest.mark.asyncio
    async def test_get_available_tools(
        self,
        builder_service_v2: BuilderService,
        mock_tool_querier: AsyncMock,
    ) -> None:
        mock_tool_querier.list_approved_tools.return_value = [
            ApprovedToolInfo(id=1, name="订单查询", description="查询", tool_type="api"),
        ]
        tools = await builder_service_v2.get_available_tools()
        assert len(tools) == 1
        assert tools[0].name == "订单查询"

    @pytest.mark.asyncio
    async def test_get_available_skills(
        self,
        builder_service_v2: BuilderService,
        mock_skill_querier: AsyncMock,
    ) -> None:
        mock_skill_querier.list_published_skills.return_value = [
            SkillSummary(id=10, name="退货处理", description="处理退货", category="售后"),
        ]
        skills = await builder_service_v2.get_available_skills()
        assert len(skills) == 1
        assert skills[0].name == "退货处理"

    @pytest.mark.asyncio
    async def test_get_available_tools_no_querier(
        self,
        builder_service: BuilderService,
    ) -> None:
        """V1 service (无 tool_querier) 返回空列表。"""
        tools = await builder_service.get_available_tools()
        assert tools == []


@pytest.mark.unit
class TestBuilderServiceGenerateBlueprint:
    """generate_blueprint_stream 测试。"""

    @pytest.mark.asyncio
    async def test_generate_blueprint_stream_parses_output(
        self,
        builder_service_v2: BuilderService,
        mock_session_repo: AsyncMock,
        mock_llm_service: AsyncMock,
        mock_tool_querier: AsyncMock,
        mock_skill_querier: AsyncMock,
    ) -> None:
        """PENDING → GENERATING → CONFIRMED (解析成功时)。"""
        session = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.PENDING)
        mock_session_repo.get_by_id.return_value = session
        mock_tool_querier.list_approved_tools.return_value = []
        mock_skill_querier.list_published_skills.return_value = []

        llm_output = """
[PERSONA]
role: 测试角色
background: 测试背景
tone: casual
[/PERSONA]
"""

        async def mock_generate(*_args: object, **_kwargs: object) -> AsyncIterator[str]:
            yield llm_output

        mock_llm_service.generate_blueprint.return_value = mock_generate()

        chunks: list[str] = []
        async for chunk in builder_service_v2.generate_blueprint_stream(1, 100):
            chunks.append(chunk)

        assert len(chunks) >= 1
        # session 应该被 update 多次 (start_generation + complete_generation)
        assert mock_session_repo.update.call_count >= 2

    @pytest.mark.asyncio
    async def test_generate_blueprint_stream_no_sections_stays_generating(
        self,
        builder_service_v2: BuilderService,
        mock_session_repo: AsyncMock,
        mock_llm_service: AsyncMock,
        mock_tool_querier: AsyncMock,
        mock_skill_querier: AsyncMock,
    ) -> None:
        """LLM 返回纯引导文本 (无结构化段) 时, session 保持 GENERATING。"""
        session = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.PENDING)
        mock_session_repo.get_by_id.return_value = session
        mock_tool_querier.list_approved_tools.return_value = []
        mock_skill_querier.list_published_skills.return_value = []

        async def mock_generate(*_args: object, **_kwargs: object) -> AsyncIterator[str]:
            yield "好的, 让我们开始吧。请描述您的业务场景。"

        mock_llm_service.generate_blueprint.return_value = mock_generate()

        chunks: list[str] = []
        async for chunk in builder_service_v2.generate_blueprint_stream(1, 100):
            chunks.append(chunk)

        assert len(chunks) == 1
        # session 应该还是 GENERATING (没有 complete_generation)
        # 最后一次 update 的 session 对象 status 应为 GENERATING
        last_update_call = mock_session_repo.update.call_args_list[-1]
        saved_session = last_update_call[0][0]
        assert saved_session.status == BuilderStatus.GENERATING


@pytest.mark.unit
class TestBuilderServiceAutoStartTesting:
    """auto_start_testing 测试。"""

    @pytest.mark.asyncio
    async def test_confirm_with_auto_start_testing(
        self,
        builder_service_v2: BuilderService,
        mock_session_repo: AsyncMock,
        mock_agent_creator: AsyncMock,
        mock_agent_lifecycle: AsyncMock,
        mock_skill_creator: AsyncMock,
    ) -> None:
        """auto_start_testing=True 时通过 IAgentLifecycle 调用 start_testing。"""
        session = make_builder_session(
            session_id=1,
            user_id=100,
            status=BuilderStatus.CONFIRMED,
            generated_config={},
            agent_name="测试",
            generated_blueprint=SAMPLE_GENERATED_BLUEPRINT,
        )
        mock_session_repo.get_by_id.return_value = session

        mock_skill_creator.create_skill.return_value = CreatedSkillInfo(
            id=10,
            name="s",
            file_path="drafts/s",
        )
        mock_skill_creator.publish_skill.return_value = CreatedSkillInfo(
            id=10,
            name="s",
            file_path="published/s/v1",
        )
        agent_info = CreatedAgentInfo(id=42, name="测试", status="draft")
        mock_agent_creator.create_agent_with_blueprint.return_value = agent_info
        mock_agent_lifecycle.start_testing.return_value = CreatedAgentInfo(id=42, name="测试", status="testing")

        confirmed = make_builder_session(
            session_id=1,
            user_id=100,
            status=BuilderStatus.CONFIRMED,
            generated_config={},
            agent_name="测试",
            generated_blueprint=SAMPLE_GENERATED_BLUEPRINT,
            created_agent_id=42,
        )
        mock_session_repo.update.return_value = confirmed

        await builder_service_v2.confirm_session(1, 100, auto_start_testing=True)

        mock_agent_lifecycle.start_testing.assert_called_once_with(42, 100)
