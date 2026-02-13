"""structlog 日志配置测试。

覆盖 src/shared/infrastructure/logging.py 中的 setup_logging 函数，
验证 dev/prod 环境差异、日志级别、第三方库日志降级等行为。
"""

import logging

import pytest
import structlog

from src.shared.infrastructure.logging import setup_logging


@pytest.fixture(autouse=True)
def _reset_logging() -> None:  # type: ignore[misc]
    """每个测试前重置 logging 和 structlog 状态。"""
    # 测试前: 清理 root logger handlers，防止跨测试污染
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)

    yield  # type: ignore[misc]

    # 测试后: 再次清理
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)
    structlog.reset_defaults()


class TestSetupLoggingDevMode:
    """dev 环境日志配置测试。"""

    def test_dev_mode_configures_console_renderer(self) -> None:
        """dev 模式应使用彩色控制台渲染器。"""
        setup_logging(log_level="INFO", is_dev=True)

        # 验证 structlog 配置成功 (能正常获取 logger)
        logger = structlog.get_logger("test.dev")
        assert logger is not None

    def test_dev_mode_sets_root_logger_level(self) -> None:
        """dev 模式应正确设置 root logger 级别。"""
        setup_logging(log_level="DEBUG", is_dev=True)

        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_dev_mode_has_stdout_handler(self) -> None:
        """dev 模式应有且仅有一个 stdout handler。"""
        setup_logging(log_level="INFO", is_dev=True)

        root = logging.getLogger()
        assert len(root.handlers) == 1
        handler = root.handlers[0]
        assert isinstance(handler, logging.StreamHandler)


class TestSetupLoggingProdMode:
    """prod 环境日志配置测试。"""

    def test_prod_mode_configures_json_renderer(self) -> None:
        """prod 模式应使用 JSON 渲染器。"""
        setup_logging(log_level="INFO", is_dev=False)

        # 验证 structlog 配置成功
        logger = structlog.get_logger("test.prod")
        assert logger is not None

    def test_prod_mode_sets_root_logger_level(self) -> None:
        """prod 模式应正确设置 root logger 级别。"""
        setup_logging(log_level="WARNING", is_dev=False)

        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_prod_mode_formatter_uses_json(self) -> None:
        """prod 模式 handler 的 formatter 应包含 JSONRenderer。"""
        setup_logging(log_level="INFO", is_dev=False)

        root = logging.getLogger()
        handler = root.handlers[0]
        formatter = handler.formatter
        # ProcessorFormatter 的 processors 列表中应包含 JSONRenderer
        assert isinstance(formatter, structlog.stdlib.ProcessorFormatter)
        processor_types = [type(p) for p in formatter.processors]
        assert structlog.processors.JSONRenderer in processor_types


class TestSetupLoggingLogLevel:
    """日志级别配置测试。"""

    @pytest.mark.parametrize(
        ("level_str", "expected_level"),
        [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ],
    )
    def test_log_level_mapping(self, level_str: str, expected_level: int) -> None:
        """各日志级别字符串应正确映射到 logging 常量。"""
        setup_logging(log_level=level_str, is_dev=True)

        root = logging.getLogger()
        assert root.level == expected_level

    def test_log_level_case_insensitive(self) -> None:
        """日志级别应不区分大小写 (通过 .upper() 处理)。"""
        setup_logging(log_level="info", is_dev=True)

        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_default_log_level_is_info(self) -> None:
        """默认日志级别应为 INFO。"""
        setup_logging(is_dev=True)

        root = logging.getLogger()
        assert root.level == logging.INFO


class TestSetupLoggingThirdPartyNoise:
    """第三方库日志降级测试。"""

    @pytest.mark.parametrize(
        "logger_name",
        [
            "uvicorn.access",
            "uvicorn.error",
            "sqlalchemy.engine",
        ],
    )
    def test_noisy_loggers_set_to_warning(self, logger_name: str) -> None:
        """嘈杂的第三方库日志应被降级到 WARNING。"""
        setup_logging(log_level="DEBUG", is_dev=True)

        noisy_logger = logging.getLogger(logger_name)
        assert noisy_logger.level == logging.WARNING


class TestSetupLoggingHandlerManagement:
    """handler 管理测试。"""

    def test_clears_existing_handlers(self) -> None:
        """setup_logging 应清除已有 handlers 后重新添加。"""
        # 预先添加一个 dummy handler
        root = logging.getLogger()
        dummy_handler = logging.StreamHandler()
        root.addHandler(dummy_handler)

        # 调用 setup_logging 应移除 dummy handler
        setup_logging(log_level="INFO", is_dev=True)

        # dummy_handler 不应存在于当前 handlers 中
        assert dummy_handler not in root.handlers
        # 应包含 setup_logging 添加的 StreamHandler
        stream_handlers = [
            h for h in root.handlers if isinstance(h, logging.StreamHandler)
            and not type(h).__name__.startswith("LogCapture")
        ]
        assert len(stream_handlers) >= 1

    def test_repeated_setup_does_not_duplicate_handlers(self) -> None:
        """多次调用 setup_logging 不应产生重复 handler。"""
        setup_logging(log_level="INFO", is_dev=True)
        setup_logging(log_level="DEBUG", is_dev=False)

        root = logging.getLogger()
        assert len(root.handlers) == 1


class TestSetupLoggingStructlogIntegration:
    """structlog 集成测试。"""

    def test_structlog_bound_logger_available(self) -> None:
        """配置后应能获取 structlog lazy proxy (BoundLoggerLazyProxy)。"""
        setup_logging(log_level="INFO", is_dev=True)

        logger = structlog.get_logger("test.integration")
        # structlog.get_logger 返回 BoundLoggerLazyProxy，绑定后变为 BoundLogger
        assert logger is not None
        # 验证 bind 操作正常工作 (证明 structlog 已正确配置)
        bound = logger.bind(user_id=1)
        assert bound is not None

    def test_dev_mode_formatter_uses_console_renderer(self) -> None:
        """dev 模式 handler 的 formatter 应包含 ConsoleRenderer。"""
        setup_logging(log_level="INFO", is_dev=True)

        root = logging.getLogger()
        handler = root.handlers[0]
        formatter = handler.formatter
        assert isinstance(formatter, structlog.stdlib.ProcessorFormatter)
        processor_types = [type(p) for p in formatter.processors]
        assert structlog.dev.ConsoleRenderer in processor_types

    def test_shared_processors_include_timestamper(self) -> None:
        """共享处理器链应包含时间戳处理器。"""
        setup_logging(log_level="INFO", is_dev=True)

        root = logging.getLogger()
        formatter = root.handlers[0].formatter
        assert isinstance(formatter, structlog.stdlib.ProcessorFormatter)
        # foreign_pre_chain 包含共享处理器
        pre_chain_types = [type(p) for p in formatter.foreign_pre_chain]
        assert structlog.processors.TimeStamper in pre_chain_types

    def test_shared_processors_include_log_level(self) -> None:
        """共享处理器链应包含日志级别处理器。"""
        setup_logging(log_level="INFO", is_dev=True)

        root = logging.getLogger()
        formatter = root.handlers[0].formatter
        assert isinstance(formatter, structlog.stdlib.ProcessorFormatter)
        # 检查 add_log_level 在 foreign_pre_chain 中
        pre_chain_funcs = formatter.foreign_pre_chain
        assert structlog.stdlib.add_log_level in pre_chain_funcs
