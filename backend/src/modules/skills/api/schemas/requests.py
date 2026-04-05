"""Skills API 请求模型。"""

from pydantic import BaseModel, Field


class CreateSkillRequest(BaseModel):
    """创建 Skill 请求。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500, default="")
    category: str = Field(default="general", max_length=50)
    trigger_description: str = Field(max_length=500, default="")
    skill_md: str = Field(max_length=50000, default="")
    references: dict[str, str] | None = None


class UpdateSkillRequest(BaseModel):
    """更新 Skill 请求。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=50)
    trigger_description: str | None = Field(default=None, max_length=500)
    skill_md: str | None = Field(default=None, max_length=50000)
    references: dict[str, str] | None = None
