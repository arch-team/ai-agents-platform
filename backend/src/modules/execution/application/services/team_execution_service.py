"""团队执行服务。"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable

import structlog

from src.modules.execution.application.dto.team_execution_dto import (
    CreateTeamExecutionDTO,
    TeamExecutionDTO,
    TeamExecutionLogDTO,
)
from src.modules.execution.application.interfaces.agent_runtime import (
    AgentRequest,
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
from src.shared.application.ownership import check_ownership, get_or_raise
from src.shared.domain.event_bus import event_bus
from src.shared.domain.exceptions import DomainError
from src.shared.domain.interfaces.agent_querier import ActiveAgentInfo, IAgentQuerier


logger = structlog.get_logger(__name__)

# 团队执行终态集合 (stream_logs / cancel 判断用)
_TERMINAL_STATUSES = frozenset(
    {
        TeamExecutionStatus.COMPLETED,
        TeamExecutionStatus.FAILED,
        TeamExecutionStatus.CANCELLED,
    },
)


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
        max_concurrent: int = 3,
        memory_id: str = "",
        bg_repo_factory: Callable[
            [],
            tuple[
                ITeamExecutionRepository,
                ITeamExecutionLogRepository,
                Callable[[], Awaitable[None]],
                Callable[[], Awaitable[None]],
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
        self._memory_id = memory_id
        self._semaphore = asyncio.Semaphore(max_concurrent)
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
        agent_info = await self._agent_querier.get_executable_agent(dto.agent_id)
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

        if execution.status in _TERMINAL_STATUSES:
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
            if refreshed.status in _TERMINAL_STATUSES:
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
                execution_id,
                dto,
                user_id,
                agent_info,
                bg_exec_repo,
                bg_log_repo,
                bg_commit,
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
        commit_fn: Callable[[], Awaitable[None]] | None,
    ) -> None:
        """实际执行逻辑 — 编排入口，协调各子函数。"""
        async with self._semaphore:
            execution = await exec_repo.get_by_id(execution_id)
            if execution is None or execution.status == TeamExecutionStatus.CANCELLED:
                return

            # 更新状态为 RUNNING
            started = await self._update_execution_status(
                execution,
                execution_id,
                exec_repo,
                commit_fn,
            )
            if not started or execution.id is None:
                return

            await event_bus.publish_async(
                TeamExecutionStartedEvent(
                    execution_id=execution.id,
                    agent_id=dto.agent_id,
                    user_id=user_id,
                ),
            )

            # 带重试的流式执行
            request = self._build_team_agent_request(dto, agent_info)
            result, last_error, input_tokens, output_tokens = await self._execute_with_retry(
                execution_id,
                request,
                log_repo,
                commit_fn,
            )

            if last_error is None and result is not None:
                await self._complete_execution(
                    execution_id,
                    user_id,
                    result,
                    input_tokens,
                    output_tokens,
                    agent_info.model_id,
                    exec_repo,
                    commit_fn,
                )
            elif last_error is not None:
                await self._fail_execution(
                    execution_id,
                    user_id,
                    last_error,
                    exec_repo,
                    commit_fn,
                )

    async def _update_execution_status(
        self,
        execution: TeamExecution,
        execution_id: int,
        exec_repo: ITeamExecutionRepository,
        commit_fn: Callable[[], Awaitable[None]] | None,
    ) -> bool:
        """将执行状态更新为 RUNNING。返回 True 表示成功启动。"""
        try:
            execution.start()
            await exec_repo.update(execution)
            if commit_fn is not None:
                await commit_fn()
        except asyncio.CancelledError:
            logger.info("execution_cancelled_during_start", execution_id=execution_id)
            return False
        except DomainError as e:
            logger.exception("execution_start_domain_error", execution_id=execution_id, error_code=e.code)
            await self._mark_as_failed_safe(execution_id, e, exec_repo, commit_fn)
            return False
        except Exception as exc:
            logger.exception(
                "execution_start_unexpected_error",
                execution_id=execution_id,
                error_type=type(exc).__name__,
            )
            await self._mark_as_failed_safe(execution_id, exc, exec_repo, commit_fn)
            return False
        return True

    def _build_team_agent_request(self, dto: CreateTeamExecutionDTO, agent_info: ActiveAgentInfo) -> AgentRequest:
        """构建 AgentRequest。"""
        return AgentRequest(
            prompt=dto.prompt,
            system_prompt=agent_info.system_prompt,
            model_id=agent_info.model_id,
            temperature=agent_info.temperature,
            max_tokens=agent_info.max_tokens,
            gateway_url=self._gateway_url,
            max_turns=self._max_turns,
            enable_teams=True,
            memory_id=self._memory_id if agent_info.enable_memory else "",
        )

    async def _execute_with_retry(
        self,
        execution_id: int,
        request: AgentRequest,
        log_repo: ITeamExecutionLogRepository,
        commit_fn: Callable[[], Awaitable[None]] | None,
    ) -> tuple[str | None, Exception | None, int, int]:
        """带重试的流式执行。返回 (result, last_error, input_tokens, output_tokens)。"""
        max_retries = 2
        retry_delay = 2.0
        last_error: Exception | None = None
        sequence = 0
        input_tokens = 0
        output_tokens = 0
        content_parts: list[str] = []

        for attempt in range(max_retries + 1):
            try:
                seq, i_tok, o_tok, parts = await self._stream_team_execution(
                    execution_id,
                    request,
                    sequence,
                    log_repo,
                    commit_fn,
                )
                sequence = seq
                input_tokens += i_tok
                output_tokens += o_tok
                content_parts.extend(parts)
                return "".join(content_parts), None, input_tokens, output_tokens
            except asyncio.CancelledError:
                logger.info("execution_cancelled", execution_id=execution_id)
                return None, None, input_tokens, output_tokens
            except TimeoutError:
                logger.exception("execution_timeout", execution_id=execution_id, timeout=self._timeout_seconds)
                last_error = TimeoutError(f"执行超时 (超过 {self._timeout_seconds}s 限制)")
                break  # 超时不重试
            except DomainError as e:
                if e.code == "AGENT_SDK_ERROR" and attempt < max_retries:
                    logger.warning(
                        "agent_sdk_call_failed_retrying",
                        execution_id=execution_id,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                    )
                    last_error = e
                    await asyncio.sleep(retry_delay * (2**attempt))
                    content_parts.clear()
                    sequence = 0
                    input_tokens = 0
                    output_tokens = 0
                    continue
                logger.exception("execution_domain_error", execution_id=execution_id, error_code=e.code)
                last_error = e
                break
            except Exception as e:
                logger.exception("execution_unexpected_error", execution_id=execution_id, error_type=type(e).__name__)
                last_error = e
                break

        return None, last_error, input_tokens, output_tokens

    async def _stream_team_execution(
        self,
        execution_id: int,
        request: AgentRequest,
        start_sequence: int,
        log_repo: ITeamExecutionLogRepository,
        commit_fn: Callable[[], Awaitable[None]] | None,
    ) -> tuple[int, int, int, list[str]]:
        """流式执行并记录日志。返回 (sequence, input_tokens, output_tokens, content_parts)。"""
        sequence = start_sequence
        input_tokens = 0
        output_tokens = 0
        content_parts: list[str] = []

        stream = await self._agent_runtime.execute_stream(request)
        async with asyncio.timeout(self._timeout_seconds):
            async for chunk in stream:
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

        return sequence, input_tokens, output_tokens, content_parts

    async def _complete_execution(
        self,
        execution_id: int,
        user_id: int,
        result: str,
        input_tokens: int,
        output_tokens: int,
        model_id: str,
        exec_repo: ITeamExecutionRepository,
        commit_fn: Callable[[], Awaitable[None]] | None,
    ) -> None:
        """标记执行成功完成。"""
        execution = await exec_repo.get_by_id(execution_id)
        if execution is None or execution.status == TeamExecutionStatus.CANCELLED:
            return

        execution.complete(result=result, input_tokens=input_tokens, output_tokens=output_tokens)
        await exec_repo.update(execution)
        if commit_fn is not None:
            await commit_fn()

        await event_bus.publish_async(
            TeamExecutionCompletedEvent(
                execution_id=execution_id,
                user_id=user_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_id=model_id,
            ),
        )
        logger.info(
            "execution_completed",
            execution_id=execution_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        # Token 消耗告警
        total_tokens = input_tokens + output_tokens
        if total_tokens > 500_000:
            logger.warning(
                "execution_high_token_usage",
                execution_id=execution_id,
                total_tokens=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

    async def _fail_execution(
        self,
        execution_id: int,
        user_id: int,
        error: Exception,
        exec_repo: ITeamExecutionRepository,
        commit_fn: Callable[[], Awaitable[None]] | None,
    ) -> None:
        """标记执行失败并发布事件。"""
        error_msg = self._format_execution_error(error)
        execution = await exec_repo.get_by_id(execution_id)
        if execution is None or execution.status in _TERMINAL_STATUSES:
            return

        if execution.status == TeamExecutionStatus.PENDING:
            execution.start()
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

    async def _mark_as_failed_safe(
        self,
        execution_id: int,
        error: Exception,
        exec_repo: ITeamExecutionRepository,
        commit_fn: Callable[[], Awaitable[None]] | None,
    ) -> None:
        """安全网: 启动阶段失败时尝试将执行标记为 FAILED。"""
        try:
            execution = await exec_repo.get_by_id(execution_id)
            if execution is not None and execution.status not in _TERMINAL_STATUSES:
                error_msg = self._format_execution_error(error)
                if execution.status == TeamExecutionStatus.PENDING:
                    execution.start()
                execution.fail(error_msg)
                await exec_repo.update(execution)
                if commit_fn is not None:
                    await commit_fn()
        except Exception:
            logger.exception("mark_execution_failed_error", execution_id=execution_id)

    # ── 辅助方法 ──

    def _format_execution_error(self, error: Exception) -> str:
        """根据异常类型生成用户可见的错误消息。"""
        if isinstance(error, TimeoutError):
            return f"执行超时 (超过 {self._timeout_seconds}s 限制)"
        if isinstance(error, DomainError):
            return f"Agent SDK 调用失败: {error.message}"
        return "执行过程中发生内部错误"

    async def _get_execution_or_raise(self, execution_id: int) -> TeamExecution:
        return await get_or_raise(
            self._execution_repo,
            execution_id,
            TeamExecutionNotFoundError,
            execution_id,
        )

    @staticmethod
    def _check_ownership(execution: TeamExecution, user_id: int) -> None:
        check_ownership(execution, user_id, owner_field="user_id", error_code="FORBIDDEN_TEAM_EXECUTION")

    @staticmethod
    def _to_dto(execution: TeamExecution) -> TeamExecutionDTO:
        id_, created_at, updated_at = execution.require_persisted()
        return TeamExecutionDTO(
            id=id_,
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
            created_at=created_at,
            updated_at=updated_at,
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
