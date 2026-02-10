"""共享基础设施工具函数 -- utc_now 由 Domain 层定义, 此处重导出供 Infrastructure 层使用。"""

from src.shared.domain.base_entity import utc_now


__all__ = ["utc_now"]
