"""Agents API 请求模型。"""

from pydantic import BaseModel, Field


class CreateAgentRequest(BaseModel):
    """创建 Agent 请求。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500, default="")
    system_prompt: str = Field(max_length=10000, default="")
    model_id: str = Field(default="anthropic.claude-3-5-sonnet-20241022-v2:0", max_length=200)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2048, ge=1, le=4096)


class UpdateAgentRequest(BaseModel):
    """更新 Agent 请求。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    system_prompt: str | None = Field(default=None, max_length=10000)
    model_id: str | None = Field(default=None, max_length=200)
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(default=None, ge=1, le=4096)
