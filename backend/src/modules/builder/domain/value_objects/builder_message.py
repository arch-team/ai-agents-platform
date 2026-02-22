"""Builder 消息值对象。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BuilderMessage:
    """Builder 对话消息（不可变值对象）。"""

    role: str
    content: str
