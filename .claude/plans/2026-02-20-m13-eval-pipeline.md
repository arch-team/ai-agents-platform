# M13：自动化评估 Pipeline 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 扩展 `evaluation` 模块，新增 `EvalPipeline` 实体和 `BedrockEvalAdapter`，实现自动化 Eval Pipeline（定时触发 + 模型对比 + Bedrock Model Evaluation API 集成）。

**Architecture:** 在现有 `evaluation` 模块的四层结构上追加 Pipeline 能力，不破坏 TestSuite/TestCase/EvaluationRun 现有代码。`BedrockEvalAdapter` 封装 boto3 `bedrock` 客户端 Evaluation Job API（< 100 行），通过 `IEvalService` 接口注入 `EvalPipelineService`。基础设施侧新增 CDK EventBridge 规则触发定时回归。

**Tech Stack:** Python 3.11+ | FastAPI | SQLAlchemy 2.0 async | Pydantic v2 | boto3 bedrock | uv | pytest

---

## 读前必看：项目规范速查

- **运行测试**: `uv run pytest tests/path/test.py::TestClass::test_method -v`（必须用 `uv run`，不是 `pytest`）
- **质量检查**: `uv run ruff check src/ && uv run mypy src/`
- **实体基类**: 继承 `PydanticEntity`，自动有 `id/created_at/updated_at`，调用 `self.touch()` 更新时间戳
- **枚举模式**: 使用 `StrEnum`（见 `EvaluationRunStatus`）
- **仓储模式**: 接口在 `domain/repositories/`，实现在 `infrastructure/persistence/repositories/`
- **Mock 模式**: `AsyncMock(spec=IXxxRepository)` + `patch` event_bus
- **目录约定**: 测试在 `tests/modules/evaluation/`，镜像 `src/` 结构

---

## Task 1：`PipelineStatus` 枚举

**Files:**
- Create: `backend/src/modules/evaluation/domain/value_objects/pipeline_status.py`
- Test: `backend/tests/modules/evaluation/unit/domain/test_pipeline_status.py`

**Step 1: 新建测试文件**

```python
# tests/modules/evaluation/unit/domain/test_pipeline_status.py
import pytest
from src.modules.evaluation.domain.value_objects.pipeline_status import PipelineStatus


class TestPipelineStatus:
    def test_all_statuses_are_strings(self) -> None:
        for status in PipelineStatus:
            assert isinstance(status.value, str)

    def test_scheduled_is_initial_status(self) -> None:
        assert PipelineStatus.SCHEDULED.value == "scheduled"

    def test_status_values(self) -> None:
        assert PipelineStatus.SCHEDULED == "scheduled"
        assert PipelineStatus.RUNNING == "running"
        assert PipelineStatus.COMPLETED == "completed"
        assert PipelineStatus.FAILED == "failed"
```

**Step 2: 运行测试确认失败**

```bash
cd backend && uv run pytest tests/modules/evaluation/unit/domain/test_pipeline_status.py -v
```
预期: `FAILED` — `ModuleNotFoundError: pipeline_status`

**Step 3: 创建实现**

```python
# src/modules/evaluation/domain/value_objects/pipeline_status.py
"""Eval Pipeline 状态枚举。"""
from enum import StrEnum


class PipelineStatus(StrEnum):
    """Pipeline 状态: SCHEDULED -> RUNNING -> COMPLETED / FAILED。"""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

**Step 4: 运行测试确认通过**

```bash
uv run pytest tests/modules/evaluation/unit/domain/test_pipeline_status.py -v
```
预期: `3 passed`

**Step 5: 提交**

```bash
git add src/modules/evaluation/domain/value_objects/pipeline_status.py \
        tests/modules/evaluation/unit/domain/test_pipeline_status.py
git commit -m "feat(evaluation): 新增 PipelineStatus 枚举"
```

---

## Task 2：`EvalPipeline` 领域实体

**Files:**
- Create: `backend/src/modules/evaluation/domain/entities/eval_pipeline.py`
- Test: `backend/tests/modules/evaluation/unit/domain/test_eval_pipeline_entity.py`

**Step 1: 新建测试文件**

```python
# tests/modules/evaluation/unit/domain/test_eval_pipeline_entity.py
import pytest
from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.modules.evaluation.domain.value_objects.pipeline_status import PipelineStatus
from src.shared.domain.exceptions import InvalidStateTransitionError


def make_pipeline(*, suite_id: int = 1, agent_id: int = 1,
                  trigger: str = "manual", model_ids: list[str] | None = None) -> EvalPipeline:
    return EvalPipeline(
        suite_id=suite_id,
        agent_id=agent_id,
        trigger=trigger,
        model_ids=model_ids or ["us.anthropic.claude-haiku-4-20250514-v1:0"],
    )


