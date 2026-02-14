"""AI Agents Platform 性能压测脚本。

使用 locust 模拟 50 并发用户执行典型操作:
- 80% 读操作 (列表/详情查询)
- 15% 写操作 (创建/更新)
- 5% 认证操作 (登录/获取当前用户)

验收标准: P95 < 300ms (非 LLM 接口)

使用方式:
  # 无头模式 (50 并发, 5 分钟)
  locust -f locustfile.py --headless -u 50 -r 10 --run-time 5m --host http://localhost:8000

  # Web UI 模式
  locust -f locustfile.py --host http://localhost:8000
"""

import json
import logging
import os
import random
import string
import time
from typing import ClassVar

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner, WorkerRunner

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

# 测试用户凭据 (可通过环境变量覆盖)
TEST_USER_EMAIL = os.getenv("LOADTEST_USER_EMAIL", "loadtest@example.com")
TEST_USER_PASSWORD = os.getenv("LOADTEST_USER_PASSWORD", "LoadTest1234")
TEST_USER_NAME = os.getenv("LOADTEST_USER_NAME", "压测用户")

# P95 延迟阈值 (毫秒)
P95_THRESHOLD_MS = int(os.getenv("LOADTEST_P95_THRESHOLD_MS", "300"))

# 是否在启动前自动注册测试用户
AUTO_REGISTER = os.getenv("LOADTEST_AUTO_REGISTER", "true").lower() == "true"

logger = logging.getLogger("loadtest")


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def _random_string(length: int = 8) -> str:
    """生成随机字符串，用于创建唯一的测试数据。"""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _random_email() -> str:
    """生成随机邮箱地址。"""
    return f"loadtest-{_random_string(12)}@example.com"


def _random_password() -> str:
    """生成符合密码策略的随机密码 (含大写、小写、数字)。"""
    return f"Lt{_random_string(10)}1A"


# ---------------------------------------------------------------------------
# 性能指标收集钩子
# ---------------------------------------------------------------------------

# 存储每个端点的响应时间，用于最终报告
_response_times: dict[str, list[float]] = {}
_error_count: int = 0
_total_requests: int = 0


@events.request.add_listener
def on_request(
    request_type: str,
    name: str,
    response_time: float,
    response_length: int,
    exception: BaseException | None,
    **kwargs: object,
) -> None:
    """记录每个请求的性能指标。"""
    global _error_count, _total_requests  # noqa: PLW0603
    _total_requests += 1

    if name not in _response_times:
        _response_times[name] = []
    _response_times[name].append(response_time)

    if exception is not None:
        _error_count += 1


@events.quitting.add_listener
def on_quitting(environment: object, **kwargs: object) -> None:
    """测试结束时输出性能摘要报告。"""
    logger.info("=" * 70)
    logger.info("性能压测报告摘要")
    logger.info("=" * 70)

    all_times: list[float] = []
    for endpoint, times in sorted(_response_times.items()):
        if not times:
            continue
        times_sorted = sorted(times)
        count = len(times_sorted)
        p50 = times_sorted[int(count * 0.50)]
        p95 = times_sorted[int(count * 0.95)]
        p99 = times_sorted[int(count * 0.99)]
        avg = sum(times_sorted) / count
        status = "PASS" if p95 < P95_THRESHOLD_MS else "FAIL"
        all_times.extend(times_sorted)

        logger.info(
            "  [%s] %s  |  请求数: %d  |  P50: %.0fms  |  P95: %.0fms  |  P99: %.0fms  |  Avg: %.0fms",
            status,
            endpoint,
            count,
            p50,
            p95,
            p99,
            avg,
        )

    if all_times:
        all_sorted = sorted(all_times)
        total = len(all_sorted)
        overall_p95 = all_sorted[int(total * 0.95)]
        overall_p99 = all_sorted[int(total * 0.99)]
        error_rate = (_error_count / _total_requests * 100) if _total_requests > 0 else 0.0

        logger.info("-" * 70)
        logger.info("  总体 P95: %.0fms  |  P99: %.0fms  |  错误率: %.2f%%", overall_p95, overall_p99, error_rate)
        logger.info(
            "  总请求数: %d  |  错误数: %d  |  P95 阈值: %dms",
            _total_requests,
            _error_count,
            P95_THRESHOLD_MS,
        )

        overall_status = "PASS" if overall_p95 < P95_THRESHOLD_MS and error_rate < 1.0 else "FAIL"
        logger.info("  验收结果: %s", overall_status)
    logger.info("=" * 70)


