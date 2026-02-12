"""团队执行 DTO。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateTeamExecutionDTO:
    """创建团队执行请求数据。"""

    agent_id: int
    prompt: str
    conversation_id: int | None = None


@dataclass
class TeamExecutionDTO:
    """团队执行响应数据。"""

    id: int
    agent_id: int
    user_id: int
    conversation_id: int | None
    prompt: str
    status: str
    result: str
    error_message: str
    input_tokens: int
    output_tokens: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass
class TeamExecutionLogDTO:
    """团队执行日志数据。"""

    id: int
    execution_id: int
    sequence: int
    log_type: str
    content: str
    created_at: datetime
