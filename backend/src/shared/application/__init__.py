"""共享应用层组件。"""

from src.shared.application.dtos import PagedResult
from src.shared.application.ownership import check_ownership, get_or_raise


__all__ = ["PagedResult", "check_ownership", "get_or_raise"]
