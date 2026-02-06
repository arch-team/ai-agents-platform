# 日志规范 (Logging Standards)

> **职责**: 结构化日志规范，定义日志格式、级别、Correlation ID 和脱敏规则。

> Claude 生成日志相关代码时优先查阅此文档

---

## 0. 速查卡片

### 日志级别速查

| 级别 | 场景 | 示例 |
|------|------|------|
| `DEBUG` | 开发调试信息 | 请求参数、SQL 语句 |
| `INFO` | 业务流程关键节点 | 用户登录、Agent 创建 |
| `WARNING` | 非预期但可恢复的情况 | 重试、降级、接近配额 |
| `ERROR` | 业务错误，需关注 | 第三方 API 失败、数据校验失败 |
| `CRITICAL` | 系统级故障 | 数据库不可达、配置缺失 |

### 脱敏规则速查

| 字段 | 脱敏方式 | 示例 |
|------|---------|------|
| 密码 | 完全隐藏 | `"****"` |
| Token/API Key | 前 4 位保留 | `"sk-1****"` |
| 邮箱 | 部分隐藏 | `"z***@example.com"` |
| 手机号 | 中间隐藏 | `"138****5678"` |
| IP 地址 | 视场景保留 | 安全审计保留，普通日志脱敏 |

### 禁止事项

| ❌ 禁止 | ✅ 正确 |
|--------|--------|
| `print()` 调试输出 | `logger.debug()` |
| `logger.info(f"密码: {pwd}")` | `logger.info("login_attempt", user_id=user.id)` |
| 字符串拼接日志 | 结构化键值对 |
| 异常只记录 message | 记录完整 traceback |

---

## 1. 结构化日志配置

### 1.1 structlog 基础配置

```python
# src/shared/infrastructure/logging.py
import structlog

def configure_logging(env: str = "dev") -> None:
    """配置 structlog，dev 环境使用彩色控制台，prod 使用 JSON。"""
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if env == "prod":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

### 1.2 Logger 获取

```python
import structlog

logger = structlog.get_logger(__name__)

# 使用: 结构化键值对，不使用字符串拼接
logger.info("user_created", user_id=user.id, email=mask_email(user.email))
logger.error("api_call_failed", service="bedrock", status_code=500, duration_ms=1200)
```

---

## 2. Correlation ID

### 2.1 中间件注入

```python
# src/presentation/api/middleware/correlation.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```

### 2.2 传递规则

| 场景 | 传递方式 |
|------|---------|
| HTTP 请求 | `X-Correlation-ID` Header |
| 事件发布 | Event 属性 `correlation_id` |
| 异步任务 | 任务参数携带 |
| 日志输出 | structlog contextvars 自动注入 |

---

## 3. 请求/响应日志

```python
# 请求日志中间件关键字段
logger.info(
    "http_request",
    method=request.method,
    path=request.url.path,
    status_code=response.status_code,
    duration_ms=duration,
    client_ip=request.client.host,
    user_agent=request.headers.get("user-agent"),
)
```

### 日志字段命名规范

| 字段 | 命名 | 类型 |
|------|------|------|
| 请求方法 | `method` | str |
| 请求路径 | `path` | str |
| 状态码 | `status_code` | int |
| 耗时 | `duration_ms` | float |
| 用户 ID | `user_id` | str |
| 关联 ID | `correlation_id` | str (自动注入) |
| 错误码 | `error_code` | str |
| 服务名 | `service` | str |

---

## 4. 脱敏工具

```python
# src/shared/infrastructure/logging_utils.py
def mask_email(email: str) -> str:
    local, domain = email.split("@")
    return f"{local[0]}***@{domain}"

def mask_token(token: str) -> str:
    return f"{token[:4]}****" if len(token) > 4 else "****"

def mask_phone(phone: str) -> str:
    return f"{phone[:3]}****{phone[-4:]}" if len(phone) >= 7 else "****"
```

---

## 5. 环境差异

| 配置项 | Dev | Staging | Prod |
|--------|-----|---------|------|
| 格式 | 彩色控制台 | JSON | JSON |
| 级别 | DEBUG | INFO | INFO |
| 输出 | stdout | stdout | stdout → CloudWatch |
| 采样 | 无 | 无 | 高频日志可采样 |

---

## PR Review 检查清单

完整检查清单见 [checklist.md](checklist.md) §日志

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [security.md](security.md) | 敏感数据脱敏要求 |
| [tech-stack.md](tech-stack.md) | structlog 版本要求 |
