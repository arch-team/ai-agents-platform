"""模板配置值对象。"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TemplateConfig:
    """模板配置，聚合 Agent 配置 + 工具 + 知识库的完整定义。"""

    system_prompt: str
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 4096
    tool_ids: list[int] = field(default_factory=list)
    knowledge_base_ids: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        """验证字段约束。"""
        if not self.system_prompt:
            msg = "system_prompt 不能为空"
            raise ValueError(msg)
        if not self.model_id:
            msg = "model_id 不能为空"
            raise ValueError(msg)
        if not 0.0 <= self.temperature <= 1.0:
            msg = "temperature 必须在 0.0 到 1.0 之间"
            raise ValueError(msg)
        if self.max_tokens < 1:
            msg = "max_tokens 必须大于 0"
            raise ValueError(msg)
