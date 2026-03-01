"""Insights API 端点。"""

from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.insights.api.dependencies import get_insights_service
from src.modules.insights.api.schemas.responses import (
    CostBreakdownItemResponse,
    CostBreakdownResponse,
    DatePeriod,
    InsightsSummaryResponse,
    UsageRecordListResponse,
    UsageRecordResponse,
    UsageSummaryResponse,
    UsageTrendPointResponse,
    UsageTrendResponse,
)
from src.modules.insights.application.dto.insights_dto import UsageRecordDTO
from src.modules.insights.application.services.insights_service import InsightsService
from src.shared.api.schemas import calc_total_pages


router = APIRouter(prefix="/api/v1/insights", tags=["insights"])

ServiceDep = Annotated[InsightsService, Depends(get_insights_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]

# 默认查询范围: 最近 30 天
_DEFAULT_RANGE_DAYS = 30


def _to_record_response(dto: UsageRecordDTO) -> UsageRecordResponse:
    return UsageRecordResponse(**asdict(dto))


def _effective_user_id(current_user: UserDTO, requested_user_id: int | None) -> int | None:
    """非 ADMIN 用户只能查看自己的数据。"""
    return requested_user_id if current_user.role == "admin" else current_user.id


def _parse_date_range(
    start_date: str | None,
    end_date: str | None,
) -> tuple[datetime, datetime]:
    """解析日期范围参数，默认最近 30 天。"""
    now = datetime.now(tz=UTC)
    end = datetime.fromisoformat(end_date).replace(tzinfo=UTC) if end_date else now
    start = (
        datetime.fromisoformat(start_date).replace(tzinfo=UTC)
        if start_date
        else end - timedelta(days=_DEFAULT_RANGE_DAYS)
    )
    return start, end


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
    paged = await service.list_usage_records(
        user_id=_effective_user_id(current_user, user_id),
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
    current_user: CurrentUserDep,
) -> UsageRecordResponse:
    """获取使用记录详情。"""
    dto = await service.get_usage_record(record_id)
    return _to_record_response(dto)


@router.get("/summary", response_model=InsightsSummaryResponse)
async def get_insights_summary(
    service: ServiceDep,
    current_user: CurrentUserDep,
    start_date: Annotated[str | None, Query()] = None,
    end_date: Annotated[str | None, Query()] = None,
) -> InsightsSummaryResponse:
    """获取 Insights 概览统计 — 组合 Cost Explorer + 自建 Token 追踪。"""
    start, end = _parse_date_range(start_date, end_date)
    summary = await service.get_insights_summary(start=start, end=end)
    return InsightsSummaryResponse(
        total_agents=summary.total_agents,
        active_agents=summary.active_agents,
        total_invocations=summary.total_invocations,
        total_cost=summary.total_cost,
        total_tokens=summary.total_tokens,
        period=DatePeriod(
            start_date=start.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
        ),
    )


@router.get("/cost-breakdown", response_model=CostBreakdownResponse)
async def get_cost_breakdown(
    service: ServiceDep,
    current_user: CurrentUserDep,
    start_date: Annotated[str | None, Query()] = None,
    end_date: Annotated[str | None, Query()] = None,
) -> CostBreakdownResponse:
    """获取按 Agent 维度的 Token 消耗归因。"""
    start, end = _parse_date_range(start_date, end_date)
    breakdowns = await service.get_cost_breakdown(start=start, end=end)
    items = [
        CostBreakdownItemResponse(
            agent_id=b.agent_id,
            agent_name=b.agent_name,
            total_tokens=b.total_tokens,
            tokens_input=b.tokens_input,
            tokens_output=b.tokens_output,
            invocation_count=b.invocation_count,
        )
        for b in breakdowns
    ]
    total_tokens = sum(b.total_tokens for b in breakdowns)
    return CostBreakdownResponse(
        items=items,
        total_tokens=total_tokens,
        period=DatePeriod(
            start_date=start.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
        ),
    )


@router.get("/usage-trends", response_model=UsageTrendResponse)
async def get_usage_trends(
    service: ServiceDep,
    current_user: CurrentUserDep,
    start_date: Annotated[str | None, Query()] = None,
    end_date: Annotated[str | None, Query()] = None,
) -> UsageTrendResponse:
    """获取按日维度的使用趋势。"""
    start, end = _parse_date_range(start_date, end_date)
    trends = await service.get_usage_trends(start=start, end=end)
    data_points = [
        UsageTrendPointResponse(
            date=t.date,
            invocation_count=t.invocation_count,
            total_tokens=t.total_tokens,
            unique_users=t.unique_users,
        )
        for t in trends
    ]
    return UsageTrendResponse(
        data_points=data_points,
        period=DatePeriod(
            start_date=start.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
        ),
    )


# 保留旧的 summary 端点向后兼容
@router.get("/usage-summary")
async def get_usage_summary(
    service: ServiceDep,
    current_user: CurrentUserDep,
    user_id: Annotated[int | None, Query()] = None,
    agent_id: Annotated[int | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    period: Annotated[str, Query()] = "all",
) -> UsageSummaryResponse:
    """获取使用量摘要统计 (旧接口，向后兼容)。"""
    summary = await service.get_usage_summary(
        user_id=_effective_user_id(current_user, user_id),
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
