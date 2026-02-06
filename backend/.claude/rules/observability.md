# 可观测性规范 (Observability Standards)

> **职责**: 可观测性规范，定义 Metrics、Distributed Tracing 和 Health Check 端点。

> Claude 生成监控、健康检查相关代码时优先查阅此文档

---

## 0. 速查卡片

### 三大支柱

| 支柱 | 用途 | 工具 |
|------|------|------|
| **Logs** | 事件记录 | structlog → CloudWatch Logs (详见 [logging.md](logging.md)) |
| **Metrics** | 量化指标 | OpenTelemetry / CloudWatch Metrics |
| **Traces** | 请求链路追踪 | OpenTelemetry / AWS X-Ray |

### Health Check 端点

| 端点 | 用途 | 返回 |
|------|------|------|
| `GET /health` | 存活检查 (Liveness) | `{"status": "ok"}` |
| `GET /health/ready` | 就绪检查 (Readiness) | `{"status": "ok", "checks": {...}}` |

---

## 1. Health Check

### 1.1 实现模板

```python
# src/presentation/api/routes/health.py
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])

@router.get("/health")
async def liveness() -> dict:
    """存活检查: 进程是否运行。"""
    return {"status": "ok"}

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """就绪检查: 依赖服务是否可用。"""
    checks = {}
    overall_status = "ok"

    # 数据库检查
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
        overall_status = "degraded"

    status_code = status.HTTP_200_OK if overall_status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={"status": overall_status, "checks": checks},
    )
```

### 1.2 依赖检查项

| 依赖 | 检查方式 | 超时 |
|------|---------|------|
| 数据库 | `SELECT 1` | 3s |
| Redis/缓存 | `PING` | 2s |
| 外部 API | HTTP HEAD 或跳过 | 5s |

**规则**: Health Check 不应包含业务逻辑，仅检查连接可用性。

---

## 2. Metrics

### 2.1 关键业务指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `http_requests_total` | Counter | HTTP 请求总数 (按 method, path, status) |
| `http_request_duration_seconds` | Histogram | 请求延迟分布 |
| `db_query_duration_seconds` | Histogram | 数据库查询延迟 |
| `agent_execution_duration_seconds` | Histogram | Agent 执行耗时 |
| `llm_tokens_total` | Counter | LLM Token 消耗 (按 model, type) |
| `active_tasks` | Gauge | 活跃异步任务数 |

### 2.2 命名规范

```
{namespace}_{subsystem}_{name}_{unit}
```

| 规则 | ✅ 正确 | ❌ 错误 |
|------|--------|--------|
| 使用 snake_case | `http_request_duration_seconds` | `httpRequestDuration` |
| 携带单位后缀 | `_seconds`, `_bytes`, `_total` | 无单位 |
| Counter 用 `_total` | `requests_total` | `request_count` |

---

## 3. Distributed Tracing

### 3.1 OpenTelemetry 配置

```python
# src/shared/infrastructure/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def configure_tracing(service_name: str, env: str) -> None:
    provider = TracerProvider(resource=Resource.create({
        "service.name": service_name,
        "deployment.environment": env,
    }))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
```

### 3.2 Span 规范

| 场景 | Span 名称模式 | 必须属性 |
|------|-------------|---------|
| HTTP 请求 | `{method} {path}` | `http.method`, `http.status_code` |
| 数据库查询 | `db.{operation}` | `db.system`, `db.statement` |
| 外部 API 调用 | `{service}.{operation}` | `peer.service`, `http.url` |
| Agent 执行 | `agent.execute` | `agent.id`, `agent.type` |

```python
tracer = trace.get_tracer(__name__)

async def call_bedrock(prompt: str) -> str:
    with tracer.start_as_current_span("bedrock.invoke_model") as span:
        span.set_attribute("llm.model", model_id)
        span.set_attribute("llm.prompt_tokens", token_count)
        result = await client.invoke_model(...)
        span.set_attribute("llm.completion_tokens", result.usage.output_tokens)
        return result
```

---

## 4. 环境配置

| 配置项 | Dev | Staging | Prod |
|--------|-----|---------|------|
| Tracing | 禁用或本地 Jaeger | X-Ray | X-Ray |
| Metrics | 控制台输出 | CloudWatch | CloudWatch |
| Health Check | 启用 | 启用 | 启用 + ALB 集成 |
| 采样率 | 100% | 10% | 1-5% |

---

## PR Review 检查清单

完整检查清单见 [checklist.md](checklist.md) §可观测性

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [logging.md](logging.md) | 结构化日志规范 |
| [security.md](security.md) | 敏感数据脱敏 |
| [tech-stack.md](tech-stack.md) | 依赖版本 |
