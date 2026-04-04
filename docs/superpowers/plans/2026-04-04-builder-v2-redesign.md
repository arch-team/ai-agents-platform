# M17: Agent Blueprint + Builder V2 实施方案

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Agent Blueprint 架构 (ADR-010 v3)：Skills 模块 + 工作目录管理 + 独立 Runtime 生命周期 + Builder V2 SOP 引导式构建器。业务专家通过 Builder 将 SOP 转化为 SKILL.md，组装为 Agent 工作目录，TESTING 阶段创建专属 AgentCore Runtime，验证通过后上线给最终用户。

**Architecture:** 详见 `docs/adr/010-agent-blueprint-architecture.md` (v3)

**Tech Stack:** Python 3.12 + FastAPI + SQLAlchemy 2.0 + claude-agent-sdk + bedrock-agentcore | S3 + EFS | React 19 + TypeScript + Zustand

---

## M17-A: 基础设施 (2-3 周, 8 Tasks)

### Task 1: Skills 模块 — 领域层

**Files:**
- Create: `backend/src/modules/skills/__init__.py`
- Create: `backend/src/modules/skills/domain/entities/skill.py`
- Create: `backend/src/modules/skills/domain/value_objects/skill_status.py`
- Create: `backend/src/modules/skills/domain/value_objects/skill_category.py`
- Create: `backend/src/modules/skills/domain/repositories/skill_repository.py`
- Create: `backend/src/modules/skills/domain/exceptions.py`
- Test: `tests/modules/skills/unit/domain/test_skill_entity.py`

Skill 实体只存元信息 (SKILL.md 内容在文件系统):
```python
class Skill(PydanticEntity):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500, default="")
    category: SkillCategory = SkillCategory.GENERAL
    trigger_description: str = Field(max_length=500, default="")
    status: SkillStatus = SkillStatus.DRAFT
    creator_id: int
    version: int = 1
    usage_count: int = 0
    file_path: str = ""  # 文件系统中的 Skill 目录路径
```

- [ ] 写 Skill 状态机测试 (DRAFT → PUBLISHED → ARCHIVED)
- [ ] 实现 Skill 实体 + 值对象 + 仓储接口
- [ ] 运行确认通过
- [ ] Commit `feat(skills): Skills 模块领域层`

### Task 2: Skills 模块 — 文件系统操作

**Files:**
- Create: `backend/src/modules/skills/application/interfaces/skill_file_manager.py`
- Create: `backend/src/modules/skills/infrastructure/external/skill_file_manager_impl.py`
- Test: `tests/modules/skills/unit/infrastructure/test_skill_file_manager.py`

ISkillFileManager: save_draft / publish / read_skill_md / delete_draft / link_to_workspace
实现: aiofiles + pathlib, 路径安全校验

- [ ] TDD 实现文件操作 (tmp_path fixture)
- [ ] Commit `feat(skills): Skill 文件系统操作 (ISkillFileManager)`

### Task 3: Skills 模块 — 应用服务 + API + 持久化

**Files:**
- Create: `backend/src/modules/skills/application/services/skill_service.py`
- Create: `backend/src/modules/skills/application/dto/skill_dto.py`
- Create: `backend/src/modules/skills/api/endpoints.py` (8 端点)
- Create: `backend/src/modules/skills/api/schemas/`
- Create: `backend/src/modules/skills/api/dependencies.py`
- Create: `backend/src/modules/skills/infrastructure/persistence/`
- Create: `backend/src/shared/domain/interfaces/skill_querier.py`
- Create: `backend/src/modules/skills/infrastructure/services/skill_querier_impl.py`
- Test: 单元 + 集成测试

- [ ] TDD 实现 SkillService (CRUD + 发布 + 文件联动)
- [ ] 实现 ORM + Repository + 迁移
- [ ] 实现 API 端点 + ISkillQuerier 跨模块接口
- [ ] 集成测试
- [ ] Commit `feat(skills): Skills 模块完整实现`

### Task 4: Agent Blueprint 数据模型

**Files:**
- Create: `backend/src/modules/agents/domain/value_objects/agent_blueprint.py`
- Create: `backend/src/modules/agents/infrastructure/persistence/models/agent_blueprint_model.py`
- Create: `backend/migrations/versions/xxx_add_blueprints.py`
- Modify: `backend/src/modules/agents/domain/value_objects/agent_status.py` (+TESTING)
- Modify: `backend/src/shared/domain/interfaces/agent_querier.py` (+workspace_path, +runtime_arn)
- Test: `tests/modules/agents/unit/domain/test_agent_blueprint.py`

Blueprint 值对象: Persona, ToolBinding, MemoryConfig, Guardrail
Agent 状态扩展: DRAFT → TESTING → ACTIVE → ARCHIVED
DB 新表: agent_blueprints, agent_blueprint_skills, agent_blueprint_tool_bindings

