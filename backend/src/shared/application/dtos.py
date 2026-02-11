"""共享 DTO 定义。"""

from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass
class PagedResult(Generic[T]):
    """泛型分页结果，替代各模块的 PagedXxxDTO。"""

    items: list[T]
    total: int
    page: int
    page_size: int
