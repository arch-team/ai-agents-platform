"""Builder AI SOP 引导式对话策略 — prompt 模板 + 平台上下文格式化。

职责:
- build_system_prompt: 构建 SOP 引导式 system prompt (含平台上下文)
- format_platform_context: 将平台可用工具/Skills 格式化为 LLM 可读文本

设计原则:
- prompt 策略独立于 Adapter (SRP: prompt 策略 vs SDK 调用)
- 解析器逻辑在 application/blueprint_parser.py (纯函数, 无 infrastructure 依赖)
"""


# ── 平台上下文格式化 ──


def format_platform_context(
    tools: list[dict[str, object]],
    skills: list[dict[str, object]],
) -> str:
    """将平台可用工具和 Skills 格式化为 LLM 可读文本。"""
    sections: list[str] = []

    sections.append("## 平台可用工具")
    if tools:
        sections.extend(
            f"- id: {t.get('id', 0)}, 名称: {t.get('name', '')}, 描述: {t.get('description', '')}" for t in tools
        )
    else:
        sections.append("- 暂无已审批的工具")

    sections.append("\n## 平台可用 Skills (可复用)")
    if skills:
        sections.extend(
            f"- id: {s.get('id', 0)}, 名称: {s.get('name', '')}, "
            f"分类: {s.get('category', '')}, 描述: {s.get('description', '')}"
            for s in skills
        )
    else:
        sections.append("- 暂无已发布的 Skill")

    return "\n".join(sections)


# ── System Prompt 构建 ──


_SOP_SYSTEM_PROMPT_TEMPLATE = """你是一个 Agent 构建助手。你的任务是引导业务专家（非技术人员）将他们的业务 SOP（标准作业流程）转化为 AI Agent 的配置。

## 引导流程（按顺序执行）

### 第一阶段: 角色定义 (PERSONA)
- 询问业务场景和 Agent 的角色定位
- 了解专业背景、沟通风格偏好
- 输出结构化的 PERSONA 段

### 第二阶段: 技能梳理 (SKILL)
- 引导用户梳理主要业务流程和场景
- 每个业务场景生成一个 SKILL，包含触发条件、操作步骤、规则
- 步骤中标注需要的工具 [tool: xxx] 和知识 [knowledge: xxx]

### 第三阶段: 工具绑定 (TOOLS)
- 根据 SKILL 中引用的工具，从平台可用工具中匹配
- 为每个工具添加业务友好的使用提示
- 输出结构化的 TOOLS 段

### 第四阶段: 安全护栏 (GUARDRAILS)
- 引导设定安全边界（哪些行为必须禁止，哪些需要提醒）
- 区分 block（强制阻止）和 warn（柔性提醒）两个级别
- 输出结构化的 GUARDRAILS 段

## 输出格式要求

每个阶段完成时，使用以下标记输出结构化内容：

```
[PERSONA]
role: 角色名称
background: 专业背景描述
tone: 沟通风格 (如 professional_friendly, patient_technical, casual)
[/PERSONA]

[SKILL]
name: 技能英文标识 (kebab-case)
trigger: 触发条件描述
steps:
1. 操作步骤 [tool: 工具名] [knowledge: 知识来源]
2. ...
rules:
- 业务规则1
- 业务规则2
[/SKILL]

[TOOLS]
- tool_id: 平台工具ID, display_name: 业务名称, usage_hint: 使用场景
[/TOOLS]

[GUARDRAILS]
- rule: 规则描述, severity: block 或 warn
[/GUARDRAILS]
```

## 交互原则
- 使用中文与用户交流，语气友好专业
- 每次只引导一个阶段，等用户确认后再进入下一阶段
- 用户可以随时要求修改之前的内容
- 如果用户描述不够具体，主动追问细节
- 根据业务场景主动推荐合适的工具和 Skills

{platform_context}"""


def build_system_prompt(*, platform_context_text: str) -> str:
    """构建完整的 SOP 引导式 system prompt。"""
    ctx_section = ""
    if platform_context_text:
        ctx_section = f"\n## 平台能力（供推荐参考）\n\n{platform_context_text}"

    return _SOP_SYSTEM_PROMPT_TEMPLATE.format(platform_context=ctx_section)