class TestEvalPipelineEntity:
    def test_default_status_is_scheduled(self) -> None:
        pipeline = make_pipeline()
        assert pipeline.status == PipelineStatus.SCHEDULED

    def test_start_transitions_scheduled_to_running(self) -> None:
        pipeline = make_pipeline()
        pipeline.start()
        assert pipeline.status == PipelineStatus.RUNNING
        assert pipeline.started_at is not None

    def test_start_fails_if_not_scheduled(self) -> None:
        pipeline = make_pipeline()
        pipeline.start()
        with pytest.raises(InvalidStateTransitionError):
            pipeline.start()

    def test_complete_transitions_running_to_completed(self) -> None:
        pipeline = make_pipeline()
        pipeline.start()
        pipeline.complete(bedrock_job_id="job-123", score_summary={"accuracy": 0.9})
        assert pipeline.status == PipelineStatus.COMPLETED
        assert pipeline.bedrock_job_id == "job-123"
        assert pipeline.score_summary == {"accuracy": 0.9}

    def test_complete_fails_if_not_running(self) -> None:
        pipeline = make_pipeline()
        with pytest.raises(InvalidStateTransitionError):
            pipeline.complete(bedrock_job_id="job-x", score_summary={})

    def test_fail_transitions_running_to_failed(self) -> None:
        pipeline = make_pipeline()
        pipeline.start()
        pipeline.fail(error="timeout")
        assert pipeline.status == PipelineStatus.FAILED
        assert pipeline.error_message == "timeout"

    def test_model_ids_required(self) -> None:
        with pytest.raises(ValueError):
            EvalPipeline(suite_id=1, agent_id=1, trigger="manual", model_ids=[])
```

**Step 2: 运行测试确认失败**

```bash
uv run pytest tests/modules/evaluation/unit/domain/test_eval_pipeline_entity.py -v
```
预期: `FAILED` — `ModuleNotFoundError: eval_pipeline`

**Step 3: 创建实现**

```python
# src/modules/evaluation/domain/entities/eval_pipeline.py
"""Eval Pipeline 领域实体。"""
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from src.modules.evaluation.domain.value_objects.pipeline_status import PipelineStatus
from src.shared.domain.base_entity import PydanticEntity, utc_now
from src.shared.domain.exceptions import InvalidStateTransitionError


