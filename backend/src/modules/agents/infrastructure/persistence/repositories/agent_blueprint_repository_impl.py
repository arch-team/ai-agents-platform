"""Agent Blueprint 仓库实现。"""

import json

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.agents.domain.repositories.agent_blueprint_repository import (
    BlueprintDetailInfo,
    BlueprintRuntimeInfo,
    BlueprintToolBindingInfo,
    CreateBlueprintDTO,
    IAgentBlueprintRepository,
)
from src.modules.agents.infrastructure.persistence.models.agent_blueprint_model import (
    AgentBlueprintModel,
    AgentBlueprintSkillModel,
    AgentBlueprintToolBindingModel,
)


class AgentBlueprintRepositoryImpl(IAgentBlueprintRepository):
    """Agent Blueprint 仓库的 SQLAlchemy 实现。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_blueprint(self, dto: CreateBlueprintDTO) -> int:
        """创建 Blueprint + 关联的 skills 和 tool_bindings。"""
        model = AgentBlueprintModel(
            agent_id=dto.agent_id,
            persona_config=dto.persona_config,
            memory_config=dto.memory_config,
            guardrails=dto.guardrails,
            model_config_json=dto.model_config_json,
            knowledge_base_ids=dto.knowledge_base_ids,
            workspace_path=dto.workspace_path,
        )
        self._session.add(model)
        await self._session.flush()

        # 关联 skills
        for i, skill_id in enumerate(dto.skill_ids):
            skill_assoc = AgentBlueprintSkillModel(
                blueprint_id=model.id,
                skill_id=skill_id,
                sort_order=i,
            )
            self._session.add(skill_assoc)

        # 关联 tool_bindings
        for i, tb in enumerate(dto.tool_bindings):
            tb_model = AgentBlueprintToolBindingModel(
                blueprint_id=model.id,
                tool_id=tb.tool_id,
                display_name=tb.display_name,
                usage_hint=tb.usage_hint,
                sort_order=i,
            )
            self._session.add(tb_model)

        await self._session.flush()
        return model.id

    async def get_runtime_info(self, agent_id: int) -> BlueprintRuntimeInfo | None:
        stmt = select(
            AgentBlueprintModel.id,
            AgentBlueprintModel.workspace_path,
            AgentBlueprintModel.runtime_arn,
            AgentBlueprintModel.workspace_s3_uri,
        ).where(AgentBlueprintModel.agent_id == agent_id)

        result = await self._session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None

        return BlueprintRuntimeInfo(
            blueprint_id=row[0],
            workspace_path=row[1],
            runtime_arn=row[2],
            workspace_s3_uri=row[3],
        )

    async def update_runtime_info(
        self,
        agent_id: int,
        *,
        runtime_arn: str,
        workspace_s3_uri: str,
    ) -> None:
        stmt = (
            update(AgentBlueprintModel)
            .where(AgentBlueprintModel.agent_id == agent_id)
            .values(runtime_arn=runtime_arn, workspace_s3_uri=workspace_s3_uri)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def update_workspace_path(self, agent_id: int, workspace_path: str) -> None:
        stmt = (
            update(AgentBlueprintModel)
            .where(AgentBlueprintModel.agent_id == agent_id)
            .values(workspace_path=workspace_path)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def clear_runtime_info(self, agent_id: int) -> None:
        stmt = (
            update(AgentBlueprintModel)
            .where(AgentBlueprintModel.agent_id == agent_id)
            .values(runtime_arn="", workspace_s3_uri="")
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_blueprint_detail(self, agent_id: int) -> BlueprintDetailInfo | None:
        # 查询主表配置字段
        bp_stmt = select(
            AgentBlueprintModel.id,
            AgentBlueprintModel.persona_config,
            AgentBlueprintModel.guardrails,
            AgentBlueprintModel.memory_config,
            AgentBlueprintModel.knowledge_base_ids,
        ).where(AgentBlueprintModel.agent_id == agent_id)

        bp_row = (await self._session.execute(bp_stmt)).one_or_none()
        if bp_row is None:
            return None

        blueprint_id = bp_row[0]

        # 查询关联 skills
        skill_stmt = (
            select(AgentBlueprintSkillModel.skill_id)
            .where(AgentBlueprintSkillModel.blueprint_id == blueprint_id)
            .order_by(AgentBlueprintSkillModel.sort_order)
        )
        skill_rows = (await self._session.execute(skill_stmt)).all()

        # 查询关联 tool_bindings
        tb_stmt = (
            select(
                AgentBlueprintToolBindingModel.tool_id,
                AgentBlueprintToolBindingModel.display_name,
                AgentBlueprintToolBindingModel.usage_hint,
            )
            .where(AgentBlueprintToolBindingModel.blueprint_id == blueprint_id)
            .order_by(AgentBlueprintToolBindingModel.sort_order)
        )
        tb_rows = (await self._session.execute(tb_stmt)).all()

        return BlueprintDetailInfo(
            blueprint_id=blueprint_id,
            persona=json.loads(bp_row[1]),
            guardrails=json.loads(bp_row[2]),
            memory_config=json.loads(bp_row[3]),
            knowledge_base_ids=json.loads(bp_row[4]),
            skill_ids=[r[0] for r in skill_rows],
            tool_bindings=[BlueprintToolBindingInfo(tool_id=r[0], display_name=r[1], usage_hint=r[2]) for r in tb_rows],
        )
