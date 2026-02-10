"""健康检查端点。"""

import asyncio

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.shared.infrastructure.database import get_engine


router = APIRouter(tags=["health"])
logger = structlog.get_logger(__name__)

_DB_CHECK_TIMEOUT = 3  # 秒


@router.get("/health")
def liveness() -> dict[str, str]:
    """存活探针，进程存活即返回 ok。"""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness() -> JSONResponse:
    """就绪探针，检查数据库连接可用性。"""
    checks: dict[str, str] = {}
    overall_status = "ok"

    # 数据库连接检查
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await asyncio.wait_for(
                conn.execute(text("SELECT 1")),
                timeout=_DB_CHECK_TIMEOUT,
            )
        checks["database"] = "ok"
    except RuntimeError:
        # 数据库未初始化（init_db 未调用）
        checks["database"] = "not_initialized"
        overall_status = "degraded"
    except (TimeoutError, asyncio.TimeoutError):
        checks["database"] = "timeout"
        overall_status = "degraded"
        logger.warning("readiness_check_failed", check="database", reason="timeout")
    except Exception:
        checks["database"] = "error"
        overall_status = "degraded"
        logger.exception("readiness_check_failed", check="database")

    status_code = 200 if overall_status == "ok" else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": overall_status, "checks": checks},
    )
