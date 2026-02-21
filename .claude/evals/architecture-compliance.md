## EVAL: architecture-compliance
Created: 2026-02-21

### Capability Evals

#### DDD 战术模式合规
- [ ] 所有实体继承 PydanticEntity 基类
- [ ] 值对象使用 frozen=True (不可变)
- [ ] 仓库接口定义在 domain 层 (IRepository)
- [ ] 仓库实现在 infrastructure 层 (RepositoryImpl)
- [ ] 领域事件继承 DomainEvent 基类
- [ ] 应用服务通过 DTO 与 API 层通信 (非实体直传)
- [ ] 领域异常继承 DomainError 基类

#### 模块隔离规则
- [ ] R1: 模块间无直接 import (通过 shared/interfaces 通信)
- [ ] R2: Domain 层不依赖 Infrastructure 层 (依赖反转)
- [ ] R3: 跨模块查询通过 IQuerier 接口 (位于 shared)
- [ ] R4: 跨模块写操作通过 EventBus (异步事件)
- [ ] 各模块 __init__.py 仅导出公共 API

#### Clean Architecture 层级依赖
- [ ] domain → (无外部依赖)
- [ ] application → domain (仅向内依赖)
- [ ] infrastructure → domain + application (实现接口)
- [ ] api → application (通过 DTO 通信)
- [ ] 内层不知道外层存在

#### 四层结构一致性 (9 个业务模块)
- [ ] auth 模块: domain/ + application/ + infrastructure/ + api/
- [ ] agents 模块: domain/ + application/ + infrastructure/ + api/
- [ ] execution 模块: domain/ + application/ + infrastructure/ + api/
- [ ] tool_catalog 模块: domain/ + application/ + infrastructure/ + api/
- [ ] knowledge 模块: domain/ + application/ + infrastructure/ + api/
- [ ] templates 模块: domain/ + application/ + infrastructure/ + api/
- [ ] evaluation 模块: domain/ + application/ + infrastructure/ + api/
- [ ] insights 模块: domain/ + application/ + infrastructure/ + api/
- [ ] audit 模块: domain/ + application/ + infrastructure/ + api/

#### SDK-First 原则
- [ ] 外部 SDK 封装 < 100 行 (薄适配器)
- [ ] BedrockLLMClient < 100 行
- [ ] BedrockKnowledgeAdapter < 100 行
- [ ] BedrockEvalAdapter < 100 行 (72 行)
- [ ] S3DocumentStorage < 100 行
- [ ] CostExplorerAdapter < 100 行
- [ ] 精确捕获 SDK 异常 (ClientError/BotoCoreError)，非 Exception
- [ ] asyncio.to_thread() 包装 boto3 同步调用 (项目标准)

#### 禁止造轮子规则
- [ ] JWT 使用 PyJWT 库 (非自行实现)
- [ ] 密码哈希使用 bcrypt (非自行实现)
- [ ] Rate Limiting 使用 slowapi (非自行实现)
- [ ] ORM 使用 SQLAlchemy (非自行实现)
- [ ] 日志使用 structlog (非自行实现)
- [ ] 验证使用 Pydantic (非自行实现)

#### 常量管理 (C-S4-6)
- [ ] shared/domain/constants.py 定义业务常量
- [ ] DEFAULT_MAX_TOKENS 等常量统一引用 (非硬编码)
- [ ] 字段长度限制 Domain/ORM 层统一引用常量

#### 依赖注入
- [ ] Composition Root 在 presentation/api/providers.py
- [ ] 各模块 dependencies.py 定义 FastAPI Depends 链
- [ ] 外部服务通过接口注入 (可替换 Mock)

#### API 设计一致性
- [ ] RESTful 命名: 复数名词 (/agents, /tools, /templates)
- [ ] HTTP 方法语义正确 (POST=创建, GET=查询, PUT=更新, DELETE=删除)
- [ ] 状态码一致: 201 创建, 200 成功, 204 删除无内容
- [ ] 错误响应统一格式 {"code", "message", "details"}
- [ ] 分页统一 PageRequest/PageResponse

#### 测试架构
- [ ] 单元测试: domain/ + application/ (Mock 外部依赖)
- [ ] 集成测试: SQLite 内存数据库 + TestClient
- [ ] E2E 测试: Playwright (前端)
- [ ] 测试目录镜像 src/ 结构
- [ ] AAA 模式: Arrange → Act → Assert

### Regression Evals

#### 架构合规测试
- [ ] test_architecture_compliance.py 14/14 规则全部通过
- [ ] 新模块添加后合规测试自动覆盖

#### 模块独立性
- [ ] 任一模块可单独运行测试 (无跨模块 fixture 泄漏)
- [ ] 删除任一非 shared 模块不导致其他模块编译失败

#### 项目结构
- [ ] 目录结构符合 Monorepo 规范 (backend/frontend/infra/docs)
- [ ] .claude/rules/ 规范文档与实际代码一致

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
# 架构合规自动化测试
pytest backend/tests/test_architecture_compliance.py -v

# 全量质量检查
ruff check backend/
mypy backend/
pytest backend/tests/ --tb=short

# SDK-First 封装行数验证
wc -l backend/src/modules/execution/infrastructure/external/bedrock_llm_client.py
wc -l backend/src/modules/knowledge/infrastructure/external/bedrock_knowledge_adapter.py
wc -l backend/src/modules/evaluation/infrastructure/external/bedrock_eval_adapter.py
wc -l backend/src/modules/knowledge/infrastructure/external/s3_document_storage.py
wc -l backend/src/modules/insights/infrastructure/external/cost_explorer_adapter.py
```