class EvalPipeline(PydanticEntity):
    """Eval Pipeline 实体，代表一次完整的自动化评估任务。"""

    suite_id: int
    agent_id: int
    trigger: str = Field(max_length=50)  # "manual" | "scheduled" | "push"
    model_ids: list[str] = Field(min_length=1)
    status: PipelineStatus = PipelineStatus.SCHEDULED
    bedrock_job_id: str | None = None
    score_summary: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("model_ids")
    @classmethod
    def validate_model_ids(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("model_ids 不能为空")
        return v

    def start(self) -> None:
        """SCHEDULED -> RUNNING。"""
        self._require_status(self.status, PipelineStatus.SCHEDULED, PipelineStatus.RUNNING.value)
        self.status = PipelineStatus.RUNNING
        self.started_at = utc_now()
        self.touch()

    def complete(self, *, bedrock_job_id: str, score_summary: dict[str, Any]) -> None:
        """RUNNING -> COMPLETED。"""
        self._require_status(self.status, PipelineStatus.RUNNING, PipelineStatus.COMPLETED.value)
        self.status = PipelineStatus.COMPLETED
        self.bedrock_job_id = bedrock_job_id
        self.score_summary = score_summary
        self.completed_at = utc_now()
        self.touch()

    def fail(self, *, error: str) -> None:
        """RUNNING -> FAILED。"""
        self._require_status(self.status, PipelineStatus.RUNNING, PipelineStatus.FAILED.value)
        self.status = PipelineStatus.FAILED
        self.error_message = error
        self.completed_at = utc_now()
        self.touch()
```

**Step 4: 运行测试确认通过**

```bash
uv run pytest tests/modules/evaluation/unit/domain/test_eval_pipeline_entity.py -v
```
预期: `7 passed`

**Step 5: 提交**

```bash
git add src/modules/evaluation/domain/entities/eval_pipeline.py \
        tests/modules/evaluation/unit/domain/test_eval_pipeline_entity.py
git commit -m "feat(evaluation): 新增 EvalPipeline 实体 + 状态机"
```

---

## Task 3：`IEvalPipelineRepository` 接口 + 领域异常

**Files:**
- Create: `backend/src/modules/evaluation/domain/repositories/eval_pipeline_repository.py`
- Modify: `backend/src/modules/evaluation/domain/exceptions.py`

**Step 1: 查看现有 exceptions.py 末尾**

```bash
tail -10 backend/src/modules/evaluation/domain/exceptions.py
```

**Step 2: 追加异常类**

在 `exceptions.py` 末尾追加（不删除现有内容）：

```python
class EvalPipelineNotFoundError(EntityNotFoundError):
    """Eval Pipeline 不存在。"""
    def __init__(self, pipeline_id: int) -> None:
        super().__init__(f"EvalPipeline {pipeline_id} 不存在")


class PipelineAlreadyRunningError(DomainError):
    """Pipeline 已在运行中，不能重复触发。"""
    def __init__(self) -> None:
        super().__init__("该 Pipeline 已在运行中，请等待完成后再触发")
```

**Step 3: 创建仓储接口**

```python
# src/modules/evaluation/domain/repositories/eval_pipeline_repository.py
"""Eval Pipeline 仓储接口。"""
from abc import abstractmethod

from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.shared.domain.interfaces import IRepository


class IEvalPipelineRepository(IRepository[EvalPipeline, int]):
    """Eval Pipeline 仓储接口。"""

    @abstractmethod
    async def list_by_suite(self, suite_id: int, limit: int = 20) -> list[EvalPipeline]:
        """查询指定 TestSuite 的最近 Pipeline 列表。"""
        ...

    @abstractmethod
    async def find_running_by_suite(self, suite_id: int) -> EvalPipeline | None:
        """查询正在运行的 Pipeline（用于防止重复触发）。"""
        ...
```

**Step 4: 运行 ruff 确认无错误**

```bash
cd backend && uv run ruff check src/modules/evaluation/domain/ --fix
```
预期: 无错误输出

**Step 5: 提交**

```bash
git add src/modules/evaluation/domain/repositories/eval_pipeline_repository.py \
        src/modules/evaluation/domain/exceptions.py
git commit -m "feat(evaluation): 新增 IEvalPipelineRepository 接口 + Pipeline 异常"
```

---

## Task 4：`IEvalService` 外部服务接口

**Files:**
- Create: `backend/src/modules/evaluation/application/interfaces/eval_service.py`

**Step 1: 检查 application/interfaces 目录是否存在**

```bash
ls backend/src/modules/evaluation/application/
```

如果 `interfaces/` 不存在，创建它：

```bash
mkdir -p backend/src/modules/evaluation/application/interfaces
touch backend/src/modules/evaluation/application/interfaces/__init__.py
```

**Step 2: 创建接口**

```python
# src/modules/evaluation/application/interfaces/eval_service.py
"""Bedrock Evaluation 外部服务接口。"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class EvalJobResult:
    """Bedrock Evaluation Job 结果。"""
    job_id: str
    status: str  # "Completed" | "Failed" | "InProgress"
    score_summary: dict[str, Any]


class IEvalService(ABC):
    """Bedrock Model Evaluation 服务接口（封装层 < 100 行）。"""

    @abstractmethod
    async def create_eval_job(self, suite_name: str, model_ids: list[str],
                              test_cases: list[dict[str, str]]) -> str:
        """创建 Bedrock Evaluation Job，返回 job_id。"""
        ...

    @abstractmethod
    async def get_eval_job_result(self, job_id: str) -> EvalJobResult:
        """查询 Evaluation Job 结果。"""
        ...
```

**Step 3: 运行 ruff + mypy**

```bash
cd backend && uv run ruff check src/modules/evaluation/application/interfaces/ && uv run mypy src/modules/evaluation/application/interfaces/
```
预期: 无错误

**Step 4: 提交**

```bash
git add src/modules/evaluation/application/interfaces/
git commit -m "feat(evaluation): 新增 IEvalService 外部服务接口"
```

---

## Task 5：`EvalPipelineService` 应用服务

**Files:**
- Create: `backend/src/modules/evaluation/application/services/eval_pipeline_service.py`
- Create: `backend/src/modules/evaluation/application/dto/pipeline_dto.py`
- Test: `backend/tests/modules/evaluation/unit/application/test_eval_pipeline_service.py`

**Step 1: 创建 DTO**

```python
# src/modules/evaluation/application/dto/pipeline_dto.py
"""Eval Pipeline DTO。"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TriggerPipelineDTO:
    suite_id: int
    agent_id: int
    model_ids: list[str] = field(default_factory=lambda: ["us.anthropic.claude-haiku-4-20250514-v1:0"])
    trigger: str = "manual"


@dataclass
class EvalPipelineDTO:
    id: int
    suite_id: int
    agent_id: int
    trigger: str
    model_ids: list[str]
    status: str
    bedrock_job_id: str | None
    score_summary: dict[str, Any]
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
```

**Step 2: 新建测试文件**

```python
# tests/modules/evaluation/unit/application/test_eval_pipeline_service.py
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.modules.evaluation.application.dto.pipeline_dto import TriggerPipelineDTO, EvalPipelineDTO
from src.modules.evaluation.application.interfaces.eval_service import IEvalService, EvalJobResult
from src.modules.evaluation.application.services.eval_pipeline_service import EvalPipelineService
from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.modules.evaluation.domain.repositories.eval_pipeline_repository import IEvalPipelineRepository
from src.modules.evaluation.domain.repositories.test_suite_repository import ITestSuiteRepository
from src.modules.evaluation.domain.repositories.test_case_repository import ITestCaseRepository
from src.modules.evaluation.domain.value_objects.pipeline_status import PipelineStatus


def make_pipeline_entity(*, pipeline_id: int = 1) -> EvalPipeline:
    return EvalPipeline(
        id=pipeline_id, suite_id=1, agent_id=1, trigger="manual",
        model_ids=["us.anthropic.claude-haiku-4-20250514-v1:0"],
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )


@pytest.fixture
def mock_pipeline_repo() -> AsyncMock:
    return AsyncMock(spec=IEvalPipelineRepository)


@pytest.fixture
def mock_suite_repo() -> AsyncMock:
    return AsyncMock(spec=ITestSuiteRepository)


@pytest.fixture
def mock_case_repo() -> AsyncMock:
    return AsyncMock(spec=ITestCaseRepository)


@pytest.fixture
def mock_eval_service() -> AsyncMock:
    return AsyncMock(spec=IEvalService)


@pytest.fixture
def service(mock_pipeline_repo, mock_suite_repo, mock_case_repo, mock_eval_service) -> EvalPipelineService:
    return EvalPipelineService(
        pipeline_repo=mock_pipeline_repo,
        suite_repo=mock_suite_repo,
        case_repo=mock_case_repo,
        eval_service=mock_eval_service,
    )


class TestEvalPipelineServiceTrigger:
    @pytest.mark.asyncio
    async def test_trigger_creates_pipeline(self, service, mock_pipeline_repo, mock_suite_repo,
                                            mock_case_repo, mock_eval_service) -> None:
        # Arrange
        from tests.modules.evaluation.conftest import make_test_suite, make_test_case
        mock_suite_repo.get.return_value = make_test_suite(suite_id=1)
        mock_case_repo.list_by_suite.return_value = [make_test_case()]
        mock_eval_service.create_eval_job.return_value = "bedrock-job-001"
        saved_pipeline = make_pipeline_entity()
        mock_pipeline_repo.save.return_value = saved_pipeline
        mock_pipeline_repo.find_running_by_suite.return_value = None

        dto = TriggerPipelineDTO(suite_id=1, agent_id=1)

        # Act
        result = await service.trigger(dto)

        # Assert
        assert isinstance(result, EvalPipelineDTO)
        mock_pipeline_repo.save.assert_called()
        mock_eval_service.create_eval_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_raises_if_already_running(self, service, mock_pipeline_repo,
                                                      mock_suite_repo) -> None:
        from src.modules.evaluation.domain.exceptions import PipelineAlreadyRunningError
        running = make_pipeline_entity()
        running.start()
        mock_pipeline_repo.find_running_by_suite.return_value = running
        mock_suite_repo.get.return_value = None  # won't be reached

        with pytest.raises(PipelineAlreadyRunningError):
            await service.trigger(TriggerPipelineDTO(suite_id=1, agent_id=1))


class TestEvalPipelineServiceGet:
    @pytest.mark.asyncio
    async def test_get_returns_dto(self, service, mock_pipeline_repo) -> None:
        mock_pipeline_repo.get.return_value = make_pipeline_entity()
        result = await service.get(pipeline_id=1, user_id=1)
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_raises_if_not_found(self, service, mock_pipeline_repo) -> None:
        from src.modules.evaluation.domain.exceptions import EvalPipelineNotFoundError
        mock_pipeline_repo.get.return_value = None
        with pytest.raises(EvalPipelineNotFoundError):
            await service.get(pipeline_id=999, user_id=1)
```

**Step 3: 运行测试确认失败**

```bash
cd backend && uv run pytest tests/modules/evaluation/unit/application/test_eval_pipeline_service.py -v
```
预期: `FAILED` — `ModuleNotFoundError: eval_pipeline_service`

**Step 4: 创建 EvalPipelineService**

```python
# src/modules/evaluation/application/services/eval_pipeline_service.py
"""Eval Pipeline 应用服务。"""
import structlog

from src.modules.evaluation.application.dto.pipeline_dto import EvalPipelineDTO, TriggerPipelineDTO
from src.modules.evaluation.application.interfaces.eval_service import IEvalService
from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.modules.evaluation.domain.exceptions import (
    EvalPipelineNotFoundError,
    PipelineAlreadyRunningError,
    TestSuiteNotFoundError,
)
from src.modules.evaluation.domain.repositories.eval_pipeline_repository import IEvalPipelineRepository
from src.modules.evaluation.domain.repositories.test_case_repository import ITestCaseRepository
from src.modules.evaluation.domain.repositories.test_suite_repository import ITestSuiteRepository

log = structlog.get_logger(__name__)


def _to_dto(pipeline: EvalPipeline) -> EvalPipelineDTO:
    return EvalPipelineDTO(
        id=pipeline.id, suite_id=pipeline.suite_id, agent_id=pipeline.agent_id,
        trigger=pipeline.trigger, model_ids=pipeline.model_ids,
        status=pipeline.status.value, bedrock_job_id=pipeline.bedrock_job_id,
        score_summary=pipeline.score_summary, error_message=pipeline.error_message,
        started_at=pipeline.started_at, completed_at=pipeline.completed_at,
        created_at=pipeline.created_at,
    )


class EvalPipelineService:
    """Eval Pipeline 业务服务：触发、查询、对比。"""

    def __init__(self, pipeline_repo: IEvalPipelineRepository, suite_repo: ITestSuiteRepository,
                 case_repo: ITestCaseRepository, eval_service: IEvalService) -> None:
        self._pipeline_repo = pipeline_repo
        self._suite_repo = suite_repo
        self._case_repo = case_repo
        self._eval_service = eval_service

    async def trigger(self, dto: TriggerPipelineDTO) -> EvalPipelineDTO:
        """触发新的 Eval Pipeline。"""
        # 防止重复触发
        running = await self._pipeline_repo.find_running_by_suite(dto.suite_id)
        if running:
            raise PipelineAlreadyRunningError()

        suite = await self._suite_repo.get(dto.suite_id)
        if not suite:
            raise TestSuiteNotFoundError(dto.suite_id)

        cases = await self._case_repo.list_by_suite(dto.suite_id)
        test_inputs = [{"input": c.input_data, "expected": c.expected_output} for c in cases]

        pipeline = EvalPipeline(
            suite_id=dto.suite_id, agent_id=dto.agent_id,
            trigger=dto.trigger, model_ids=dto.model_ids,
        )
        pipeline = await self._pipeline_repo.save(pipeline)
        pipeline.start()

        job_id = await self._eval_service.create_eval_job(
            suite_name=suite.name, model_ids=dto.model_ids, test_cases=test_inputs,
        )
        pipeline.complete(bedrock_job_id=job_id, score_summary={})
        pipeline = await self._pipeline_repo.save(pipeline)

        log.info("eval_pipeline_triggered", pipeline_id=pipeline.id, suite_id=dto.suite_id)
        return _to_dto(pipeline)

    async def get(self, *, pipeline_id: int, user_id: int) -> EvalPipelineDTO:
        pipeline = await self._pipeline_repo.get(pipeline_id)
        if not pipeline:
            raise EvalPipelineNotFoundError(pipeline_id)
        return _to_dto(pipeline)

    async def list_by_suite(self, suite_id: int) -> list[EvalPipelineDTO]:
        pipelines = await self._pipeline_repo.list_by_suite(suite_id)
        return [_to_dto(p) for p in pipelines]
```

**Step 5: 运行测试确认通过**

```bash
uv run pytest tests/modules/evaluation/unit/application/test_eval_pipeline_service.py -v
```
预期: `4 passed`

**Step 6: 提交**

```bash
git add src/modules/evaluation/application/dto/pipeline_dto.py \
        src/modules/evaluation/application/services/eval_pipeline_service.py \
        tests/modules/evaluation/unit/application/test_eval_pipeline_service.py
git commit -m "feat(evaluation): 新增 EvalPipelineService + TriggerPipelineDTO"
```

---

## Task 6：`BedrockEvalAdapter` 基础设施适配器

**Files:**
- Create: `backend/src/modules/evaluation/infrastructure/external/bedrock_eval_adapter.py`
- Test: `backend/tests/modules/evaluation/unit/infrastructure/test_bedrock_eval_adapter.py`

**Step 1: 检查 infrastructure/external 目录**

```bash
ls backend/src/modules/evaluation/infrastructure/
```

若无 `external/`，创建：

```bash
mkdir -p backend/src/modules/evaluation/infrastructure/external
touch backend/src/modules/evaluation/infrastructure/external/__init__.py
```

**Step 2: 新建测试文件**

```python
# tests/modules/evaluation/unit/infrastructure/test_bedrock_eval_adapter.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.modules.evaluation.application.interfaces.eval_service import EvalJobResult
from src.modules.evaluation.infrastructure.external.bedrock_eval_adapter import BedrockEvalAdapter


@pytest.fixture
def mock_boto3_client():
    with patch("boto3.client") as mock_client:
        yield mock_client.return_value


class TestBedrockEvalAdapter:
    def test_create_eval_job_returns_job_id(self, mock_boto3_client) -> None:
        mock_boto3_client.create_model_evaluation_job.return_value = {
            "jobArn": "arn:aws:bedrock:us-east-1:123456789012:evaluation-job/test-job-001"
        }
        adapter = BedrockEvalAdapter(region="us-east-1")

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            adapter.create_eval_job("测试套件", ["haiku-model-id"], [{"input": "q", "expected": "a"}])
        )

        assert result == "test-job-001"
        mock_boto3_client.create_model_evaluation_job.assert_called_once()

    def test_get_eval_job_result_completed(self, mock_boto3_client) -> None:
        mock_boto3_client.get_model_evaluation_job.return_value = {
            "status": "Completed",
            "evaluationSummary": {"accuracy": 0.85},
        }
        adapter = BedrockEvalAdapter(region="us-east-1")

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            adapter.get_eval_job_result("test-job-001")
        )

        assert isinstance(result, EvalJobResult)
        assert result.status == "Completed"
        assert result.score_summary == {"accuracy": 0.85}

    def test_adapter_is_under_100_lines(self) -> None:
        import inspect
        import src.modules.evaluation.infrastructure.external.bedrock_eval_adapter as mod
        source = inspect.getsource(mod)
        line_count = len(source.splitlines())
        assert line_count < 100, f"适配器超过 100 行 ({line_count} 行)，违反 SDK-First 原则"
