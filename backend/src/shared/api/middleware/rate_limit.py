"""Rate Limiting 中间件."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


def _custom_rate_limit_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Rate Limit 超限统一错误响应."""
    return JSONResponse(
        status_code=429,
        content={
            "code": "RATE_LIMIT_EXCEEDED",
            "message": f"请求频率超限: {exc.detail}",
            "details": None,
        },
    )


# 全局 Limiter 实例, 以客户端 IP 为默认限流 key
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
)


def setup_rate_limiting(app: FastAPI) -> None:
    """注册 Rate Limiting 到 FastAPI 应用."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _custom_rate_limit_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)
