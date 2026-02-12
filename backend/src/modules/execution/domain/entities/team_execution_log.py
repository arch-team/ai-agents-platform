"""团队执行日志实体。"""

from pydantic import Field

from src.shared.domain.base_entity import PydanticEntity


class TeamExecutionLog(PydanticEntity):
    """团队执行日志实体，记录执行过程中的进度和输出。"""

    execution_id: int
    sequence: int = Field(default=0, ge=0)
    log_type: str = Field(max_length=20, default="progress")
    content: str = ""
