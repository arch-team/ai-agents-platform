"""团队执行服务。"""

import asyncio
from collections.abc import AsyncIterator, Callable

import structlog

from src.modules.execution.application.dto.team_execution_dto import (
    CreateTeamExecutionDTO,
    TeamExecutionDTO,
    TeamExecutionLogDTO,
)
from src.modules.execution.application.interfaces.agent_runtime import (
    AgentRequest,
    AgentResponseChunk,
    IAgentRuntime,
)
from src.modules.execution.domain.entities.team_execution import TeamExecution
from src.modules.execution.domain.entities.team_execution_log import TeamExecutionLog
from src.modules.execution.domain.events import (
    TeamExecutionCompletedEvent,
    TeamExecutionFailedEvent,
    TeamExecutionStartedEvent,
)
from src.modules.execution.domain.exceptions import (
    TeamExecutionNotCancellableError,
    TeamExecutionNotFoundError,
)
from src.modules.execution.domain.repositories.team_execution_repository import (
    ITeamExecutionLogRepository,
    ITeamExecutionRepository,
)
from src.modules.execution.domain.value_objects.team_execution_status import (
    TeamExecutionStatus,
)
from src.shared.application.dtos import PagedResult
from src.shared.domain.event_bus import event_bus
from src.shared.domain.exceptions import DomainError, ForbiddenError
from src.shared.domain.interfaces.agent_querier import ActiveAgentInfo, IAgentQuerier


logger = structlog.get_logger(__name__)

_SEMAPHORE_MAX_CONCURRENT = 3  # 最多同时运行的团队执行数量
_team_execution_semaphore = asyncio.Semaphore(_SEMAPHORE_MAX_CONCURRENT)


