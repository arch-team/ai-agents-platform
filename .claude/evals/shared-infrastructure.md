## EVAL: shared-infrastructure
Created: 2026-02-21

### Capability Evals

#### PydanticEntity 基类
- [ ] PydanticEntity 自动生成自增 int id
- [ ] PydanticEntity 自动填充 created_at / updated_at 时间戳
- [ ] updated_at 在实体更新时自动刷新
- [ ] 实体支持 Pydantic model_validate / model_dump 序列化
- [ ] id=None 表示未持久化的新实体 (id: int | None = None)

#### IRepository 泛型接口
- [ ] IRepository 定义 create(entity) 方法
- [ ] IRepository 定义 update(entity) 方法
- [ ] IRepository 定义 get_by_id(id) 方法
- [ ] IRepository 定义 delete(id) 方法
- [ ] IRepository 定义 list_all(offset, limit) 分页方法
- [ ] 方法签名使用 async def

#### PydanticRepository 基类
- [ ] PydanticRepository 实现 IRepository 全部方法
- [ ] 正确处理 SQLAlchemy AsyncSession
- [ ] Entity ↔ ORM Model 双向转换正确
- [ ] list_all 分页查询返回正确的 offset/limit 结果
- [ ] get_by_id 不存在时返回 None (非异常)

#### EventBus 进程内事件总线
- [ ] EventBus.subscribe(event_type, handler) 注册订阅
- [ ] EventBus.publish(event) 触发所有订阅者
- [ ] 支持同一事件类型多个订阅者
- [ ] 订阅者异常不阻塞其他订阅者
- [ ] WeakRef 弱引用防止内存泄漏 (C-S2-3)
- [ ] publish 为 async 方法

#### DomainEvent 基类
- [ ] DomainEvent 包含 event_id (UUID) + occurred_at 时间戳
- [ ] 子类可自定义额外字段
- [ ] 事件对象不可变

#### DomainError 异常体系
- [ ] DomainError 基类包含 code + message
- [ ] AuthenticationError → 401 映射
- [ ] AuthorizationError → 403 映射
- [ ] *NotFoundError → 404 映射
- [ ] *DuplicateError → 409 映射
- [ ] InvalidStatusTransitionError → 409 映射
- [ ] AccountLockedError → 423 映射
- [ ] 异常体系可扩展 (各模块定义子类)

#### get_db 数据库会话管理
- [ ] get_db() 返回 AsyncSession
- [ ] 请求结束后 session 自动关闭
- [ ] 连接池参数正确 (pool_size, max_overflow, pool_timeout, pool_recycle)
- [ ] 自定义线程池 (C-S2-1) 正常工作
- [ ] pool_recycle 从 Settings 读取 (非硬编码)

#### get_settings 配置管理
- [ ] Settings 从环境变量加载配置
- [ ] JWT_SECRET 启动校验 (非默认值时报错，C-S0-6)
- [ ] CORS_ALLOWED_ORIGINS 运行时校验 (C-S1-5)
- [ ] 所有数据库连接参数可通过环境变量覆盖
- [ ] Settings 为单例 (functools.lru_cache)

#### 通用 Schemas
- [ ] PageRequest 包含 page + page_size，有合理默认值和约束
- [ ] PageResponse 包含 items + total + page + page_size + total_pages
- [ ] ErrorResponse 包含 code + message + details
- [ ] 统一异常处理器正确映射所有 DomainError 子类

#### 结构化日志
- [ ] structlog 配置正确初始化
- [ ] Correlation ID 自动注入日志上下文
- [ ] 日志格式包含 timestamp + level + module + correlation_id
- [ ] log.exception 正确记录异常堆栈

#### OpenTelemetry 可观测性
- [ ] OTEL 追踪正确初始化
- [ ] SQLAlchemy instrumentation 正常工作
- [ ] FastAPI 自动追踪集成正常
- [ ] 追踪不影响应用性能

#### 跨模块接口 (shared/domain/interfaces)
- [ ] IAgentQuerier 接口定义 get_active_agent() 方法
- [ ] IToolQuerier 接口定义 get_approved_tools() 方法
- [ ] IKnowledgeQuerier 接口定义相关方法
- [ ] ActiveAgentInfo 数据结构包含必要字段
- [ ] 接口位置在 shared 而非具体模块 (模块隔离)

### Regression Evals

#### 基类稳定性
- [ ] PydanticEntity API 不变 (所有 9 模块依赖)
- [ ] IRepository 方法签名不变 (所有仓库实现依赖)
- [ ] PydanticRepository 行为不变 (所有 RepositoryImpl 继承)
- [ ] EventBus 发布/订阅接口不变 (审计+Insights+Gateway 订阅)
- [ ] DomainError 体系不变 (异常处理器映射依赖)

#### 数据库
- [ ] AsyncSession 创建和关闭行为正常
- [ ] 连接池在高并发下稳定 (无连接泄漏)

#### 配置
- [ ] Settings 默认值向后兼容
- [ ] 新增环境变量不破坏现有部署

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
# shared 模块全量测试
pytest backend/tests/shared/ -v --tb=short

# 域基类测试
pytest backend/tests/shared/domain/ -v

# 基础设施测试
pytest backend/tests/shared/infrastructure/ -v

# API 层测试 (异常处理/Schema)
pytest backend/tests/shared/api/ -v

# 日志模块
pytest backend/tests/shared/infrastructure/test_logging*.py -v
```
