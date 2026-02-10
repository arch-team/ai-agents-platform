"""共享基础设施工具函数。"""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """获取当前 UTC 时间。"""
    return datetime.now(UTC)
