# 项目进度

> 每次 Claude Code 会话开始时读取此文件。会话结束时更新"当前状态"和"上次会话"。

## 当前状态

- **阶段**: Phase 1 MVP (0-3 月)
- **里程碑**: M1 项目脚手架 — ✅ 已完成
- **下一步**: 从 roadmap.md 拆解 M2 里程碑任务

## 模块状态

### Phase 1 (0-3 月)

| 模块 | 状态 | 分支 | 备注 |
|------|:----:|------|------|
| `shared` | 已完成 | ai-agents-factory-v1 | PydanticEntity, IRepository, EventBus, DomainError, get_db, get_settings, PydanticRepository, exception_handlers, schemas |
| `auth` | 已完成 | ai-agents-factory-v1 | User, Role, JWT, RBAC, get_current_user, 登录/注册/me 端点 |
| `agents` | 待开始 | - | Agent CRUD, 状态机 (draft → active → archived) |
| `execution` | 待开始 | - | 单 Agent 对话, Bedrock AgentCore 集成, SSE |

### 后续阶段

| 阶段 | 模块 |
|------|------|
| Phase 2 | tools, knowledge, monitoring, templates |
| Phase 3 | orchestration, evaluation, models |
| Phase 4 | audit, marketplace, analytics |

## 基础设施

| CDK Stack | 状态 | 备注 |
|-----------|:----:|------|
| NetworkStack | 待开始 | VPC, Subnets, NAT Gateway |
| SecurityStack | 待开始 | Security Groups, KMS, VPC Endpoints |
| DatabaseStack | 待开始 | Aurora MySQL 3.x |

---

## 当前 Milestone 任务拆解

### M1: 项目脚手架 (第 1-4 周) — ✅ 已完成

> 交付物: 后端 shared + auth 模块完成
> 验收标准: ruff check + mypy + pytest --cov-fail-under=85 全通过
> 验收结果: **254 测试通过，覆盖率 95.04%，ruff/mypy 全通过**

<details>
<summary>展开查看 M1 任务详情</summary>

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | 创建 backend 目录结构 + pyproject.toml + uv sync | 已完成 | - | `rules/project-structure.md` 初始化检查清单 | 2026-02-09 |
| 2 | shared/domain: PydanticEntity 基类 + IRepository 泛型接口 + DomainError 异常体系 | 已完成 | #1 | `rules/architecture.md` §5 DDD 战术模式 | 2026-02-09 |
| 3 | shared/domain: DomainEvent + EventBus (进程内事件总线) | 已完成 | #1 | `rules/architecture.md` §4.2 事件驱动通信 | 2026-02-09 |
| 4 | shared/infrastructure: get_db 数据库会话 + get_settings 配置管理 + PydanticRepository 基类实现 | 已完成 | #2 | `rules/tech-stack.md` + `rules/sdk-first.md` | 2026-02-09 |
| 5 | shared/api: exception_handler 统一异常处理 + 通用 schemas (PageRequest/PageResponse 等) | 已完成 | #2 | `rules/api-design.md` 错误格式 | 2026-02-09 |
| 6 | presentation/api/main.py: FastAPI app 工厂 + health check 端点 + CORS/中间件 | 已完成 | #4, #5 | `rules/observability.md` §1 Health Check | 2026-02-09 |
| 7 | tests: shared 模块单元测试 + 架构合规测试 (模块边界/依赖方向) | 已完成 | #2-#6 | `rules/testing.md` TDD + AAA 模式 | 2026-02-09 |
| 8 | auth/domain: User 实体 + Role 枚举 + IUserRepository 接口 | 已完成 | #2 | `rules/architecture.md` §5 + `rules/security.md` | 2026-02-09 |
| 9 | auth/application: UserService + JWT Token 签发/验证 + 密码哈希 | 已完成 | #4, #8 | `rules/security.md` + `rules/sdk-first.md` | 2026-02-09 |
| 10 | auth/infrastructure: UserRepositoryImpl + SQLAlchemy ORM Model + Alembic migration | 已完成 | #4, #8 | `rules/tech-stack.md` | 2026-02-09 |
| 11 | auth/api: 登录/注册端点 + get_current_user 依赖注入 + RBAC 权限装饰器 | 已完成 | #6, #9, #10 | `rules/api-design.md` + `rules/security.md` | 2026-02-09 |
| 12 | tests: auth 模块单元测试 + 集成测试 (含数据库交互) | 已完成 | #8-#11 | `rules/testing.md` TDD + AAA 模式 | 2026-02-09 |
| 13 | 质量验收: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过 | 已完成 | #1-#12 | `rules/checklist.md` + roadmap.md §2.6 | 2026-02-09 |

</details>

---

## 遗留事项

(当前无代码缺陷遗留)

### 部署注意事项

- Alembic migration 已配置并通过 `alembic history` 验证，但未连接实际 MySQL 运行 `alembic upgrade head`，首次部署时需验证

---

## 上次会话

> 仅保留最近一次，每次会话结束时覆盖更新此节。

- **日期**: 2026-02-09
- **完成**: M1 里程碑全部完成 — 13 项任务使用 Agent Teams (3 并行 agent) 在单次会话内全部交付；260 测试通过，覆盖率 98.23%；ruff/mypy 全通过；遗留事项全部清理（ANN101/102 warning 消除、passlib 替换为 bcrypt、dependencies.py 覆盖率 100%）；嵌入会话工作流协议到 Claude Code 自动加载配置
- **决策**: Application 层不直接导入 Settings (Infrastructure)，改为通过构造函数注入 JWT 配置参数，保持 Clean Architecture 分层纯净性；密码哈希从 passlib 改为直接使用 bcrypt 库（兼容性问题）；异常处理器从 type() 精确匹配改为 isinstance 匹配（修复子类异常映射 bug）
