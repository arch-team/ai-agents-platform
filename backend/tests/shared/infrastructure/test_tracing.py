"""tracing 模块单元测试。"""

from unittest.mock import MagicMock, patch

import structlog

from src.shared.infrastructure.tracing import (
    get_tracer,
    inject_trace_context,
    setup_tracing,
)


class TestSetupTracing:
    """setup_tracing 配置测试。"""

    def test_dev_mode_uses_noop_exporter(self) -> None:
        """dev 模式下使用 _NoOpSpanExporter (避免 Console 输出淹没 structlog)。"""
        with (
            patch("src.shared.infrastructure.tracing.TracerProvider") as mock_provider,
            patch("src.shared.infrastructure.tracing._NoOpSpanExporter") as mock_noop,
            patch("src.shared.infrastructure.tracing.BatchSpanProcessor") as mock_processor,
            patch("src.shared.infrastructure.tracing.trace") as mock_trace,
            patch("src.shared.infrastructure.tracing.SQLAlchemyInstrumentor"),
        ):
            mock_provider_instance = MagicMock()
            mock_provider.return_value = mock_provider_instance

            setup_tracing(service_name="test-service", is_dev=True, otlp_endpoint="")

            mock_noop.assert_called_once()
            mock_processor.assert_called_once_with(mock_noop.return_value)
            mock_provider_instance.add_span_processor.assert_called_once_with(
                mock_processor.return_value,
            )
            mock_trace.set_tracer_provider.assert_called_once_with(mock_provider_instance)

    def test_prod_mode_with_otlp_endpoint_uses_otlp_exporter(self) -> None:
        """prod 模式且配置了 OTLP 端点时使用 OTLPSpanExporter。"""
        with (
            patch("src.shared.infrastructure.tracing.TracerProvider") as mock_provider,
            patch("src.shared.infrastructure.tracing.OTLPSpanExporter") as mock_otlp,
            patch("src.shared.infrastructure.tracing.BatchSpanProcessor") as mock_processor,
            patch("src.shared.infrastructure.tracing.trace") as mock_trace,
            patch("src.shared.infrastructure.tracing.SQLAlchemyInstrumentor"),
        ):
            mock_provider_instance = MagicMock()
            mock_provider.return_value = mock_provider_instance

            setup_tracing(
                service_name="test-service",
                is_dev=False,
                otlp_endpoint="http://localhost:4317",
            )

            mock_otlp.assert_called_once_with(endpoint="http://localhost:4317")
            mock_processor.assert_called_once_with(mock_otlp.return_value)
            mock_provider_instance.add_span_processor.assert_called_once()
            mock_trace.set_tracer_provider.assert_called_once_with(mock_provider_instance)

    def test_prod_mode_without_otlp_endpoint_falls_back_to_noop(self) -> None:
        """prod 模式但未配置 OTLP 端点时降级为 _NoOpSpanExporter。"""
        with (
            patch("src.shared.infrastructure.tracing.TracerProvider") as mock_provider,
            patch("src.shared.infrastructure.tracing._NoOpSpanExporter") as mock_noop,
            patch("src.shared.infrastructure.tracing.BatchSpanProcessor") as mock_processor,
            patch("src.shared.infrastructure.tracing.trace") as mock_trace,
            patch("src.shared.infrastructure.tracing.SQLAlchemyInstrumentor"),
        ):
            mock_provider_instance = MagicMock()
            mock_provider.return_value = mock_provider_instance

            setup_tracing(service_name="test-service", is_dev=False, otlp_endpoint="")

            mock_noop.assert_called_once()
            mock_processor.assert_called_once_with(mock_noop.return_value)
            mock_trace.set_tracer_provider.assert_called_once_with(mock_provider_instance)

    def test_resource_includes_service_name_and_environment(self) -> None:
        """Resource 包含 service.name 和 deployment.environment 属性。"""
        with (
            patch("src.shared.infrastructure.tracing.TracerProvider") as mock_provider,
            patch("src.shared.infrastructure.tracing.Resource") as mock_resource,
            patch("src.shared.infrastructure.tracing._NoOpSpanExporter"),
            patch("src.shared.infrastructure.tracing.BatchSpanProcessor"),
            patch("src.shared.infrastructure.tracing.trace"),
            patch("src.shared.infrastructure.tracing.SQLAlchemyInstrumentor"),
        ):
            mock_provider.return_value = MagicMock()

            setup_tracing(
                service_name="my-service",
                is_dev=True,
                otlp_endpoint="",
                environment="development",
            )

            mock_resource.create.assert_called_once()
            call_args = mock_resource.create.call_args[0][0]
            assert call_args["service.name"] == "my-service"
            assert call_args["deployment.environment"] == "development"

    def test_sqlalchemy_instrumentor_is_registered(self) -> None:
        """SQLAlchemyInstrumentor 在 setup 时被注册。"""
        with (
            patch("src.shared.infrastructure.tracing.TracerProvider") as mock_provider,
            patch("src.shared.infrastructure.tracing._NoOpSpanExporter"),
            patch("src.shared.infrastructure.tracing.BatchSpanProcessor"),
            patch("src.shared.infrastructure.tracing.trace"),
            patch("src.shared.infrastructure.tracing.SQLAlchemyInstrumentor") as mock_sqla,
        ):
            mock_provider.return_value = MagicMock()
            mock_instrumentor = MagicMock()
            mock_sqla.return_value = mock_instrumentor

            setup_tracing(service_name="test-service", is_dev=True, otlp_endpoint="")

            mock_sqla.assert_called_once()
            mock_instrumentor.instrument.assert_called_once()


class TestGetTracer:
    """get_tracer 工厂函数测试。"""

    def test_returns_tracer_with_module_name(self) -> None:
        """返回以模块名标识的 Tracer 实例。"""
        with patch("src.shared.infrastructure.tracing.trace") as mock_trace:
            mock_tracer = MagicMock()
            mock_trace.get_tracer.return_value = mock_tracer

            tracer = get_tracer("my.module")

            mock_trace.get_tracer.assert_called_once_with("my.module")
            assert tracer is mock_tracer


class TestInjectTraceContext:
    """trace_id 注入 structlog 上下文测试。"""

    def test_injects_trace_id_and_span_id_into_structlog(self) -> None:
        """将 trace_id 和 span_id 注入 structlog contextvars。"""
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.trace_id = 0x1234567890ABCDEF1234567890ABCDEF
        mock_context.span_id = 0x1234567890ABCDEF
        mock_span.get_span_context.return_value = mock_context

        with patch("src.shared.infrastructure.tracing.trace") as mock_trace:
            mock_trace.get_current_span.return_value = mock_span
            structlog.contextvars.clear_contextvars()

            inject_trace_context()

            ctx = structlog.contextvars.get_contextvars()
            assert "trace_id" in ctx
            assert "span_id" in ctx
            # trace_id 应该是 32 位十六进制字符串
            assert len(ctx["trace_id"]) == 32
            # span_id 应该是 16 位十六进制字符串
            assert len(ctx["span_id"]) == 16

    def test_does_not_inject_when_no_active_span(self) -> None:
        """无活跃 Span 时不注入。"""
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.trace_id = 0  # 无效的 trace_id
        mock_span.get_span_context.return_value = mock_context

        with patch("src.shared.infrastructure.tracing.trace") as mock_trace:
            mock_trace.get_current_span.return_value = mock_span
            structlog.contextvars.clear_contextvars()

            inject_trace_context()

            ctx = structlog.contextvars.get_contextvars()
            assert "trace_id" not in ctx
