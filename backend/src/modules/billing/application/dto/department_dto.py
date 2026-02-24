"""Department DTO 定义。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateDepartmentDTO:
    """创建部门 DTO。"""

    name: str
    code: str
    description: str = ""


@dataclass
class UpdateDepartmentDTO:
    """更新部门 DTO。"""

    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


@dataclass
class DepartmentDTO:
    """部门 DTO (响应)。"""

    id: int
    name: str
    code: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
