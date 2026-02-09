"""Health check endpoints."""

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def liveness() -> dict[str, str]:
    """Liveness probe. Returns ok if process is alive."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness() -> dict[str, object]:
    """Readiness probe. Returns ok with dependency checks."""
    # MVP: 暂无外部依赖检查, 数据库检查在集成后补充
    checks: dict[str, str] = {}
    return {"status": "ok", "checks": checks}
