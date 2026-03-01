"""API 层通用 Schema。"""

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ErrorResponse(BaseModel):
    """统一错误响应格式。"""

    code: str
    message: str
    details: dict[str, str] | None = None


class PageRequest(BaseModel):
    """分页请求参数。"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PageResponse(BaseModel, Generic[T]):
    """分页响应封装。"""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


def calc_total_pages(total: int, page_size: int) -> int:
    """计算总页数。"""
    return math.ceil(total / page_size) if total else 0
