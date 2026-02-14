"""A2A 跨 Runtime Agent 通信适配器。

SDK-First: 薄封装层，通过 AgentCore Runtime A2A API 实现跨 Runtime 的
Agent 消息传递。遵循 ADR-011 "有限采纳" 决策。

核心能力:
- tasks/send: 向目标 Agent 发送异步任务消息
- tasks/{id}: 查询 A2A 任务状态
"""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import structlog


logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class A2ATaskResult:
    """A2A 任务发送结果。"""

    task_id: str
    status: str  # submitted / working / completed / failed
    content: str = ""


@dataclass(frozen=True)
class A2ATaskStatus:
    """A2A 任务状态查询结果。"""

    task_id: str
    status: str
    content: str = ""
    error: str = ""


class A2AAdapter:
    """A2A 跨 Runtime Agent 通信适配器。

    通过 AgentCore Runtime A2A API 向目标 Agent 发送任务消息。
    未配置 gateway_url 时降级为 NoOp。
    """

    def __init__(self, *, gateway_url: str, region: str) -> None:
        self._gateway_url = gateway_url
        self._region = region

    @lru_cache(maxsize=1)  # noqa: B019
    def _get_client(self) -> Any:  # noqa: ANN401
        """获取 bedrock-agentcore 客户端 (懒加载单例)。"""
        import boto3

        return boto3.client("bedrock-agentcore", region_name=self._region)

    async def send_task(
        self,
        *,
        target_agent_url: str,
        message: str,
        session_id: str = "",
    ) -> A2ATaskResult:
        """向目标 Agent 发送 A2A 任务消息。

        返回任务 ID 和初始状态。未配置时返回空结果。
        """
        if not self._gateway_url:
            logger.debug("a2a_send_skip", reason="gateway_url 未配置")
            return A2ATaskResult(task_id="", status="skipped")

        try:
            client = self._get_client()
            payload: dict[str, Any] = {
                "jsonrpc": "2.0",
                "method": "tasks/send",
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [{"type": "text", "text": message}],
                    },
                },
            }
            if session_id:
                payload["params"]["sessionId"] = session_id

            response = await asyncio.to_thread(
                client.invoke_agent_runtime,
                agentRuntimeUrl=target_agent_url,
                payload=payload,
            )
        except Exception:
            logger.exception("a2a_send_failed", target=target_agent_url)
            return A2ATaskResult(task_id="", status="failed")

        result = response.get("result", {})
        return A2ATaskResult(
            task_id=result.get("id", ""),
            status=result.get("status", {}).get("state", "unknown"),
            content=self._extract_content(result),
        )

    async def get_task_status(self, task_id: str) -> A2ATaskStatus:
        """查询 A2A 任务状态。

        未配置时返回 skipped 状态。
        """
        if not self._gateway_url:
            return A2ATaskStatus(task_id=task_id, status="skipped")

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.get_agent_runtime_task,
                taskId=task_id,
            )
        except Exception:
            logger.exception("a2a_status_failed", task_id=task_id)
            return A2ATaskStatus(task_id=task_id, status="error", error="查询失败")

        result = response.get("result", {})
        status_obj = result.get("status", {})
        return A2ATaskStatus(
            task_id=task_id,
            status=status_obj.get("state", "unknown"),
            content=self._extract_content(result),
            error=status_obj.get("message", ""),
        )

    @staticmethod
    def _extract_content(result: dict[str, Any]) -> str:
        """从 A2A 响应中提取文本内容。"""
        artifacts = result.get("artifacts", [])
        if not artifacts:
            return ""
        parts = artifacts[0].get("parts", [])
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")