```

**Step 3: 运行测试确认失败**

```bash
uv run pytest tests/modules/evaluation/unit/infrastructure/test_bedrock_eval_adapter.py -v
```
预期: `FAILED` — `ModuleNotFoundError`

**Step 4: 创建适配器**

```python
# src/modules/evaluation/infrastructure/external/bedrock_eval_adapter.py
"""Bedrock Model Evaluation 薄封装适配器（< 100 行，SDK-First）。"""
import asyncio
from typing import Any

import boto3
import structlog

from src.modules.evaluation.application.interfaces.eval_service import EvalJobResult, IEvalService

log = structlog.get_logger(__name__)


class BedrockEvalAdapter(IEvalService):
    """Bedrock Model Evaluation Job API 薄封装，不超过 100 行。"""

    def __init__(self, region: str = "us-east-1") -> None:
        self._client = boto3.client("bedrock", region_name=region)

    async def create_eval_job(self, suite_name: str, model_ids: list[str],
                               test_cases: list[dict[str, str]]) -> str:
        response = await asyncio.to_thread(
            self._client.create_model_evaluation_job,
            jobName=f"eval-{suite_name[:40]}",
            roleArn="",  # 由 IAM 执行角色注入，运行时从 Settings 读取
            evaluatorModelConfig={"bedrockEvaluatorModels": [{"modelIdentifier": m} for m in model_ids]},
            inferenceConfig={"models": [{"bedrockModel": {"modelIdentifier": model_ids[0]}}]},
        )
        job_arn: str = response["jobArn"]
        job_id = job_arn.split("/")[-1]
        log.info("bedrock_eval_job_created", job_id=job_id, suite=suite_name)
        return job_id

    async def get_eval_job_result(self, job_id: str) -> EvalJobResult:
        response = await asyncio.to_thread(self._client.get_model_evaluation_job, jobIdentifier=job_id)
        return EvalJobResult(
            job_id=job_id,
            status=response.get("status", "Unknown"),
            score_summary=response.get("evaluationSummary", {}),
        )
