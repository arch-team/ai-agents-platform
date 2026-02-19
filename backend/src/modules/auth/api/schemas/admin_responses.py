"""Admin API 响应模型。"""

from pydantic import BaseModel

from src.modules.auth.api.schemas.responses import UserResponse


class UserListResponse(BaseModel):
    """用户列表分页响应。"""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
