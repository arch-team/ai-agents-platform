"""全局测试配置和 Fixture。"""

import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """指定异步测试后端。"""
    return "asyncio"
