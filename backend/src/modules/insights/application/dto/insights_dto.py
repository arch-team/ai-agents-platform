"""Insights 相关 DTO。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateUsageRecordDTO:
    """创建使用记录请求数据。"""

    user_id: int
    agent_id: int
    model_id: str
    tokens_input: int
    tokens_output: int
    conversation_id: int | None = None


@dataclass
class UsageRecordDTO:
    """使用记录响应数据。"""

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


@dataclass
class UsageSummaryDTO:
    """使用量摘要数据。"""

    total_tokens: int
    total_cost: float
    conversation_count: int
    record_count: int
    period: str


@dataclass
class InsightsSummaryDTO:
    """Insights 概览摘要数据。"""

    total_agents: int
    active_agents: int
    total_invocations: int
    total_cost: float
    total_tokens: int
