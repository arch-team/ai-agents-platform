# ADR-010: Agent Blueprint 架构 — 文件系统原生 Skill + 工作目录 + 独立 Runtime

> **状态**: 提议 (Proposed)
> **日期**: 2026-04-04 (v3: 独立 Runtime 生命周期 + TESTING 阶段创建)
> **决策者**: 架构团队
> **关联**: ADR-006 (Agent 框架选型), M17 (智能协作引擎)

---

## 1. 背景与问题

### 1.1 核心场景

业务专家（售后主管、客服经理）通过 Builder 将领域知识（SOP、业务规则）转化为 Agent，发布给最终用户。

### 1.2 当前问题

Agent 领域知识全部在 `system_prompt: str` 中，无法结构化、无法复用、无法被 Builder 分段引导构建。

### 1.3 关键约束 — Claude Code 的 Skill 运行模型

参考 enterprise-architect Plugin 的实际运行方式（`skills/ddd/SKILL.md`），Claude Code 运行时原生支持：

```
Plugin/Agent 工作目录/
├── CLAUDE.md              ← 运行时自动加载为 system prompt
├── skills/                ← 运行时自动扫描，frontmatter 常驻内存
│   └── {skill-name}/
│       ├── SKILL.md       ← 用户意图匹配时动态加载
│       └── references/    ← Skill 执行中按需读取
└── .claude/
    └── settings.json      ← MCP servers 等运行时配置
```

**Skill 是文件系统中的目录，不是数据库中的 JSON。** Claude Code 通过扫描文件系统发现和加载 Skills。

### 1.4 已有基础设施

SDK 和 execution 模块**已支持** `cwd` 参数：

```python
# ClaudeAgentOptions (SDK)
cwd: str | Path | None = None       # ← 已支持
system_prompt: str | SystemPromptPreset | SystemPromptFile | None = None
plugins: list[SdkPluginConfig] = []  # ← 已支持 Plugin 加载

# AgentRequest (execution 模块)
cwd: str = ""  # Agent 工作目录 ← 已定义

# ClaudeAgentAdapter (已实现)
if request.cwd:
    kwargs["cwd"] = request.cwd      # ← 已实现传递
```

---

## 2. 决策

### 2.1 Agent = 一个可被 Claude Code 直接运行的工作目录

每个 Agent 对应一个文件系统工作目录。Blueprint 的元信息存数据库（检索、权限、审计），Skill 内容存文件系统（Claude Code 运行时消费）。

### 2.2 Skill 存文件系统，元信息存数据库

```
文件系统 (Skill 真实内容 — Claude Code 消费)
skill-library/published/{skill-name}/SKILL.md + references/

数据库 (元信息索引 — 平台管理消费)
skills 表: id, name, status, creator_id, version, file_path, usage_count
```

### 2.3 不需要"编译" — Claude Code 原生加载

~~Blueprint → 编译 → system_prompt~~ (否决)

正确路径：
1. Builder 生成 CLAUDE.md + 选择 Skills + 配置 MCP tools
2. 写入 Agent 工作目录
3. 执行时传入 `cwd` → Claude Code 自动发现 CLAUDE.md 和 skills/

---

## 3. 架构设计

### 3.1 存储分层

