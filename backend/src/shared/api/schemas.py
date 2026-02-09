"""API layer common schemas."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Unified error response format."""

    code: str
    message: str
    details: dict[str, str] | None = None


class PageRequest(BaseModel):
    """Pagination request parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


class PageResponse(BaseModel, Generic[T]):
    """Pagination response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
