"""Builder API 请求模型。"""

from pydantic import BaseModel, Field


class TriggerBuilderRequest(BaseModel):
    """创建 Builder 会话请求。"""

    prompt: str = Field(min_length=1, max_length=2000, description="用户对 Agent 的描述")
    template_id: int | None = Field(default=None, description="模板 ID (从模板起步)")
    selected_skill_ids: list[int] = Field(default_factory=list, description="预选 Skill ID 列表")


class ConfirmBuilderRequest(BaseModel):
    """确认创建 Agent 请求。"""

    name_override: str | None = Field(default=None, max_length=200, description="覆盖 Agent 名称")
    auto_start_testing: bool = Field(default=False, description="V2: 创建后自动进入 TESTING 状态")


class RefineBuilderRequest(BaseModel):
    """多轮迭代请求。"""

    message: str = Field(min_length=1, max_length=2000, description="用户追加的修改需求")
