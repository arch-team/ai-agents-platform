"""健康检查端点。"""

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def liveness() -> dict[str, str]:
    """存活探针，进程存活即返回 ok。"""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness() -> dict[str, object]:
    """就绪探针，返回依赖检查结果。"""
    # MVP: 暂无外部依赖检查, 数据库检查在集成后补充
    return {"status": "ok", "checks": {}}