class TeamExecutionService:
    """团队执行服务，编排团队异步执行的完整生命周期。"""

    def __init__(
        self,
        *,
        execution_repo: ITeamExecutionRepository,
        log_repo: ITeamExecutionLogRepository,
        agent_runtime: IAgentRuntime,
        agent_querier: IAgentQuerier,
        gateway_url: str = "",
        max_turns: int = 200,
        timeout_seconds: int = 1800,
        bg_repo_factory: Callable[
            [],
            tuple[
                ITeamExecutionRepository,
                ITeamExecutionLogRepository,
                Callable[[], object],
                Callable[[], object],
            ],
        ]
        | None = None,
    ) -> None:
        self._execution_repo = execution_repo
        self._log_repo = log_repo
        self._agent_runtime = agent_runtime
        self._agent_querier = agent_querier
        self._gateway_url = gateway_url
        self._max_turns = max_turns
        self._timeout_seconds = timeout_seconds
        # 后台任务用独立 session 的 repo 工厂
        self._bg_repo_factory = bg_repo_factory
        # 后台任务追踪 (execution_id -> asyncio.Task)
        self._running_tasks: dict[int, asyncio.Task[None]] = {}

    async def submit(
        self,
        dto: CreateTeamExecutionDTO,
        user_id: int,
    ) -> TeamExecutionDTO:
        """提交团队执行任务。

        创建 TeamExecution(PENDING), 启动后台 asyncio.Task 执行。

        Raises:
            DomainError: Agent 不可用或未启用 Teams
        """
        # 校验 Agent 可用且启用 Teams
        agent_info = await self._agent_querier.get_active_agent(dto.agent_id)
        if agent_info is None:
            raise DomainError(
                message=f"Agent(id={dto.agent_id}) 不可用",
                code="AGENT_NOT_AVAILABLE",
            )
        if not agent_info.enable_teams:
            raise DomainError(
                message=f"Agent(id={dto.agent_id}) 未启用 Teams 能力",
                code="AGENT_TEAMS_NOT_ENABLED",
            )

        # 创建执行记录
        execution = TeamExecution(
            agent_id=dto.agent_id,
            user_id=user_id,
            conversation_id=dto.conversation_id,
            prompt=dto.prompt,
        )
        created = await self._execution_repo.create(execution)
        if created.id is None:
            msg = "TeamExecution 创建后 ID 不能为空"
            raise ValueError(msg)

        # 启动后台执行任务
        exec_id = created.id
        task = asyncio.create_task(
            self._execute_in_background(exec_id, dto, user_id, agent_info),
        )
        self._running_tasks[exec_id] = task
        # 任务完成后自动清理
        task.add_done_callback(lambda _t: self._running_tasks.pop(exec_id, None))

        return self._to_dto(created)

    async def get(self, execution_id: int, user_id: int) -> TeamExecutionDTO:
        """查询团队执行详情。"""
        execution = await self._get_execution_or_raise(execution_id)
        self._check_ownership(execution, user_id)
        return self._to_dto(execution)

    async def list_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[TeamExecutionDTO]:
        """分页列出用户的团队执行。"""
        offset = (page - 1) * page_size
        executions = await self._execution_repo.list_by_user(
            user_id=user_id,
            offset=offset,
            limit=page_size,
        )
        total = await self._execution_repo.count_by_user(user_id)
        return PagedResult(
            items=[self._to_dto(e) for e in executions],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def cancel(self, execution_id: int, user_id: int) -> TeamExecutionDTO:
        """取消团队执行。仅 PENDING/RUNNING 状态可取消。

        Raises:
            TeamExecutionNotFoundError, TeamExecutionNotCancellableError
        """
        execution = await self._get_execution_or_raise(execution_id)
        self._check_ownership(execution, user_id)

        if execution.status not in (
            TeamExecutionStatus.PENDING,
            TeamExecutionStatus.RUNNING,
        ):
            raise TeamExecutionNotCancellableError(execution_id)

        execution.cancel()
        updated = await self._execution_repo.update(execution)

        # 取消后台任务
        task = self._running_tasks.pop(execution_id, None)
        if task and not task.done():
            task.cancel()

        return self._to_dto(updated)

    async def get_logs(
        self,
        execution_id: int,
        user_id: int,
        after_sequence: int = 0,
    ) -> list[TeamExecutionLogDTO]:
        """获取执行日志。"""
        execution = await self._get_execution_or_raise(execution_id)
        self._check_ownership(execution, user_id)
        logs = await self._log_repo.list_by_execution(
            execution_id=execution_id,
            after_sequence=after_sequence,
        )
        return [self._to_log_dto(log) for log in logs]

    async def stream_logs(
        self,
        execution_id: int,
        user_id: int,
    ) -> AsyncIterator[TeamExecutionLogDTO]:
        """SSE 日志流。轮询日志表并 yield 新日志。"""
        execution = await self._get_execution_or_raise(execution_id)
        self._check_ownership(execution, user_id)

        last_sequence = 0
        while True:
            logs = await self._log_repo.list_by_execution(
                execution_id=execution_id,
                after_sequence=last_sequence,
            )
            for log in logs:
                last_sequence = log.sequence
                yield self._to_log_dto(log)

            # 检查执行是否已结束
            refreshed = await self._execution_repo.get_by_id(execution_id)
            if refreshed is None:
                break
            if refreshed.status in (
                TeamExecutionStatus.COMPLETED,
                TeamExecutionStatus.FAILED,
                TeamExecutionStatus.CANCELLED,
            ):
                # 最后一次读取确保不丢失日志
                final_logs = await self._log_repo.list_by_execution(
                    execution_id=execution_id,
                    after_sequence=last_sequence,
                )
                for log in final_logs:
                    yield self._to_log_dto(log)
                break

            await asyncio.sleep(1)

    # ── 后台执行逻辑 ──

    async def _execute_in_background(
        self,
        execution_id: int,
        dto: CreateTeamExecutionDTO,
        user_id: int,
        agent_info: ActiveAgentInfo,
    ) -> None:
        """后台执行团队任务。

        使用独立 DB session (通过 bg_repo_factory)，
        避免请求级 session 关闭后后台任务 DB 操作失败。
        """
        # 获取独立 session 的 repos
        if self._bg_repo_factory is not None:
            bg_exec_repo, bg_log_repo, bg_commit, bg_close = self._bg_repo_factory()
        else:
            bg_exec_repo = self._execution_repo
            bg_log_repo = self._log_repo
            bg_commit = None
            bg_close = None

        try:
            await self._do_execute(
                execution_id, dto, user_id, agent_info,
                bg_exec_repo, bg_log_repo, bg_commit,
            )
        finally:
            if bg_close is not None:
                await bg_close()

    async def _do_execute(
        self,
        execution_id: int,
        dto: CreateTeamExecutionDTO,
        user_id: int,
        agent_info: ActiveAgentInfo,
        exec_repo: ITeamExecutionRepository,
        log_repo: ITeamExecutionLogRepository,
        commit_fn: Callable[[], object] | None,
    ) -> None:
        """实际执行逻辑（使用传入的 repo）。"""
        async with _team_execution_semaphore:
            execution = await exec_repo.get_by_id(execution_id)
            if execution is None or execution.status == TeamExecutionStatus.CANCELLED:
                return

            # 更新状态为 RUNNING
            execution.start()
            await exec_repo.update(execution)
            if commit_fn is not None:
                await commit_fn()

            if execution.id is None:
                return

            await event_bus.publish_async(
                TeamExecutionStartedEvent(
                    execution_id=execution.id,
                    agent_id=dto.agent_id,
                    user_id=user_id,
                ),
            )

            sequence = 0
            input_tokens = 0
            output_tokens = 0
            content_parts: list[str] = []

            max_retries = 2
            retry_delay = 2.0
            last_error: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    # 构建 AgentRequest
                    request = AgentRequest(
                        prompt=dto.prompt,
                        system_prompt=agent_info.system_prompt,
                        model_id=agent_info.model_id,
                        temperature=agent_info.temperature,
                        max_tokens=agent_info.max_tokens,
                        gateway_url=self._gateway_url,
                        max_turns=self._max_turns,
                        enable_teams=True,
                    )

                    # 带超时的流式执行
                    async with asyncio.timeout(self._timeout_seconds):
                        async for chunk in self._consume_stream(request):
                            if chunk.content:
                                content_parts.append(chunk.content)
                                sequence += 1
                                log = TeamExecutionLog(
                                    execution_id=execution_id,
                                    sequence=sequence,
                                    log_type="content",
                                    content=chunk.content,
                                )
                                await log_repo.append_log(log)
                                if commit_fn is not None:
                                    await commit_fn()

                            input_tokens += chunk.input_tokens
                            output_tokens += chunk.output_tokens

                    # 执行完成
                    result = "".join(content_parts)
                    execution = await exec_repo.get_by_id(execution_id)
                    if execution is None:
                        return
                    if execution.status == TeamExecutionStatus.CANCELLED:
                        return

                    execution.complete(
                        result=result,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )
                    await exec_repo.update(execution)
                    if commit_fn is not None:
                        await commit_fn()

                    await event_bus.publish_async(
                        TeamExecutionCompletedEvent(
                            execution_id=execution_id,
                            user_id=user_id,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                        ),
                    )
                    logger.info(
                        "团队执行完成",
                        execution_id=execution_id,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )

                    # Token 消耗告警
                    total_tokens = input_tokens + output_tokens
                    if total_tokens > 500_000:
                        logger.warning(
                            "团队执行 Token 消耗较高",
                            execution_id=execution_id,
                            total_tokens=total_tokens,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                        )

                    return  # 成功则退出重试循环  # noqa: TRY300

                except asyncio.CancelledError:
                    logger.info("团队执行已取消", execution_id=execution_id)
                    return
                except TimeoutError:
                    logger.exception(
                        "团队执行超时",
                        execution_id=execution_id,
                        timeout=self._timeout_seconds,
                    )
                    last_error = TimeoutError(
                        f"执行超时 (超过 {self._timeout_seconds}s 限制)",
                    )
                    break  # 超时不重试
                except DomainError as e:
                    if e.code == "AGENT_SDK_ERROR" and attempt < max_retries:
                        logger.warning(
                            "Agent SDK 调用失败, 准备重试",
                            execution_id=execution_id,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                        )
                        last_error = e
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        # 重置累积状态
                        content_parts.clear()
                        sequence = 0
                        input_tokens = 0
                        output_tokens = 0
                        continue
                    logger.exception(
                        "团队执行 SDK 错误",
                        execution_id=execution_id,
                    )
                    last_error = e
                    break
                except Exception as e:
                    logger.exception("团队执行失败", execution_id=execution_id)
                    last_error = e
                    break

            # 重试耗尽或不可重试错误 - 标记为 FAILED
            if last_error is not None:
                if isinstance(last_error, TimeoutError):
                    error_msg = f"执行超时 (超过 {self._timeout_seconds}s 限制)"
                elif isinstance(last_error, DomainError):
                    error_msg = f"Agent SDK 调用失败: {last_error.message}"
                else:
                    error_msg = "执行过程中发生内部错误"

                execution = await exec_repo.get_by_id(execution_id)
                if execution is not None and execution.status == TeamExecutionStatus.RUNNING:
                    execution.fail(error_msg)
                    await exec_repo.update(execution)
                    if commit_fn is not None:
                        await commit_fn()

                    if execution.id is not None:
                        await event_bus.publish_async(
                            TeamExecutionFailedEvent(
                                execution_id=execution.id,
                                user_id=user_id,
                                error_message=error_msg,
                            ),
                        )

    async def _consume_stream(
        self,
        request: AgentRequest,
    ) -> AsyncIterator[AgentResponseChunk]:
        """消费 agent_runtime 流式响应。

        兼容 coroutine (async def) 和 async generator 两种返回类型。
        """
        result = self._agent_runtime.execute_stream(request)
        if hasattr(result, "__anext__"):
            stream = result
        else:
            stream = await result
        async for chunk in stream:
            yield chunk

    # ── 辅助方法 ──

    async def _get_execution_or_raise(self, execution_id: int) -> TeamExecution:
        execution = await self._execution_repo.get_by_id(execution_id)
        if execution is None:
            raise TeamExecutionNotFoundError(execution_id)
        return execution

    @staticmethod
    def _check_ownership(execution: TeamExecution, user_id: int) -> None:
        if execution.user_id != user_id:
            msg = "无权访问此团队执行"
            raise ForbiddenError(msg)

    @staticmethod
    def _to_dto(execution: TeamExecution) -> TeamExecutionDTO:
        if execution.id is None or execution.created_at is None or execution.updated_at is None:
            msg = "TeamExecution 缺少必要字段"
            raise ValueError(msg)
        return TeamExecutionDTO(
            id=execution.id,
            agent_id=execution.agent_id,
            user_id=execution.user_id,
            conversation_id=execution.conversation_id,
            prompt=execution.prompt,
            status=execution.status.value,
            result=execution.result,
            error_message=execution.error_message,
            input_tokens=execution.input_tokens,
            output_tokens=execution.output_tokens,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            created_at=execution.created_at,
            updated_at=execution.updated_at,
        )

    @staticmethod
    def _to_log_dto(log: TeamExecutionLog) -> TeamExecutionLogDTO:
        if log.id is None or log.created_at is None:
            msg = "TeamExecutionLog 缺少必要字段"
            raise ValueError(msg)
        return TeamExecutionLogDTO(
            id=log.id,
            execution_id=log.execution_id,
            sequence=log.sequence,
            log_type=log.log_type,
            content=log.content,
            created_at=log.created_at,
        )