```

**Step 5: 运行测试确认通过**

```bash
uv run pytest tests/modules/evaluation/unit/infrastructure/test_bedrock_eval_adapter.py -v
```
预期: `3 passed`

**Step 6: 提交**

```bash
git add src/modules/evaluation/infrastructure/external/ \
        tests/modules/evaluation/unit/infrastructure/
git commit -m "feat(evaluation): 新增 BedrockEvalAdapter (SDK-First, <100 行)"
```

---

## Task 7：ORM Model + Alembic 迁移

**Files:**
- Create: `backend/src/modules/evaluation/infrastructure/persistence/models/eval_pipeline_model.py`
- Create: `backend/migrations/versions/s8t9u0v1w2x3_add_eval_pipelines_table.py`

**Step 1: 查看现有 ORM 模型作为参考**

```bash
cat backend/src/modules/evaluation/infrastructure/persistence/models/evaluation_run_model.py
```

**Step 2: 创建 ORM 模型**

```python
# src/modules/evaluation/infrastructure/persistence/models/eval_pipeline_model.py
"""EvalPipeline ORM 模型。"""
import json
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class EvalPipelineModel(Base):
    __tablename__ = "eval_pipelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    suite_id: Mapped[int] = mapped_column(Integer, ForeignKey("test_suites.id"), nullable=False, index=True)
    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    model_ids_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled", index=True)
    bedrock_job_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    score_summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    @property
    def model_ids(self) -> list[str]:
        return json.loads(self.model_ids_json)

    @property
    def score_summary(self) -> dict:
        return json.loads(self.score_summary_json)
