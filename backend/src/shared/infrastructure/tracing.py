"""OpenTelemetry 分布式追踪配置。

dev 环境: NoOp (禁用 Span 导出, 避免淹没 structlog)
prod 环境: OTLPSpanExporter (导出到 ADOT Collector → CloudWatch)
未配置 OTLP 端点时: 降级为 NoOp
"""

from collections.abc import Sequence

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult


logger = structlog.get_logger(__name__)


class _NoOpSpanExporter(SpanExporter):
    """静默丢弃 Span, 避免 Console 输出干扰 structlog 业务日志。"""

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass


def setup_tracing(
    *,
    service_name: str,
    is_dev: bool,
    otlp_endpoint: str,
    environment: str = "",
) -> None:
    """初始化 OpenTelemetry TracerProvider。

    Args:
        service_name: 服务名称 (对应 Resource 的 service.name)
        is_dev: 开发环境标志
        otlp_endpoint: OTLP 导出端点 (如 http://localhost:4317)
        environment: 部署环境名 (development/staging/production)
    """
    resource = Resource.create(
        {
            "service.name": service_name,
            "deployment.environment": environment,
        },
    )

    provider = TracerProvider(resource=resource)

    # 选择 Exporter: dev/无 OTLP 端点时禁用导出 (避免 Console 输出淹没 structlog), 否则使用 OTLP
    exporter: SpanExporter
    if is_dev or not otlp_endpoint:
        exporter = _NoOpSpanExporter()
        exporter_type = "noop"
    else:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        exporter_type = "otlp"

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    # SQLAlchemy 自动追踪: 拦截所有后续创建的数据库引擎
    SQLAlchemyInstrumentor().instrument()

    logger.info(
        "tracing_initialized",
        service_name=service_name,
        exporter=exporter_type,
        environment=environment,
    )


def get_tracer(name: str) -> trace.Tracer:
    """获取指定名称的 Tracer 实例。"""
    return trace.get_tracer(name)


def inject_trace_context() -> None:
    """将当前 Span 的 trace_id 和 span_id 注入 structlog contextvars。

    使 structlog 日志自动携带 tracing 信息，实现日志-链路关联。
    """
    span = trace.get_current_span()
    span_context = span.get_span_context()

    if span_context.trace_id == 0:
        return

    structlog.contextvars.bind_contextvars(
        trace_id=format(span_context.trace_id, "032x"),
        span_id=format(span_context.span_id, "016x"),
    )
