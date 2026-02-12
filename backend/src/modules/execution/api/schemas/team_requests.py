"""团队执行 API 请求模型。"""

from pydantic import BaseModel, Field


class CreateTeamExecutionRequest(BaseModel):
    """创建团队执行请求。"""

    agent_id: int
    prompt: str = Field(min_length=1, max_length=100000)
    conversation_id: int | None = None
