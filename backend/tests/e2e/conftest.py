"""E2E 测试配置 — 针对运行中的服务器执行真实 HTTP 请求。"""

import os
from collections.abc import Iterator

import httpx
import pytest


BASE_URL = os.getenv(
    "E2E_BASE_URL",
    "http://ai-agents-dev-546356512.us-east-1.elb.amazonaws.com",
)
ADMIN_EMAIL = os.getenv("E2E_ADMIN_EMAIL", "admin@company.com")
ADMIN_PASSWORD = os.getenv("E2E_ADMIN_PASSWORD", "Admin@2026!")

# 资源类型 → API 路径映射
_RESOURCE_ENDPOINTS: dict[str, str] = {
    "agent": "/api/v1/agents",
    "template": "/api/v1/templates",
    "tool": "/api/v1/tools",
    "knowledge_base": "/api/v1/knowledge-bases",
    "test_suite": "/api/v1/test-suites",
    "skill": "/api/v1/skills",
}


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def http() -> Iterator[httpx.Client]:
    """共享的 HTTP 客户端，带超时和 base_url。"""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def admin_token(http: httpx.Client) -> str:
    """Admin JWT token — 整个测试会话复用。"""
    resp = http.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"Admin 登录失败: {resp.text}"
    token: str = resp.json()["access_token"]
    return token


@pytest.fixture(scope="session")
def admin_headers(admin_token: str) -> dict[str, str]:
    """带 Bearer token 的请求头。"""
    return {"Authorization": f"Bearer {admin_token}"}


class ResourceTracker:
    """跟踪 E2E 测试创建的资源，会话结束时尽力清理。

    策略: 反向遍历（后创建先删除），对每个资源尝试 DELETE。
    - 204: 删除成功
    - 409: 状态不允许删除（如 archived Agent），记录警告后跳过
    - 其他: 记录警告后跳过
    清理失败不会中断流程，最终打印残留报告。
    """

    def __init__(self) -> None:
        self._created: list[tuple[str, int]] = []

    def track(self, resource_type: str, resource_id: int) -> None:
        """记录新创建的资源。resource_type 须匹配 _RESOURCE_ENDPOINTS 中的 key。"""
        self._created.append((resource_type, resource_id))

    def cleanup(self, http: httpx.Client, headers: dict[str, str]) -> None:
        """会话结束时清理资源。反向遍历，尽力删除，不中断。"""
        if not self._created:
            return

        orphans: list[str] = []

        # 反向: 后创建的先清理，避免外键依赖阻塞
        for resource_type, resource_id in reversed(self._created):
            endpoint = _RESOURCE_ENDPOINTS.get(resource_type)
            if endpoint is None:
                orphans.append(f"{resource_type}#{resource_id} (未知类型)")
                continue

            url = f"{endpoint}/{resource_id}"
            try:
                resp = http.delete(url, headers=headers)
                if resp.status_code == 204:
                    continue
                if resp.status_code == 404:
                    # 已被测试流程删除，正常
                    continue
                # 409 = 状态不允许删除，其他码也记录
                orphans.append(f"{resource_type}#{resource_id} (HTTP {resp.status_code})")
            except Exception as exc:
                orphans.append(f"{resource_type}#{resource_id} (异常: {exc})")

        if orphans:
            print(f"\n⚠️  E2E 残留资源 ({len(orphans)} 个，需手动处理):")
            for item in orphans:
                print(f"   - {item}")


@pytest.fixture(scope="session")
def resource_tracker(
    http: httpx.Client,
    admin_headers: dict[str, str],
) -> Iterator[ResourceTracker]:
    """全局资源追踪器 — yield 后自动执行清理。"""
    tracker = ResourceTracker()
    yield tracker
    tracker.cleanup(http, admin_headers)


def collect_sse_events(
    base_url: str,
    path: str,
    headers: dict[str, str],
    json_body: dict[str, object],
    timeout: float = 60.0,
) -> list[dict[str, object]]:
    """发送 POST 请求并收集 SSE data 行，解析为 JSON 列表。

    用于测试 Builder V2 的 /generate 和 /refine 端点。
    """
    import json

    events: list[dict[str, object]] = []
    url = f"{base_url}{path}"
    with httpx.stream(
        "POST",
        url,
        json=json_body,
        headers={**headers, "Accept": "text/event-stream"},
        timeout=timeout,
    ) as resp:
        assert resp.status_code == 200, f"SSE 请求失败: HTTP {resp.status_code}"
        for line in resp.iter_lines():
            if line.startswith("data: "):
                payload = line[6:]
                if payload.strip():
                    events.append(json.loads(payload))
    return events
