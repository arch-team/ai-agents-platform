"""Insights API 端点。"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.insights.api.dependencies import get_insights_service
from src.modules.insights.api.schemas.responses import (
    UsageRecordListResponse,
    UsageRecordResponse,
    UsageSummaryResponse,
)
from src.modules.insights.application.dto.insights_dto import (
    UsageRecordDTO,
)
from src.modules.insights.application.services.insights_service import InsightsService
from src.shared.api.schemas import calc_total_pages


router = APIRouter(prefix="/api/v1/insights", tags=["insights"])

ServiceDep = Annotated[InsightsService, Depends(get_insights_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


def _to_record_response(dto: UsageRecordDTO) -> UsageRecordResponse:
    return UsageRecordResponse(
        id=dto.id,
        user_id=dto.user_id,
        agent_id=dto.agent_id,
        conversation_id=dto.conversation_id,
        model_id=dto.model_id,
        tokens_input=dto.tokens_input,
        tokens_output=dto.tokens_output,
        estimated_cost=dto.estimated_cost,
        recorded_at=dto.recorded_at,
        created_at=dto.created_at,
    )


@router.get("/usage-records")
async def list_usage_records(
    service: ServiceDep,
    current_user: CurrentUserDep,
    user_id: Annotated[int | None, Query()] = None,
    agent_id: Annotated[int | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UsageRecordListResponse:
    """获取使用记录列表 (支持用户/Agent 过滤)。"""
    # 非 ADMIN 用户只能查看自己的数据
    effective_user_id = user_id if current_user.role == "admin" else current_user.id

    paged = await service.list_usage_records(
        user_id=effective_user_id,
        agent_id=agent_id,
        page=page,
        page_size=page_size,
    )
    return UsageRecordListResponse(
        items=[_to_record_response(r) for r in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/usage-records/{record_id}")
async def get_usage_record(
    record_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,  # noqa: ARG001
) -> UsageRecordResponse:
    """获取使用记录详情。"""
    dto = await service.get_usage_record(record_id)
    return _to_record_response(dto)


@router.get("/summary")
async def get_usage_summary(
    service: ServiceDep,
    current_user: CurrentUserDep,
    user_id: Annotated[int | None, Query()] = None,
    agent_id: Annotated[int | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    period: Annotated[str, Query()] = "all",
) -> UsageSummaryResponse:
    """获取使用量摘要统计。"""
    effective_user_id = user_id if current_user.role == "admin" else current_user.id

    summary = await service.get_usage_summary(
        user_id=effective_user_id,
        agent_id=agent_id,
        start=start_date,
        end=end_date,
        period=period,
    )
    return UsageSummaryResponse(
        total_tokens=summary.total_tokens,
        total_cost=summary.total_cost,
        conversation_count=summary.conversation_count,
        record_count=summary.record_count,
        period=summary.period,
    )
