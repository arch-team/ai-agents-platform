# 日志规范 (Logging Standards)

> **职责**: 结构化日志规范，定义日志格式、级别、Correlation ID 和脱敏规则。

---

## 速查卡片

### 日志级别

| 级别 | 场景 | 示例 |
|------|------|------|
| `DEBUG` | 开发调试 | 请求参数、SQL 语句 |
| `INFO` | 业务关键节点 | 用户登录、Agent 创建 |
| `WARNING` | 可恢复异常 | 重试、降级、接近配额 |
| `ERROR` | 业务错误 | 第三方 API 失败、数据校验失败 |
| `CRITICAL` | 系统级故障 | 数据库不可达、配置缺失 |

### 禁止事项

| ❌ 禁止 | ✅ 正确 |
|--------|--------|
| `print()` 调试输出 | `logger.debug()` |
| `logger.info(f"密码: {pwd}")` | `logger.info("login_attempt", user_id=user.id)` |
| 字符串拼接日志 | 结构化键值对 |
| 异常只记录 message | 记录完整 traceback |

---

## 1. 结构化日志

**库**: structlog | **配置**: `src/shared/infrastructure/logging.py`

```python
# Logger 获取和使用
logger = structlog.get_logger(__name__)
logger.info("user_created", user_id=user.id, email=mask_email(user.email))
logger.error("api_call_failed", service="bedrock", status_code=500, duration_ms=1200)
```

**关键约束**: dev 环境彩色控制台输出，prod 环境 JSON 输出。

### 标准字段命名

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

## 2. Correlation ID

**中间件**: `src/presentation/api/middleware/correlation.py`

| 场景 | 传递方式 |
|------|---------|
| HTTP 请求 | `X-Correlation-ID` Header |
| 事件发布 | Event 属性 `correlation_id` |
| 异步任务 | 任务参数携带 |
| 日志输出 | structlog contextvars 自动注入 |

---

## 3. 脱敏规则

**工具函数**: `src/shared/infrastructure/logging_utils.py`

| 字段 | 脱敏方式 | 示例 |
|------|---------|------|
| 密码 | 完全隐藏 | `"****"` |
| Token/API Key | `mask_token()` 前 4 位保留 | `"sk-1****"` |
| 邮箱 | `mask_email()` 部分隐藏 | `"z***@example.com"` |
| 手机号 | `mask_phone()` 中间隐藏 | `"138****5678"` |
| IP 地址 | 视场景 | 安全审计保留，普通日志脱敏 |

---

## 4. 环境差异

| 配置项 | Dev | Staging | Prod |
|--------|-----|---------|------|
| 格式 | 彩色控制台 | JSON | JSON |
| 级别 | DEBUG | INFO | INFO |
| 输出 | stdout | stdout | stdout → CloudWatch |

---

## 相关文档

- [checklist.md](checklist.md) §日志 - PR Review 检查清单
- [security.md](security.md) - 敏感数据脱敏要求
- [observability.md](observability.md) - 可观测性（Metrics/Tracing）
