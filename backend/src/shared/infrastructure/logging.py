"""structlog 配置。

dev 环境: 彩色控制台输出
prod 环境: JSON 格式输出 (适配 CloudWatch Logs)
"""

import logging
import sys

import structlog


def setup_logging(*, log_level: str = "INFO", is_dev: bool = True) -> None:
    """初始化 structlog + 标准库 logging 配置。

    Args:
        log_level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        is_dev: 开发环境使用彩色控制台，生产环境使用 JSON
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if is_dev:
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 配置标准库 logging（拦截第三方库日志 → structlog 格式化输出）
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # 降低第三方库日志级别
    for noisy_logger in ("uvicorn.access", "uvicorn.error", "sqlalchemy.engine"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
