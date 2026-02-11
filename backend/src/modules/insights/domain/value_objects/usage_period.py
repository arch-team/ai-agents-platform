"""使用周期枚举。"""

from enum import StrEnum


class UsagePeriod(StrEnum):
    """统计周期枚举 — 日/周/月。"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