- [ ] TDD 实现 Blueprint 值对象
- [ ] Agent 状态机 +TESTING 状态
- [ ] ORM + 迁移
- [ ] ActiveAgentInfo +workspace_path +runtime_arn +workspace_s3_uri
- [ ] Commit `feat(agents): Agent Blueprint 数据模型 + TESTING 状态`

### Task 5: WorkspaceManager — 工作目录 + S3 上传

**Files:**
- Create: `backend/src/modules/agents/application/interfaces/workspace_manager.py`
- Create: `backend/src/modules/agents/infrastructure/external/workspace_manager.py`
- Test: `tests/modules/agents/unit/infrastructure/test_workspace_manager.py`

核心方法:
- `create_workspace(agent_id, blueprint)` → 本地目录 (CLAUDE.md + skills/ + .claude/)
- `upload_to_s3(workspace_path, agent_id)` → S3 URI
- `update_workspace(agent_id, blueprint)` → 重新生成 + 重新上传

- [ ] TDD 实现目录生成 + 版本化复制
- [ ] TDD 实现 S3 打包上传
- [ ] Commit `feat(agents): WorkspaceManager 工作目录 + S3 同步`

### Task 6: AgentRuntimeManager — Runtime 生命周期

**Files:**
- Create: `backend/src/modules/agents/application/interfaces/agent_runtime_manager.py`
- Create: `backend/src/modules/agents/infrastructure/external/agentcore_runtime_manager.py`
- Test: `tests/modules/agents/unit/infrastructure/test_agentcore_runtime_manager.py`

IAgentRuntimeManager: provision / update_workspace / deprovision
使用 bedrock-agentcore SDK 的 create/delete_agent_runtime API

- [ ] TDD 实现 Runtime 创建/销毁 (mock agentcore client)
- [ ] Commit `feat(agents): AgentRuntimeManager — Runtime 动态创建/销毁`

### Task 7: Agent 上线/下线 服务编排

**Files:**
- Modify: `backend/src/modules/agents/application/services/agent_service.py`
- Create: `backend/src/modules/agents/api/schemas/requests.py` (+StartTestingRequest)
- Modify: `backend/src/modules/agents/api/endpoints.py` (+start-testing, +go-live, +take-offline)
- Test: 集成测试

新端点:
| 方法 | 路径 | 功能 | 状态转换 |
|------|------|------|---------|
| POST | /agents/{id}/start-testing | 开始测试 | DRAFT → TESTING (创建 Runtime) |
| POST | /agents/{id}/go-live | 上线 | TESTING → ACTIVE |
| POST | /agents/{id}/take-offline | 下线 | ACTIVE → ARCHIVED (销毁 Runtime) |

AgentService.start_testing() 编排:
1. 校验 DRAFT 状态 + Blueprint 存在
2. WorkspaceManager.upload_to_s3()
3. AgentRuntimeManager.provision()
4. 保存 runtime_arn 到 Blueprint
5. Agent → TESTING

- [ ] TDD 实现上线/下线服务编排
- [ ] API 端点
- [ ] 集成测试 (mock RuntimeManager)
- [ ] Commit `feat(agents): Agent 上线/下线 API + Runtime 生命周期编排`

### Task 8: Execution 三模式路由 + agent_entrypoint S3 同步

**Files:**
- Modify: `backend/src/modules/execution/application/services/execution_service.py`
- Modify: `backend/src/modules/agents/infrastructure/services/agent_querier_impl.py`
- Modify: `backend/src/agent_entrypoint.py` (+S3 Workspace 同步)
- Test: 单元 + 集成测试

三模式路由:
```python
if agent_info.runtime_arn:     # TESTING/ACTIVE → 专属 Runtime
elif agent_info.workspace_path: # DRAFT → 本地 cwd
else:                           # V1 兼容 → 内联 system_prompt
```

agent_entrypoint.py: 启动时从 WORKSPACE_S3_URI 下载 Workspace

- [ ] TDD 实现路由切换
- [ ] agent_entrypoint.py S3 同步
- [ ] 全量 execution 测试确认无回归
- [ ] Commit `feat(execution): 三模式路由 + agent_entrypoint S3 Workspace 同步`

---

## M17-B: Builder V2 (3-4 周, 5 Tasks)

### Task 9: Builder AI SOP 引导式对话策略

**Files:**
- Create: `backend/src/modules/builder/infrastructure/external/builder_prompts.py`
- Modify: `backend/src/modules/builder/infrastructure/external/claude_builder_adapter.py`
- Modify: `backend/src/modules/builder/application/interfaces/builder_llm_service.py`

Builder AI 输出从 JSON 配置变为 SKILL.md + CLAUDE.md 内容

