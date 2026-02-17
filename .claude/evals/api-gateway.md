## EVAL: api-gateway
Created: 2026-02-17

### Capability Evals

#### 健康检查
- [ ] GET /health 返回 {"status": "ok"} (存活探针)
- [ ] GET /health/ready 返回数据库连接状态 (就绪探针)
- [ ] 数据库不可达时 /health/ready 返回 degraded 状态
- [ ] 健康检查端点无需认证

#### CORS 配置
- [ ] CORS 允许 CORS_ALLOWED_ORIGINS 环境变量指定的域名
- [ ] 允许的 HTTP 方法: GET, POST, PUT, DELETE
- [ ] 允许的请求头: Authorization, Content-Type
- [ ] 允许携带凭证 (allow_credentials=True)
- [ ] 非允许域名的跨域请求被拒绝

#### Correlation ID 中间件
- [ ] 请求携带 X-Correlation-ID 时使用该值
- [ ] 请求未携带 X-Correlation-ID 时自动生成 UUID
- [ ] Correlation ID 注入到 structlog contextvars
- [ ] Correlation ID 返回到响应头

#### Rate Limiting
- [ ] 全局默认限流: 60 次/分钟 per IP
- [ ] 超限返回 429 + RATE_LIMIT_EXCEEDED 错误码
- [ ] 认证端点有独立更严格限制 (注册 3/h, 登录 5/min, 刷新 10/min)

#### 路由注册
- [ ] 所有 13 个 Router 正确注册 (health, auth, agents, conversations, team-executions, preview, tools, knowledge-bases, insights, templates, evaluation, audit, stats)
- [ ] 路由前缀正确 (/api/v1/*)

#### 异常处理
- [ ] DomainError 子类正确映射到 HTTP 状态码
- [ ] 统一错误响应格式: {"code": "...", "message": "...", "details": null}
- [ ] AuthenticationError -> 401
- [ ] AuthorizationError -> 403
- [ ] *NotFoundError -> 404
- [ ] *DuplicateError -> 409
- [ ] AccountLockedError -> 423
- [ ] 未处理异常 -> 500 (INTERNAL_ERROR)

#### 应用生命周期
- [ ] 启动时初始化结构化日志
- [ ] 启动时初始化 OpenTelemetry 追踪
- [ ] 启动时初始化数据库连接池
- [ ] 启动时注册事件订阅 (5 类)
- [ ] FastAPI 自动追踪集成正常

#### 统计端点
- [ ] GET /api/v1/stats/summary ADMIN 角色看全局统计
- [ ] GET /api/v1/stats/summary 普通用户看自己的统计
- [ ] 返回 agents_total, conversations_total, team_executions_total

#### 文档控制
- [ ] 非 debug 环境禁用 /docs 和 /redoc
- [ ] debug 环境可访问 /docs 和 /redoc

### Regression Evals

#### 中间件链
- [ ] 中间件执行顺序正确 (CORS -> Correlation -> Rate Limit -> 业务)
- [ ] 中间件不影响 SSE 流式端点
- [ ] 中间件不影响健康检查端点

#### 异常处理
- [ ] 所有 20+ 种 DomainError 映射关系不变
- [ ] 未注册的异常类型返回 500

#### 数据库连接
- [ ] 连接池参数 (pool_size, max_overflow, pool_timeout, pool_recycle) 正确
- [ ] 数据库会话正确关闭 (无连接泄漏)

#### 事件系统
- [ ] Gateway 工具同步订阅正常
- [ ] 团队执行成本归因订阅正常
- [ ] 消息接收成本归因订阅正常
- [ ] 记忆提取订阅正常
- [ ] 审计日志订阅正常

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
# 应用工厂测试
pytest backend/tests/presentation/api/test_main.py -v

# 健康检查测试
pytest backend/tests/presentation/api/test_health.py -v

# 统计端点测试
pytest backend/tests/presentation/api/test_stats.py -v

# 中间件测试
pytest backend/tests/presentation/api/middleware/ -v
pytest backend/tests/shared/api/middleware/ -v

# 异常处理测试
pytest backend/tests/shared/api/test_exception_handlers.py -v

# 全量
pytest backend/tests/presentation/ backend/tests/shared/api/ -v --tb=short
```
