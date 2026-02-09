# 项目进度

> 每次 Claude Code 会话开始时读取此文件。会话结束时更新"当前状态"和"上次会话"。

## 当前状态

- **阶段**: Phase 1 MVP (0-3 月)
- **里程碑**: M1 项目脚手架 — 进行中
- **下一步**: 从任务 #1 开始，创建 backend 目录结构 + uv sync

## 模块状态

### Phase 1 (0-3 月)

| 模块 | 状态 | 分支 | 备注 |
|------|:----:|------|------|
| `shared` | 待开始 | - | PydanticEntity, IRepository, EventBus, DomainError, get_db |
| `auth` | 待开始 | - | JWT, RBAC, get_current_user |
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

### M1: 项目脚手架 (第 1-4 周)

> 交付物: 后端 shared + auth 模块完成
> 验收标准: ruff check + mypy + pytest --cov-fail-under=85 全通过

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | 创建 backend 目录结构 + pyproject.toml + uv sync | 待开始 | - | `rules/project-structure.md` 初始化检查清单 | - |
| 2 | shared/domain: PydanticEntity 基类 + IRepository 泛型接口 + DomainError 异常体系 | 待开始 | #1 | `rules/architecture.md` §5 DDD 战术模式 | - |
| 3 | shared/domain: DomainEvent + EventBus (进程内事件总线) | 待开始 | #1 | `rules/architecture.md` §4.2 事件驱动通信 | - |
| 4 | shared/infrastructure: get_db 数据库会话 + get_settings 配置管理 + PydanticRepository 基类实现 | 待开始 | #2 | `rules/tech-stack.md` + `rules/sdk-first.md` | - |
| 5 | shared/api: exception_handler 统一异常处理 + 通用 schemas (PageRequest/PageResponse 等) | 待开始 | #2 | `rules/api-design.md` 错误格式 | - |
| 6 | presentation/api/main.py: FastAPI app 工厂 + health check 端点 + CORS/中间件 | 待开始 | #4, #5 | `rules/observability.md` §1 Health Check | - |
| 7 | tests: shared 模块单元测试 + 架构合规测试 (模块边界/依赖方向) | 待开始 | #2-#6 | `rules/testing.md` TDD + AAA 模式 | - |
| 8 | auth/domain: User 实体 + Role 枚举 + IUserRepository 接口 | 待开始 | #2 | `rules/architecture.md` §5 + `rules/security.md` | - |
| 9 | auth/application: UserService + JWT Token 签发/验证 + 密码哈希 | 待开始 | #4, #8 | `rules/security.md` + `rules/sdk-first.md` | - |
| 10 | auth/infrastructure: UserRepositoryImpl + SQLAlchemy ORM Model + Alembic migration | 待开始 | #4, #8 | `rules/tech-stack.md` | - |
| 11 | auth/api: 登录/注册端点 + get_current_user 依赖注入 + RBAC 权限装饰器 | 待开始 | #6, #9, #10 | `rules/api-design.md` + `rules/security.md` | - |
| 12 | tests: auth 模块单元测试 + 集成测试 (含数据库交互) | 待开始 | #8-#11 | `rules/testing.md` TDD + AAA 模式 | - |
| 13 | 质量验收: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过 | 待开始 | #1-#12 | `rules/checklist.md` + roadmap.md §2.6 | - |

---

## 遗留事项

(当前无)

---

## 上次会话

> 仅保留最近一次，每次会话结束时覆盖更新此节。

- **日期**: 2026-02-09
- **完成**: 升级 progress.md 为"任务驱动器"格式 — 增加"当前 Milestone 任务拆解"区（M1: 13 项任务）和"遗留事项"区；从 roadmap.md 拆解 M1 任务并标注依赖关系和参考规范
- **决策**: 采用"文档驱动开发迭代工作流"方案，progress.md 作为任务驱动器，与 roadmap.md（决定做什么）、rules/*（指导怎么做）、checklist.md（验证做得对不对）形成闭环