# ---------------------------------------------------------------------------
# 用户行为模型
# ---------------------------------------------------------------------------


class PlatformUser(HttpUser):
    """模拟 AI Agents Platform 的典型用户行为。

    任务权重分配:
    - 读操作 (80%): Agent 列表、Agent 详情、对话列表、工具列表、模板列表等
    - 写操作 (15%): 创建 Agent、创建对话、更新 Agent
    - 认证操作 (5%): 获取当前用户信息
    """

    # 用户请求间隔: 1~3 秒 (模拟真实用户行为)
    wait_time = between(1, 3)

    # 存储测试过程中创建的资源 ID，供后续操作使用
    _agent_ids: ClassVar[list[int]] = []
    _conversation_ids: ClassVar[list[int]] = []

    def on_start(self) -> None:
        """用户启动时执行: 登录获取 JWT Token。"""
        self._login()

    def _login(self) -> None:
        """登录并存储 JWT Token。"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
            name="/api/v1/auth/login",
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            logger.warning(
                "登录失败 (status=%d)，尝试注册新用户...",
                response.status_code,
            )
            self._register_and_login()

    def _register_and_login(self) -> None:
        """注册新用户后登录 (当预置用户不可用时的降级策略)。"""
        email = _random_email()
        password = _random_password()

        reg_response = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "name": f"压测用户-{_random_string(4)}"},
            name="/api/v1/auth/register (fallback)",
        )
        if reg_response.status_code != 201:
            logger.error("注册失败 (status=%d): %s", reg_response.status_code, reg_response.text)
            return

        login_response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            name="/api/v1/auth/login (fallback)",
        )
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            logger.error("降级登录失败 (status=%d)", login_response.status_code)

    # -----------------------------------------------------------------------
    # 读操作 (80%)
    # -----------------------------------------------------------------------

    @task(20)
    def list_agents(self) -> None:
        """获取 Agent 列表 (分页)。"""
        page = random.randint(1, 3)
        self.client.get(
            f"/api/v1/agents?page={page}&page_size=20",
            name="/api/v1/agents [GET list]",
        )

    @task(15)
    def get_agent_detail(self) -> None:
        """获取 Agent 详情。"""
        if not self._agent_ids:
            # 先获取列表，收集 ID
            self._collect_agent_ids()
            return
        agent_id = random.choice(self._agent_ids)
        self.client.get(
            f"/api/v1/agents/{agent_id}",
            name="/api/v1/agents/{id} [GET detail]",
        )

    @task(15)
    def list_conversations(self) -> None:
        """获取对话列表。"""
        self.client.get(
            "/api/v1/conversations?page=1&page_size=20",
            name="/api/v1/conversations [GET list]",
        )

    @task(8)
    def get_conversation_detail(self) -> None:
        """获取对话详情。"""
        if not self._conversation_ids:
            return
        conv_id = random.choice(self._conversation_ids)
        self.client.get(
            f"/api/v1/conversations/{conv_id}",
            name="/api/v1/conversations/{id} [GET detail]",
        )

    @task(8)
    def list_tools(self) -> None:
        """获取工具列表。"""
        self.client.get(
            "/api/v1/tools?page=1&page_size=20",
            name="/api/v1/tools [GET list]",
        )

    @task(5)
    def list_knowledge_bases(self) -> None:
        """获取知识库列表。"""
        self.client.get(
            "/api/v1/knowledge-bases?page=1&page_size=20",
            name="/api/v1/knowledge-bases [GET list]",
        )

    @task(5)
    def list_templates(self) -> None:
        """获取模板列表。"""
        self.client.get(
            "/api/v1/templates?page=1&page_size=20",
            name="/api/v1/templates [GET list]",
        )

    @task(4)
    def get_insights_summary(self) -> None:
        """获取洞察摘要。"""
        self.client.get(
            "/api/v1/insights/summary",
            name="/api/v1/insights/summary [GET]",
        )

    # -----------------------------------------------------------------------
    # 写操作 (15%)
    # -----------------------------------------------------------------------

    @task(6)
    def create_agent(self) -> None:
        """创建 Agent。"""
        payload = {
            "name": f"压测Agent-{_random_string(6)}",
            "description": f"性能测试创建的 Agent ({_random_string(10)})",
            "system_prompt": "你是一个有用的助手。",
            "model_id": "anthropic.claude-sonnet-4-20250514",
            "temperature": round(random.uniform(0.0, 1.0), 2),
            "max_tokens": random.choice([1024, 2048, 4096]),
        }
        response = self.client.post(
            "/api/v1/agents",
            json=payload,
            name="/api/v1/agents [POST create]",
        )
        if response.status_code == 201:
            data = response.json()
            agent_id = data.get("id")
            if agent_id:
                self._agent_ids.append(agent_id)

    @task(5)
    def create_conversation(self) -> None:
        """创建对话。"""
        if not self._agent_ids:
            return
        agent_id = random.choice(self._agent_ids)
        payload = {
            "agent_id": agent_id,
            "title": f"压测对话-{_random_string(6)}",
        }
        response = self.client.post(
            "/api/v1/conversations",
            json=payload,
            name="/api/v1/conversations [POST create]",
        )
        if response.status_code == 201:
            data = response.json()
            conv_id = data.get("id")
            if conv_id:
                self._conversation_ids.append(conv_id)

    @task(4)
    def update_agent(self) -> None:
        """更新 Agent。"""
        if not self._agent_ids:
            return
        agent_id = random.choice(self._agent_ids)
        payload = {
            "name": f"压测Agent-已更新-{_random_string(4)}",
            "description": f"压测期间更新 ({_random_string(8)})",
        }
        self.client.put(
            f"/api/v1/agents/{agent_id}",
            json=payload,
            name="/api/v1/agents/{id} [PUT update]",
        )

    # -----------------------------------------------------------------------
    # 认证操作 (5%)
    # -----------------------------------------------------------------------

    @task(5)
    def get_current_user(self) -> None:
        """获取当前用户信息。"""
        self.client.get(
            "/api/v1/auth/me",
            name="/api/v1/auth/me [GET]",
        )

    # -----------------------------------------------------------------------
    # 辅助方法
    # -----------------------------------------------------------------------

    def _collect_agent_ids(self) -> None:
        """从 Agent 列表中收集 ID，供详情查询使用。"""
        response = self.client.get(
            "/api/v1/agents?page=1&page_size=50",
            name="/api/v1/agents [GET list] (collect)",
        )
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            for item in items:
                agent_id = item.get("id")
                if agent_id and agent_id not in self._agent_ids:
                    self._agent_ids.append(agent_id)


# ---------------------------------------------------------------------------
# 测试环境初始化 (仅 Master / 单机模式)
# ---------------------------------------------------------------------------


@events.test_start.add_listener
def on_test_start(environment: object, **kwargs: object) -> None:
    """测试开始前的环境准备。"""
    runner = getattr(environment, "runner", None)

    # Worker 模式下跳过初始化
    if isinstance(runner, WorkerRunner):
        return

    logger.info("=" * 70)
    logger.info("AI Agents Platform 性能压测")
    logger.info("  目标: P95 < %dms (非 LLM 接口)", P95_THRESHOLD_MS)
    logger.info("  测试用户: %s", TEST_USER_EMAIL)
    logger.info("  自动注册: %s", AUTO_REGISTER)
    logger.info("=" * 70)