```

**Step 3: 生成 Alembic 迁移**

```bash
cd backend && uv run alembic revision --autogenerate -m "add_eval_pipelines_table"
```

检查生成的迁移文件，确认包含 `eval_pipelines` 表创建，不包含其他意外变更：

```bash
ls migrations/versions/ | grep eval_pipelines
```

**Step 4: 在本地 SQLite 测试迁移**

```bash
cd backend && DATABASE_URL=sqlite:///./test_migration.db uv run alembic upgrade head
echo "迁移成功" && rm -f test_migration.db
```

**Step 5: 提交**

```bash
git add src/modules/evaluation/infrastructure/persistence/models/eval_pipeline_model.py \
        migrations/versions/*eval_pipelines*
git commit -m "feat(evaluation): 新增 EvalPipelineModel ORM + Alembic 迁移"
```

---

## Task 8：`EvalPipelineRepositoryImpl`

**Files:**
- Create: `backend/src/modules/evaluation/infrastructure/persistence/repositories/eval_pipeline_repository_impl.py`
- Test: `backend/tests/modules/evaluation/integration/test_eval_pipeline_repository.py`

**Step 1: 查看现有 RepositoryImpl 作为参考**

```bash
head -60 backend/src/modules/evaluation/infrastructure/persistence/repositories/evaluation_run_repository_impl.py
```

**Step 2: 新建集成测试**

```python
# tests/modules/evaluation/integration/test_eval_pipeline_repository.py
import pytest
from datetime import datetime

from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.modules.evaluation.infrastructure.persistence.repositories.eval_pipeline_repository_impl import (
    EvalPipelineRepositoryImpl,
)


def make_pipeline() -> EvalPipeline:
    return EvalPipeline(
        suite_id=1, agent_id=1, trigger="manual",
        model_ids=["us.anthropic.claude-haiku-4-20250514-v1:0"],
    )


@pytest.mark.asyncio
class TestEvalPipelineRepositoryImpl:
    async def test_save_and_get(self, db_session) -> None:
        repo = EvalPipelineRepositoryImpl(db_session)
        pipeline = make_pipeline()
        saved = await repo.save(pipeline)
        assert saved.id is not None

        fetched = await repo.get(saved.id)
        assert fetched is not None
        assert fetched.suite_id == 1
        assert fetched.trigger == "manual"

    async def test_list_by_suite(self, db_session) -> None:
        repo = EvalPipelineRepositoryImpl(db_session)
        for _ in range(3):
            await repo.save(make_pipeline())

        results = await repo.list_by_suite(suite_id=1)
        assert len(results) == 3

    async def test_find_running_by_suite_returns_none_if_none(self, db_session) -> None:
        repo = EvalPipelineRepositoryImpl(db_session)
        result = await repo.find_running_by_suite(suite_id=99)
        assert result is None
```

**Step 3: 运行测试确认失败**

```bash
uv run pytest tests/modules/evaluation/integration/test_eval_pipeline_repository.py -v
```
预期: `FAILED` — `ModuleNotFoundError`

**Step 4: 创建仓储实现**

```python
# src/modules/evaluation/infrastructure/persistence/repositories/eval_pipeline_repository_impl.py
"""EvalPipeline 仓储实现。"""
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.modules.evaluation.domain.repositories.eval_pipeline_repository import IEvalPipelineRepository
from src.modules.evaluation.domain.value_objects.pipeline_status import PipelineStatus
from src.modules.evaluation.infrastructure.persistence.models.eval_pipeline_model import EvalPipelineModel
from src.shared.infrastructure.repositories import PydanticRepository


class EvalPipelineRepositoryImpl(PydanticRepository[EvalPipeline, EvalPipelineModel, int], IEvalPipelineRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, EvalPipelineModel, EvalPipeline)

    def _to_model(self, entity: EvalPipeline) -> EvalPipelineModel:
        return EvalPipelineModel(
            id=entity.id, suite_id=entity.suite_id, agent_id=entity.agent_id,
            trigger=entity.trigger, model_ids_json=json.dumps(entity.model_ids),
            status=entity.status.value, bedrock_job_id=entity.bedrock_job_id,
            score_summary_json=json.dumps(entity.score_summary),
            error_message=entity.error_message, started_at=entity.started_at,
            completed_at=entity.completed_at, created_at=entity.created_at, updated_at=entity.updated_at,
        )

    def _to_entity(self, model: EvalPipelineModel) -> EvalPipeline:
        return EvalPipeline(
            id=model.id, suite_id=model.suite_id, agent_id=model.agent_id,
            trigger=model.trigger, model_ids=model.model_ids,
            status=PipelineStatus(model.status), bedrock_job_id=model.bedrock_job_id,
            score_summary=model.score_summary, error_message=model.error_message,
            started_at=model.started_at, completed_at=model.completed_at,
            created_at=model.created_at, updated_at=model.updated_at,
        )

    async def list_by_suite(self, suite_id: int, limit: int = 20) -> list[EvalPipeline]:
        stmt = (select(EvalPipelineModel).where(EvalPipelineModel.suite_id == suite_id)
                .order_by(EvalPipelineModel.created_at.desc()).limit(limit))
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_running_by_suite(self, suite_id: int) -> EvalPipeline | None:
        stmt = select(EvalPipelineModel).where(
            EvalPipelineModel.suite_id == suite_id,
            EvalPipelineModel.status == PipelineStatus.RUNNING.value,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
```

**Step 5: 运行集成测试**

```bash
uv run pytest tests/modules/evaluation/integration/test_eval_pipeline_repository.py -v
```
预期: `3 passed`

**Step 6: 提交**

```bash
git add src/modules/evaluation/infrastructure/persistence/repositories/eval_pipeline_repository_impl.py \
        tests/modules/evaluation/integration/test_eval_pipeline_repository.py
git commit -m "feat(evaluation): 新增 EvalPipelineRepositoryImpl"
```

---

## Task 9：API 端点 + 依赖注入

**Files:**
- Modify: `backend/src/modules/evaluation/api/schemas/requests.py`
- Modify: `backend/src/modules/evaluation/api/schemas/responses.py`
- Modify: `backend/src/modules/evaluation/api/dependencies.py`
- Modify: `backend/src/modules/evaluation/api/endpoints.py`
- Test: `backend/tests/modules/evaluation/integration/test_eval_pipeline_endpoints.py`

**Step 1: 追加 API Schema（打开文件后追加，不删除现有内容）**

在 `requests.py` 末尾追加：

```python
# 追加到 requests.py
class TriggerPipelineRequest(BaseModel):
    model_ids: list[str] = ["us.anthropic.claude-haiku-4-20250514-v1:0"]
    trigger: str = "manual"
```

在 `responses.py` 末尾追加：

```python
# 追加到 responses.py
from datetime import datetime
from typing import Any

class EvalPipelineResponse(BaseModel):
    id: int
    suite_id: int
    agent_id: int
    trigger: str
    model_ids: list[str]
    status: str
    bedrock_job_id: str | None
    score_summary: dict[str, Any]
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
```

**Step 2: 追加依赖注入到 dependencies.py**

在 `dependencies.py` 末尾追加 `get_eval_pipeline_service` 依赖函数（参考现有 `get_evaluation_service` 函数的模式）。

**Step 3: 新建集成测试**

```python
# tests/modules/evaluation/integration/test_eval_pipeline_endpoints.py
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from src.modules.evaluation.application.dto.pipeline_dto import EvalPipelineDTO
from src.modules.evaluation.domain.exceptions import PipelineAlreadyRunningError
from datetime import datetime


def make_pipeline_dto() -> EvalPipelineDTO:
    return EvalPipelineDTO(
        id=1, suite_id=1, agent_id=1, trigger="manual",
        model_ids=["haiku-model-id"], status="completed",
        bedrock_job_id="job-001", score_summary={"accuracy": 0.9},
        error_message=None, started_at=None, completed_at=None,
        created_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
class TestEvalPipelineEndpoints:
    async def test_post_trigger_pipeline_returns_201(self, client: AsyncClient, admin_token: str) -> None:
        with patch("src.modules.evaluation.api.dependencies.get_eval_pipeline_service") as mock_dep:
            mock_service = AsyncMock()
            mock_service.trigger.return_value = make_pipeline_dto()
            mock_dep.return_value = mock_service

            response = await client.post(
                "/api/v1/eval-suites/1/pipelines",
                json={"model_ids": ["haiku-model-id"]},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        assert response.status_code == 201
        assert response.json()["id"] == 1

    async def test_post_trigger_returns_409_if_running(self, client: AsyncClient, admin_token: str) -> None:
        with patch("src.modules.evaluation.api.dependencies.get_eval_pipeline_service") as mock_dep:
            mock_service = AsyncMock()
            mock_service.trigger.side_effect = PipelineAlreadyRunningError()
            mock_dep.return_value = mock_service

            response = await client.post(
                "/api/v1/eval-suites/1/pipelines",
                json={},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        assert response.status_code == 409
```

**Step 4: 追加 API 端点到 endpoints.py**

在 `endpoints.py` 末尾追加两个端点：

```python
# 追加到 endpoints.py（不替换现有内容）
from src.modules.evaluation.api.schemas.requests import TriggerPipelineRequest
from src.modules.evaluation.api.schemas.responses import EvalPipelineResponse
from src.modules.evaluation.application.dto.pipeline_dto import TriggerPipelineDTO
from src.modules.evaluation.application.services.eval_pipeline_service import EvalPipelineService


@router.post("/eval-suites/{suite_id}/pipelines", response_model=EvalPipelineResponse, status_code=201)
async def trigger_pipeline(suite_id: int, body: TriggerPipelineRequest,
                            current_user: CurrentUserDep,
                            pipeline_service: EvalPipelineService = Depends(get_eval_pipeline_service)) -> EvalPipelineResponse:
    dto = TriggerPipelineDTO(suite_id=suite_id, agent_id=body.agent_id if hasattr(body, 'agent_id') else 0,
                             model_ids=body.model_ids, trigger=body.trigger)
    result = await pipeline_service.trigger(dto)
    return EvalPipelineResponse(**result.__dict__)


@router.get("/eval-suites/{suite_id}/pipelines", response_model=list[EvalPipelineResponse])
async def list_pipelines(suite_id: int, current_user: CurrentUserDep,
                         pipeline_service: EvalPipelineService = Depends(get_eval_pipeline_service)) -> list[EvalPipelineResponse]:
    results = await pipeline_service.list_by_suite(suite_id)
    return [EvalPipelineResponse(**r.__dict__) for r in results]
```

**Step 5: 运行集成测试**

```bash
uv run pytest tests/modules/evaluation/integration/test_eval_pipeline_endpoints.py -v
```
预期: `2 passed`

**Step 6: 提交**

```bash
git add src/modules/evaluation/api/ \
        tests/modules/evaluation/integration/test_eval_pipeline_endpoints.py
git commit -m "feat(evaluation): 新增 Eval Pipeline API 端点 (POST/GET /eval-suites/{id}/pipelines)"
```

---

## Task 10：质量验收

**Step 1: 运行所有 evaluation 模块测试**

```bash
cd backend && uv run pytest tests/modules/evaluation/ -v --cov=src/modules/evaluation --cov-report=term-missing
```
预期: 所有测试通过，覆盖率 ≥85%

**Step 2: 运行全量后端测试**

```bash
uv run pytest --cov=src --cov-fail-under=85
```
预期: `passed`，无回归

**Step 3: 代码质量检查**

```bash
uv run ruff check src/modules/evaluation/ && \
uv run ruff format --check src/modules/evaluation/ && \
uv run mypy src/modules/evaluation/
```
预期: 无错误，无警告

**Step 4: 架构合规测试**

```bash
uv run pytest tests/unit/test_architecture_compliance.py -v
```
预期: 全部通过

**Step 5: 最终提交**

```bash
git add .
git commit -m "feat(evaluation): M13 Eval Pipeline 完成 — 自动化评估 + BedrockEvalAdapter"
```

---

## 检查清单

- [ ] Task 1: PipelineStatus 枚举通过测试
- [ ] Task 2: EvalPipeline 实体 + 状态机 7 个测试全通过
- [ ] Task 3: IEvalPipelineRepository 接口 + 异常定义
- [ ] Task 4: IEvalService 接口定义
- [ ] Task 5: EvalPipelineService + DTO 4 个测试全通过
- [ ] Task 6: BedrockEvalAdapter 3 个测试（含 < 100 行断言）全通过
- [ ] Task 7: ORM Model + Alembic 迁移本地验证通过
- [ ] Task 8: EvalPipelineRepositoryImpl 3 个集成测试全通过
- [ ] Task 9: API 端点 2 个集成测试全通过
- [ ] Task 10: 全量测试 ≥85% 覆盖率，ruff + mypy 无错误
