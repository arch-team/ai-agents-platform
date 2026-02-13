"""Insights API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class UsageRecordResponse(BaseModel):
    """使用记录响应。"""

    id: int
    user_id: int
    agent_id: int
    conversation_id: int | None
    model_id: str
    tokens_input: int
    tokens_output: int
    estimated_cost: float
    recorded_at: datetime
    created_at: datetime


class UsageRecordListResponse(BaseModel):
    """使用记录列表响应。"""

    items: list[UsageRecordResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UsageSummaryResponse(BaseModel):
    """使用量摘要响应。"""

    total_tokens: int
    total_cost: float
    conversation_count: int
    record_count: int
    period: str


# ── 新增: Insights 增强响应 ──


class DatePeriod(BaseModel):
    """时间范围。"""

    start_date: str
    end_date: str


class CostBreakdownItemResponse(BaseModel):
    """成本归因 — 单个 Agent 的 Token 消耗。"""

    agent_id: int
    agent_name: str
    total_tokens: int
    tokens_input: int
    tokens_output: int
    invocation_count: int


class CostBreakdownResponse(BaseModel):
    """成本归因响应 — 按 Agent 维度的 Token 消耗聚合。"""

    items: list[CostBreakdownItemResponse]
    total_tokens: int
    period: DatePeriod


class UsageTrendPointResponse(BaseModel):
    """使用趋势 — 单日数据点。"""

    date: str
    invocation_count: int
    total_tokens: int
    unique_users: int


class UsageTrendResponse(BaseModel):
    """使用趋势响应 — 按日维度的使用量聚合。"""

    data_points: list[UsageTrendPointResponse]
    period: DatePeriod


class InsightsSummaryResponse(BaseModel):
    """Insights 概览响应 — 组合多数据源的统计摘要。"""

    total_agents: int
    active_agents: int
    total_invocations: int
    total_cost: float
    total_tokens: int
    period: DatePeriod