```
┌────────────────────────────────────────────────────────────────┐
│               文件系统 — Claude Code 运行时消费                   │
│                                                                │
│  {WORKSPACE_ROOT}/                                             │
│  ├── skill-library/             ← 平台级 Skill 库 (已发布)      │
│  │   ├── return-processing/                                    │
│  │   │   ├── SKILL.md                                          │
│  │   │   └── references/                                       │
│  │   │       ├── _index.yml                                    │
│  │   │       └── policy-guide.md                               │
│  │   ├── order-inquiry/                                        │
│  │   └── complaint-handling/                                   │
│  │                                                             │
│  └── agent-workspaces/          ← 每个 Agent 的运行环境         │
│      └── {agent-id}/                                           │
│          ├── CLAUDE.md          ← Persona + 行为规则 + 护栏     │
│          ├── skills/            ← 版本化复制自 skill-library      │
│          │   ├── return-processing -> ../../skill-library/...  │
│          │   └── order-inquiry -> ../../skill-library/...      │
│          └── .claude/                                          │
│              └── settings.json  ← MCP tools 配置               │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                           │
                           │ 元信息索引
                           ▼
┌────────────────────────────────────────────────────────────────┐
│              数据库 — 平台管理消费                                │
│                                                                │
│  skills 表                                                     │
│  ├── id, name, description, category                           │
│  ├── trigger_description       (触发条件文本, 用于搜索和展示)     │
│  ├── status                    (draft | published | archived)  │
│  ├── creator_id, version, usage_count                          │
│  ├── file_path                 (指向 skill-library 中的目录)    │
│  └── created_at, updated_at                                    │
│                                                                │
│  agent_blueprints 表                                           │
│  ├── id, agent_id, version                                     │
│  ├── persona_config JSON       ({role, background, tone})      │
│  ├── memory_config JSON        ({enabled, strategy, retain})   │
│  ├── guardrails JSON           ([{rule, severity}])            │
│  ├── model_config JSON         ({model_id, temperature, ...})  │
│  ├── knowledge_base_ids JSON   ([1, 2])                        │
│  ├── workspace_path            (agent-workspaces/{agent-id})   │
│  └── status, created_at, updated_at                            │
│                                                                │
│  agent_blueprint_skills 关联表                                  │
│  ├── blueprint_id, skill_id    (多对多, 可查询引用关系)          │
│  └── sort_order                                                │
│                                                                │
│  agent_blueprint_tool_bindings 表                               │
│  ├── blueprint_id, tool_id                                     │
│  ├── display_name, usage_hint  (业务友好描述)                    │
│  └── sort_order                                                │
│                                                                │
│  agents 表 (演进)                                               │
│  ├── ... (现有字段保留)                                          │
│  ├── blueprint_id FK           (引用 agent_blueprints)          │
│  └── system_prompt             (保留, 向后兼容无 Blueprint 的 Agent)│
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent 工作目录的生成规则

当 Blueprint 创建或更新时，`WorkspaceManager` 同步生成工作目录：

```python
class WorkspaceManager:
    """Agent 工作目录管理器 — 从 Blueprint 生成 Claude Code 可运行的目录。"""

    def __init__(self, workspace_root: Path, skill_library_root: Path) -> None:
        self._workspace_root = workspace_root
        self._skill_library_root = skill_library_root

    async def create_workspace(self, agent_id: int, blueprint: AgentBlueprintDTO) -> Path:
        """根据 Blueprint 创建 Agent 工作目录。"""
        workspace = self._workspace_root / str(agent_id)
        workspace.mkdir(parents=True, exist_ok=True)

        # 1. 生成 CLAUDE.md (Persona + 护栏)
        claude_md = self._render_claude_md(blueprint)
        (workspace / "CLAUDE.md").write_text(claude_md, encoding="utf-8")

        # 2. 链接 Skills (版本化复制自 skill-library)
        skills_dir = workspace / "skills"
        skills_dir.mkdir(exist_ok=True)
        for skill_path in blueprint.skill_paths:
            link = skills_dir / Path(skill_path).name
            if not link.exists():
                link.symlink_to(self._skill_library_root / skill_path)

        # 3. 生成 .claude/settings.json (MCP tools 配置)
        claude_dir = workspace / ".claude"
        claude_dir.mkdir(exist_ok=True)
        settings = self._render_settings(blueprint)
        (claude_dir / "settings.json").write_text(
            json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        return workspace

    def _render_claude_md(self, blueprint: AgentBlueprintDTO) -> str:
        """生成 CLAUDE.md — Agent 的角色定义和行为规则。"""
        sections = []
        p = blueprint.persona
        sections.append(f"# {p.role}\n\n{p.background}")
        if p.tone:
            sections.append(f"\n## 沟通风格\n{p.tone}")
        if blueprint.guardrails:
            sections.append("\n## 安全边界（必须遵守）")
            for g in blueprint.guardrails:
                prefix = "⛔" if g.severity == "block" else "⚠️"
                sections.append(f"- {prefix} {g.rule}")
        if blueprint.memory_config.enabled and blueprint.memory_config.retain_fields:
            sections.append(f"\n## 记忆策略\n请记住: {', '.join(blueprint.memory_config.retain_fields)}")
        return "\n".join(sections)
```

### 3.3 执行链路 — 最小改动

```
最终用户发消息
    │
    ▼
ExecutionService._prepare_for_send()
    │  agent_info = IAgentQuerier.get_active_agent(agent_id)
    │  新增: workspace_path = agent_info.workspace_path  ← 从 Blueprint 读取
    │
    ▼
ExecutionService._build_agent_request()
    │  AgentRequest(
    │      prompt = 用户消息,
    │      cwd = workspace_path,        ← 设置工作目录 (已有字段!)
    │      system_prompt = "",           ← 不再内联, Claude Code 从 CLAUDE.md 读取
    │      tools = [...],                ← MCP 工具 (现有逻辑保持)
    │      ...
    │  )
    │
    ▼
ClaudeAgentAdapter._build_options()
    │  ClaudeAgentOptions(
    │      cwd = request.cwd,            ← 已实现!
    │      # system_prompt 不传或传空 → Claude Code 自动读取 cwd/CLAUDE.md
    │      # skills/ 自动被扫描和加载
    │  )
    │
    ▼
claude_agent_sdk.query(prompt, options)
    │  Claude Code 运行时:
    │  1. 读取 {cwd}/CLAUDE.md → 角色 + 规则
    │  2. 扫描 {cwd}/skills/ → frontmatter 常驻内存
    │  3. 意图匹配 → 动态加载 SKILL.md body
    │  4. MCP 调用工具
```

**改动范围**：

| 组件 | 改动 | 说明 |
|------|------|------|
| `ActiveAgentInfo` | +1 字段 | `workspace_path: str = ""` |
| `AgentQuerierImpl` | +1 行 | 读取 blueprint.workspace_path |
| `ExecutionService._build_agent_request` | 修改 1 处 | `cwd=workspace_path`, `system_prompt` 逻辑调整 |
| `AgentRequest` | 不变 | `cwd` 已存在 |
| `ClaudeAgentAdapter` | 不变 | `cwd` 传递已实现 |

### 3.4 Skill 生命周期

```
业务专家在 Builder 中描述流程
    │
    ▼
Builder AI 生成 SKILL.md + references/
    │
    ▼
保存到临时目录 (draft)
    │  DB: skills 表 INSERT (status=draft, file_path=tmp)
    │
    ▼
业务专家在 Builder 中预览和编辑 Skill
    │
    ▼
发布 Skill
    │  1. 文件从临时目录移动到 skill-library/published/{name}/
    │  2. DB: skills 表 UPDATE (status=published, file_path=published/{name})
    │
    ▼
在 Builder 中选择 Skill 绑定到 Agent
    │  1. DB: agent_blueprint_skills INSERT
    │  2. 文件: agent-workspaces/{agent-id}/skills/{name} 版本化复制自 skill-library
    │
    ▼
Skill 更新 (新版本)
    │  1. 文件: skill-library/published/{name}/ 内容更新
    │  2. DB: skills 表 version++
    │  3. 版本化复制自动指向最新内容 (无需重新链接)
```

### 3.5 Agent 状态机 + 独立 Runtime 生命周期

每个上线的 Agent 拥有独立的 AgentCore Runtime 容器。Runtime 在 **TESTING 阶段创建**（测试环境 = 生产环境），ACTIVE 阶段复用，ARCHIVED 阶段销毁。

```
DRAFT (编辑中)
  │  Workspace 在本地文件系统构建
  │  无 Runtime, 无容器开销
  │  Builder 可用本地 SDK 快速预览 (cwd 模式)
  │
  ▼  业务专家点击"开始测试"

TESTING (测试中)
  │  1. WorkspaceManager 打包 Workspace → 上传 S3
  │  2. AgentRuntimeManager 创建专属 AgentCore Runtime
  │     runtime_name = f"agent_{agent_id}_{env}"
  │     环境变量: WORKSPACE_S3_URI, AGENT_ID, ENV_NAME
  │  3. Runtime 容器启动 → 从 S3 下载 Workspace → 就绪
  │  4. 业务专家用真实场景测试 (路由到专属 Runtime)
  │  5. 发现问题 → 修改 Skill → 重新同步 Workspace → 重启容器
  │
  ▼  验证通过, 点击"上线发布"

ACTIVE (上线)
  │  同一个 Runtime, 开放给最终用户
  │  无需重新创建容器 — 测试通过的即是生产运行的
  │
  ▼  业务调整 (Skill 更新)

ACTIVE (热更新)
  │  Workspace 重新打包上传 S3
  │  Runtime 容器滚动更新 (重新加载 Workspace)
  │
  ▼  下线归档

ARCHIVED (已归档)
     AgentRuntimeManager 销毁 Runtime → 释放计算资源
     Workspace S3 对象保留 (审计), 本地目录清理
```

#### Agent 状态扩展

```python
class AgentStatus(str, Enum):
    DRAFT = "draft"           # 编辑中, 无 Runtime
    TESTING = "testing"       # 测试中, 专属 Runtime 已创建
    ACTIVE = "active"         # 上线, 同一 Runtime 服务最终用户
    ARCHIVED = "archived"     # 已归档, Runtime 已销毁
```

#### AgentRuntimeManager 接口

```python
class IAgentRuntimeManager(ABC):
    """Agent Runtime 生命周期管理。"""

    @abstractmethod
    async def provision(self, agent_id: int, workspace_s3_uri: str) -> RuntimeInfo:
        """创建专属 AgentCore Runtime, 返回 runtime_arn + endpoint。"""

    @abstractmethod
    async def update_workspace(self, runtime_arn: str, workspace_s3_uri: str) -> None:
        """更新 Runtime 的 Workspace (Skill 变更 / 容器滚动更新)。"""

    @abstractmethod
    async def deprovision(self, runtime_arn: str) -> None:
        """销毁 Runtime, 释放资源。"""


@dataclass(frozen=True)
class RuntimeInfo:
    runtime_arn: str
    runtime_name: str
```

### 3.6 执行路由 — 三模式

```python
# ExecutionService — 根据 Agent 状态路由到不同执行模式
if agent_info.runtime_arn:
    # 模式 1: 专属 Runtime (TESTING / ACTIVE Agent)
    # 测试和生产用同一容器, 零环境差异
    adapter = AgentCoreRuntimeAdapter(runtime_arn=agent_info.runtime_arn)

elif agent_info.workspace_path:
    # 模式 2: 本地 SDK + cwd (DRAFT Agent, Builder 快速预览)
    # 用于 Builder 实时预览, 无需等待容器创建
    request.cwd = agent_info.workspace_path

else:
    # 模式 3: V1 兼容 (无 Blueprint 的旧 Agent)
    request.system_prompt = agent_info.system_prompt
```

### 3.7 向后兼容

已有 Agent（无 Blueprint, 无 Runtime）通过模式 3 继续正常工作。无需迁移即可共存。

#### ActiveAgentInfo 扩展

```python
@dataclass(frozen=True)
class ActiveAgentInfo:
    # ... 现有字段保留 ...
    workspace_path: str = ""       # 本地工作目录 (DRAFT 预览用)
    runtime_arn: str = ""          # 专属 Runtime ARN (TESTING/ACTIVE)
    workspace_s3_uri: str = ""     # S3 Workspace URI (Runtime 同步用)
```

---

## 4. Skills 新模块

### 4.1 模块架构

```
backend/src/modules/skills/
├── __init__.py
├── api/
│   ├── endpoints.py              # CRUD + 发布
│   ├── dependencies.py
│   └── schemas/
├── application/
│   ├── dto/skill_dto.py
│   ├── interfaces/
│   │   └── skill_file_manager.py # 文件系统操作接口
│   └── services/skill_service.py
├── domain/
│   ├── entities/skill.py         # 元信息实体 (不含文件内容)
│   ├── value_objects/
│   │   └── skill_status.py       # DRAFT → PUBLISHED → ARCHIVED
│   ├── repositories/skill_repository.py
│   └── exceptions.py
└── infrastructure/
    ├── persistence/
    │   ├── models/skill_model.py
    │   └── repositories/skill_repository_impl.py
    ├── external/
    │   └── skill_file_manager_impl.py  # 文件系统操作实现
    └── services/
        └── skill_querier_impl.py       # ISkillQuerier 跨模块接口
```

### 4.2 Skill 实体 — 只存元信息

```python
class Skill(PydanticEntity):
    """Skill 元信息实体 — 内容在文件系统中。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500, default="")
    category: SkillCategory = SkillCategory.GENERAL
    trigger_description: str = Field(max_length=500, default="")
    status: SkillStatus = SkillStatus.DRAFT
    creator_id: int
    version: int = 1
    usage_count: int = 0
    file_path: str = ""  # 指向 skill-library 中的相对路径
```

### 4.3 ISkillFileManager — 文件系统操作抽象

```python
class ISkillFileManager(ABC):
    """Skill 文件系统操作接口 (Infrastructure 层实现)。"""

    @abstractmethod
    async def save_draft(self, skill_name: str, skill_md: str, references: dict[str, str]) -> str:
        """保存 Skill 草稿到临时目录，返回 file_path。"""

    @abstractmethod
    async def publish(self, draft_path: str, skill_name: str) -> str:
        """将草稿发布到 skill-library/published/，返回发布路径。"""

    @abstractmethod
    async def read_skill_md(self, file_path: str) -> str:
        """读取 SKILL.md 内容（Builder 预览用）。"""

    @abstractmethod
    async def link_to_workspace(self, skill_path: str, workspace_path: str) -> None:
        """在 Agent 工作目录中创建 Skill 版本化复制。"""
```

---

## 5. Builder V2 — 工作目录组装器 + Runtime 触发

Builder 的输出从 JSON 变为文件系统目录 + Runtime 生命周期操作：

```
Builder 引导对话 → 生成:
1. CLAUDE.md              (Persona + 规则 + 护栏)
2. skills/                (新建 SKILL.md 或引用已有 Skill)
3. .claude/settings.json  (MCP 工具配置)
4. DB 记录                (agent_blueprints + agent_blueprint_skills)

确认 → WorkspaceManager.create_workspace() → Agent DRAFT

开始测试 → WorkspaceManager.upload_to_s3()
         → AgentRuntimeManager.provision() → 专属 Runtime 创建
         → Agent TESTING (可在专属 Runtime 上真实测试)

上线 → Agent ACTIVE (同一 Runtime 开放给最终用户)

下线 → AgentRuntimeManager.deprovision() → Agent ARCHIVED
```

---

## 6. 部署与基础设施

### 6.1 存储分层

| 存储层 | 内容 | 环境 | 用途 |
|--------|------|------|------|
| 本地文件系统 | skill-library/ + agent-workspaces/ | Dev: 本地, Prod: EFS | Builder 编辑、DRAFT 预览 |
| **S3** | workspace.tar.gz (每个 Agent) | Dev + Prod | **AgentCore Runtime 启动时下载** |
| 数据库 | 元信息 (skills 表, agent_blueprints 表) | Dev + Prod | 平台管理、搜索、权限 |

### 6.2 Runtime 容器启动流程

```
AgentCore Runtime 容器启动
    │
    ├── 1. 读取环境变量 WORKSPACE_S3_URI
    │
    ├── 2. 从 S3 下载 workspace.tar.gz → /workspace/
    │      CLAUDE.md + skills/ + .claude/settings.json
    │
    ├── 3. 验证目录结构完整性
    │
    └── 4. 进入就绪状态, 等待 invoke 请求
          → agent_entrypoint.py 使用 cwd="/workspace/"
```

agent_entrypoint.py 需要增加启动时 S3 同步逻辑：

```python
# agent_entrypoint.py — 启动时 Workspace 同步
import boto3, tarfile, os

WORKSPACE_S3_URI = os.environ.get("WORKSPACE_S3_URI", "")
WORKSPACE_DIR = "/workspace"

def sync_workspace():
    """从 S3 下载并解压 Workspace。"""
    if not WORKSPACE_S3_URI:
        return  # 兼容无 Blueprint 的旧模式
    bucket, key = parse_s3_uri(WORKSPACE_S3_URI)
    s3 = boto3.client("s3")
    s3.download_file(bucket, key, "/tmp/workspace.tar.gz")
    with tarfile.open("/tmp/workspace.tar.gz") as tar:
        tar.extractall(WORKSPACE_DIR)

# 在 invoke handler 之前调用
sync_workspace()
```

### 6.3 CDK 变更

```typescript
// 1. S3 存储桶 — Workspace 持久化
const workspaceBucket = new s3.Bucket(this, 'AgentWorkspacesBucket', {
    bucketName: `${PROJECT_NAME}-workspaces-${envName}`,
    encryption: s3.BucketEncryption.S3_MANAGED,
    blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    enforceSSL: true,
    lifecycleRules: [{
        // 归档 Agent 的 workspace 90 天后移入低频存储
        transitions: [{ storageClass: s3.StorageClass.INFREQUENT_ACCESS, transitionAfter: cdk.Duration.days(90) }],
    }],
});

// 2. EFS — 本地文件系统 (ECS Web API 用, Builder 编辑用)
const skillLibraryFs = new efs.FileSystem(this, 'SkillLibraryEfs', {
    vpc, encrypted: true,
});

// 3. 共享 Runtime 保留 (DRAFT 预览 + V1 兼容)
// 已有 agentcore-stack.ts 中的 Runtime 继续作为共享 Runtime

// 4. 专属 Runtime 通过 AgentRuntimeManager (boto3 API) 动态创建
// 不在 CDK 中静态定义 — 每个 Agent 上线时通过 API 创建
```

### 6.4 AgentRuntimeManager 实现方式

```python
# 使用 bedrock-agentcore SDK 动态创建/管理 Runtime
class AgentCoreRuntimeManager(IAgentRuntimeManager):
    """通过 AgentCore API 动态管理 Agent Runtime。"""

    def __init__(self, agentcore_client, ecr_repo_uri: str, vpc_config: dict) -> None:
        self._client = agentcore_client
        self._ecr_repo_uri = ecr_repo_uri
        self._vpc_config = vpc_config

    async def provision(self, agent_id: int, workspace_s3_uri: str) -> RuntimeInfo:
        """创建专属 Runtime。"""
        runtime_name = f"agent_{agent_id}_{self._env}"
        response = self._client.create_agent_runtime(
            agentRuntimeName=runtime_name,
            agentRuntimeArtifact={"ecr": {"repositoryUri": self._ecr_repo_uri, "tag": "latest"}},
            networkConfiguration=self._vpc_config,
            environmentVariables={
                "WORKSPACE_S3_URI": workspace_s3_uri,
                "AGENT_ID": str(agent_id),
            },
        )
        return RuntimeInfo(
            runtime_arn=response["agentRuntimeArn"],
            runtime_name=runtime_name,
        )

    async def deprovision(self, runtime_arn: str) -> None:
        """销毁 Runtime。"""
        self._client.delete_agent_runtime(agentRuntimeArn=runtime_arn)
```

---

## 7. 实施策略 — M17 三阶段

### M17-A: 基础设施 (2-3 周)
- [ ] 新增 `skills` 模块 (元信息 CRUD + 文件系统操作)
- [ ] 新增 `agent_blueprints` + `agent_blueprint_skills` + `agent_blueprint_tool_bindings` 表
- [ ] `Agent` 状态机扩展: DRAFT → TESTING → ACTIVE → ARCHIVED
- [ ] 实现 `WorkspaceManager` (目录生成 + S3 上传 + 版本化复制)
- [ ] 实现 `IAgentRuntimeManager` (Runtime 创建/更新/销毁)
- [ ] `ActiveAgentInfo` 增加 `workspace_path`, `runtime_arn`, `workspace_s3_uri`
- [ ] 执行路由: 三模式路由逻辑 (专属 Runtime / 本地 cwd / V1 兼容)
- [ ] `agent_entrypoint.py` 增加 S3 Workspace 同步
- [ ] CDK: S3 Workspace 存储桶 + EFS Skill Library

### M17-B: Builder V2 (3-4 周)
- [ ] Builder AI 对话策略: SOP 引导 → 生成 SKILL.md + CLAUDE.md
- [ ] Builder 输出: workspace 目录 → DB Blueprint 记录
- [ ] "开始测试" 按钮: 触发 S3 上传 + Runtime 创建 + Agent → TESTING
- [ ] 测试沙盒: 路由到专属 Runtime 进行真实场景验证
- [ ] "上线发布" 按钮: Agent TESTING → ACTIVE (同一 Runtime)
- [ ] 前端: 蓝图预览 (Persona/Skills/Tools/Guardrails 卡片)
- [ ] 前端: Skill 选择器 (从 skill-library 选择已发布 Skill)

### M17-C: 迁移 + 运营 (1-2 周)
- [ ] 迁移工具: 现有 Agent → 生成 workspace + 创建 Blueprint
- [ ] Templates 升级: 模板包含预置 Skills 目录
- [ ] Agent Runtime 监控: CloudWatch 面板 (每个 Runtime 的 CPU/内存/调用量)
- [ ] Runtime 成本治理: ARCHIVED Agent 自动销毁 Runtime

---

## 8. 备选方案

| 方案 | 说明 | 评估 |
|------|------|------|
| A: Skill 存数据库 JSON | 所有内容在数据库 | ❌ 否决: Claude Code 无法从数据库加载 Skill |
| B: 编译 Blueprint → system_prompt | Blueprint 构建时编译为字符串 | ❌ 否决: 丢失渐进披露、无法动态加载 |
| **C: 文件系统 Skill + DB 元信息** | **Skill 在文件系统, 元信息在数据库** | **✅ 选择: 与 Claude Code 运行模型一致** |
| D: S3 对象存储 Skill | Skill 存 S3, 运行时下载 | ⚠️ 备选: 冷启动延迟, 适合 Serverless 场景 |

---

## 9. 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| **AgentCore Runtime 配额** | 每账户 Runtime 数量有限制 | 监控配额使用率; 及时销毁 ARCHIVED Agent 的 Runtime; 必要时申请提额 |
| **Runtime 创建延迟** | TESTING 转换需等待容器就绪 (~30-60s) | 前端展示创建进度; 异步创建 + 轮询状态 |
| **Runtime 成本** | 每个 TESTING/ACTIVE Agent 持续占用计算资源 | ARCHIVED 自动销毁; 非工作时间缩容; CloudWatch 成本告警 |
| S3 同步延迟 | Workspace 更新后容器需重启同步 | 滚动更新策略; workspace 包体积控制 (< 10MB) |
| 版本化复制安全 | 恶意 Skill 路径遍历 | `WorkspaceManager` 验证路径在 workspace_root 内 |
| Skill 并发写入 | 多人同时编辑同一 Skill | 文件级锁 + 版本号乐观并发控制 |
| **Skill 热更新影响范围** | 一个 Skill 被 N 个 Agent 引用, 更新需重启 N 个 Runtime | 异步通知 + 渐进式滚动更新; Agent 所有者确认后才更新 |
