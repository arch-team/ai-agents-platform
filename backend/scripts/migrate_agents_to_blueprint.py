"""存量 Agent 迁移脚本 — 为 ACTIVE Agent 创建 Blueprint + workspace 目录。

使用方式:
    uv run python -m scripts.migrate_agents_to_blueprint [--dry-run] [--workspace-root /data/agent-workspaces]

说明:
    - 遍历所有 ACTIVE Agent (无 Blueprint 的旧模式)
    - 从 system_prompt 提取角色信息，生成 CLAUDE.md
    - 从 AgentConfig.tool_ids 生成 .claude/settings.json
    - 在 agent_blueprints 表创建记录
    - 生成 workspace 目录结构
    - 此迁移是可选的: 旧 Agent 通过执行路由模式 3 (V1 兼容) 继续正常工作

注意:
    - 脚本幂等: 已有 Blueprint 的 Agent 自动跳过
    - --dry-run 模式只输出计划，不执行写入
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="存量 Agent → Blueprint 迁移")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只输出迁移计划，不执行写入",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path("/data/agent-workspaces"),
        help="Agent workspace 根目录 (默认: /data/agent-workspaces)",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default="",
        help="数据库连接 URL (默认: 从环境变量构建)",
    )
    return parser.parse_args()


def build_database_url() -> str:
    """从环境变量构建数据库连接 URL (与 Settings 逻辑一致)。"""
    import os

    host = os.environ.get("DATABASE_HOST", "localhost")
    port = os.environ.get("DATABASE_PORT", "3306")
    user = os.environ.get("DATABASE_USER", "root")
    password = os.environ.get("DATABASE_PASSWORD", "")
    db_name = os.environ.get("DATABASE_NAME", "ai_agents_platform")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"


def generate_claude_md(agent_name: str, system_prompt: str) -> str:
    """从 Agent 的 system_prompt 生成 CLAUDE.md。"""
    lines = [f"# {agent_name}"]
    if system_prompt.strip():
        lines.append("")
        lines.append(system_prompt.strip())
    return "\n".join(lines)


def generate_settings_json(tool_ids: list[int]) -> str:
    """从 tool_ids 生成 .claude/settings.json (工具引用占位)。"""
    settings: dict[str, object] = {
        "tools": [{"id": tid} for tid in tool_ids],
    }
    return json.dumps(settings, ensure_ascii=False, indent=2)


def create_workspace(
    workspace_root: Path, agent_id: int, agent_name: str, system_prompt: str, tool_ids: list[int],
) -> Path:
    """为单个 Agent 创建 workspace 目录。"""
    workspace = workspace_root / str(agent_id)
    workspace.mkdir(parents=True, exist_ok=True)

    # CLAUDE.md
    claude_md = generate_claude_md(agent_name, system_prompt)
    (workspace / "CLAUDE.md").write_text(claude_md, encoding="utf-8")

    # skills/ (空目录，旧 Agent 无 Skill)
    (workspace / "skills").mkdir(exist_ok=True)

    # .claude/settings.json
    claude_dir = workspace / ".claude"
    claude_dir.mkdir(exist_ok=True)
    settings = generate_settings_json(tool_ids)
    (claude_dir / "settings.json").write_text(settings, encoding="utf-8")

    return workspace


def main() -> None:
    args = parse_args()

    # 延迟导入 — 避免无数据库时脚本无法启动
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        print("错误: 需要安装 sqlalchemy 和 pymysql")
        print("  uv add sqlalchemy pymysql")
        sys.exit(1)

    db_url = args.database_url or build_database_url()

    print(f"{'[DRY RUN] ' if args.dry_run else ''}存量 Agent → Blueprint 迁移")
    print(f"  数据库: {db_url.split('@')[-1] if '@' in db_url else '(检查连接)'}")
    print(f"  Workspace 根目录: {args.workspace_root}")
    print()

    engine = create_engine(db_url)

    with engine.connect() as conn:
        # 1. 查找所有 ACTIVE Agent (无 Blueprint)
        rows = conn.execute(
            text("""
                SELECT a.id, a.name, a.description, a.system_prompt, a.config
                FROM agents a
                LEFT JOIN agent_blueprints bp ON bp.agent_id = a.id
                WHERE a.status = 'active'
                  AND bp.id IS NULL
                ORDER BY a.id
            """),
        ).fetchall()

        if not rows:
            print("无需迁移: 所有 ACTIVE Agent 已有 Blueprint 或无 ACTIVE Agent")
            return

        print(f"发现 {len(rows)} 个待迁移 ACTIVE Agent:")
        for row in rows:
            print(f"  Agent #{row[0]}: {row[1]}")
        print()

        if args.dry_run:
            print("[DRY RUN] 以上 Agent 将被迁移，退出。")
            return

        # 2. 逐个迁移
        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        migrated = 0

        for row in rows:
            agent_id, agent_name, description, system_prompt, config_json = row

            # 解析 config JSON
            try:
                config = json.loads(config_json) if config_json else {}
            except json.JSONDecodeError:
                config = {}
            tool_ids: list[int] = config.get("tool_ids", [])

            # 创建 workspace
            workspace = create_workspace(
                args.workspace_root,
                agent_id,
                agent_name,
                system_prompt or "",
                tool_ids,
            )

            # 插入 agent_blueprints 记录
            persona_config = json.dumps(
                {
                    "role": agent_name,
                    "background": description or "",
                    "tone": "",
                },
                ensure_ascii=False,
            )
            model_config = json.dumps(
                {k: config.get(k) for k in ("model_id", "temperature", "max_tokens", "top_p") if k in config},
                ensure_ascii=False,
            )

            conn.execute(
                text("""
                    INSERT INTO agent_blueprints
                        (agent_id, version, status, persona_config, memory_config,
                         guardrails, model_config_json, knowledge_base_ids,
                         workspace_path, runtime_arn, workspace_s3_uri,
                         created_at, updated_at)
                    VALUES
                        (:agent_id, 1, 'active', :persona, '{}',
                         '[]', :model_cfg, '[]',
                         :ws_path, '', '',
                         :now, :now)
                """),
                {
                    "agent_id": agent_id,
                    "persona": persona_config,
                    "model_cfg": model_config,
                    "ws_path": str(workspace),
                    "now": now,
                },
            )

            # 更新 Agent 的 blueprint_id (在同一事务中查询刚插入的 id)
            bp_row = conn.execute(
                text("SELECT id FROM agent_blueprints WHERE agent_id = :aid"),
                {"aid": agent_id},
            ).fetchone()

            if bp_row:
                conn.execute(
                    text("UPDATE agents SET blueprint_id = :bpid WHERE id = :aid"),
                    {"bpid": bp_row[0], "aid": agent_id},
                )

            migrated += 1
            print(f"  ✓ Agent #{agent_id} ({agent_name}) → Blueprint + workspace 已创建")

        conn.commit()
        print(f"\n迁移完成: {migrated}/{len(rows)} 个 Agent 成功迁移")


if __name__ == "__main__":
    main()