- [ ] 编写 SOP 引导式 system prompt
- [ ] 重写 Adapter (多轮 + 平台感知 + SKILL.md 输出)
- [ ] Commit `feat(builder): SOP 引导式 Builder AI`

### Task 10: BuilderService V2 — 工作目录 + Runtime 触发

**Files:**
- Modify: `backend/src/modules/builder/application/services/builder_service.py`
- Modify: `backend/src/modules/builder/domain/entities/builder_session.py`

confirm_session 新流程:
1. 解析 LLM 输出为 SKILL.md + CLAUDE.md + Guardrails
2. ISkillFileManager 保存 Skill → DB 记录
3. 创建 Blueprint + WorkspaceManager 创建工作目录
4. IAgentCreator 创建 Agent (DRAFT + Blueprint)

新增 start_testing() 调用: 触发 Agent 上线流程

- [ ] TDD 实现新 BuilderService
- [ ] Commit `feat(builder): BuilderService V2 输出工作目录 + Runtime 触发`

### Task 11: 前端 — 蓝图预览 + Skill 卡片

**Files:**
- Modify: `frontend/src/features/builder/ui/BuilderPreview.tsx`
- Create: `frontend/src/features/builder/ui/SkillCard.tsx`
- Create: `frontend/src/features/builder/ui/ToolSelector.tsx`
- Modify: `frontend/src/features/builder/api/types.ts`
- Modify: `frontend/src/features/builder/model/store.ts`

预览: 角色卡片 + 技能卡片 + 工具卡片 + 护栏规则 + 记忆开关

- [ ] 实现 UI 组件 + 测试
- [ ] Commit `feat(builder): 蓝图预览 UI`

### Task 12: 前端 — 多轮对话 + 测试沙盒 + 上线流程

**Files:**
- Modify: `frontend/src/features/builder/ui/BuilderChat.tsx`
- Create: `frontend/src/features/builder/ui/TestSandbox.tsx`
- Modify: `frontend/src/features/builder/ui/BuilderActions.tsx`
- Modify: `frontend/src/pages/builder/index.tsx`

阶段感知按钮:
| Phase | 按钮 |
|-------|------|
| input | [开始生成] |
| configure | [继续调整] [开始测试 →] |
| testing | [测试对话面板] [上线发布 ✓] |

测试沙盒: 路由到专属 Runtime 的真实对话 (非 mock)

- [ ] 实现多轮对话 + 测试沙盒 + 阶段按钮
- [ ] Commit `feat(builder): 多轮对话 + 测试沙盒 + 上线流程`

### Task 13: CDK — S3 存储桶 + EFS

**Files:**
- Create: `infra/lib/stacks/storage-stack.ts`
- Modify: `infra/lib/stacks/compute-stack.ts` (EFS 挂载)
- Modify: `infra/bin/app.ts`
- Test: `test/stacks/storage-stack.test.ts`

S3 Workspace 桶 + EFS Skill Library + ECS 挂载

- [ ] TDD 实现 Storage Stack
- [ ] 部署 Dev 环境
- [ ] Commit `feat(infra): S3 Workspace 存储桶 + EFS Skill Library`

---

## M17-C: 迁移 + 运营 (1-2 周, 2 Tasks)

### Task 14: 存量迁移 + Templates 升级

- [ ] 迁移脚本: 现有 Agent → workspace + Blueprint
- [ ] Templates 升级: 模板包含预置 Skill 目录

### Task 15: 全量质量检查 + 监控

- [ ] 后端: ruff + mypy + pytest (≥85% 覆盖率)
- [ ] 前端: lint + test
- [ ] 架构合规测试
- [ ] CloudWatch 面板: 每个 Runtime 的 CPU/内存/调用量
- [ ] Runtime 成本治理: ARCHIVED 自动销毁

---

## 设计决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| Skill 存储 | 文件系统 SKILL.md | Claude Code 运行时原生加载 |
| 元信息存储 | 数据库 skills 表 | 平台管理: 搜索、权限、审计 |
| Blueprint 存储 | DB agent_blueprints 表 + S3 workspace | DB 存结构化元信息, S3 存打包的运行目录 |
| Runtime 模型 | **每 Agent 独立 Runtime** | 隔离性 + 测试即生产 |
| Runtime 创建时机 | **TESTING 阶段** | 测试环境 = 生产环境, 消除环境差异风险 |
| Workspace 同步 | S3 下载 (容器启动时) | AgentCore Runtime 不支持 EFS 挂载 |
| 执行路由 | 三模式 (专属Runtime / 本地cwd / V1兼容) | 向后兼容 + 渐进迁移 |
| Agent 状态机 | DRAFT→TESTING→ACTIVE→ARCHIVED | TESTING 绑定 Runtime 创建, ARCHIVED 绑定 Runtime 销毁 |
