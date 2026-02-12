"""Insights 相关 DTO。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateUsageRecordDTO:
    """创建使用记录请求数据。"""

    user_id: int
    agent_id: int
    conversation_id: int
    model_id: str
    tokens_input: int
    tokens_output: int


@dataclass
class UsageRecordDTO:
    """使用记录响应数据。"""

    id: int
    user_id: int
    agent_id: int
    conversation_id: int
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
class UsageTrendDTO:
    """使用趋势数据 (时间序列)。"""

    date: str
    metric_name: str
    metric_value: float


@dataclass
class AgentStatsDTO:
    """Agent 维度统计数据。"""

    agent_id: int
    total_conversations: int
    total_tokens: int
    total_cost: float


@dataclass
class UserStatsDTO:
    """用户维度统计数据。"""

    user_id: int
    total_conversations: int
    total_tokens: int
    total_cost: float
