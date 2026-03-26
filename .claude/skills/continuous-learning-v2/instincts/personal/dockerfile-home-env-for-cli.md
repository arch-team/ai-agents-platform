---
id: dockerfile-home-env-for-cli
trigger: "when running Node.js CLI binary in Docker container as non-root user"
confidence: 0.8
domain: "infrastructure"
source: "session-observation-2026-02-28"
---

# Docker 非 root 用户必须显式设置 HOME 环境变量

## Action
`useradd --create-home` 创建了 home 目录但不设置 `HOME` 环境变量。
Node.js CLI (如 Claude Code) 通过 `os.homedir()` 查找 `$HOME`，默认 `/root` 无权限写入。
必须 `ENV HOME=/home/appuser` + `mkdir -p $HOME/.claude && chown appuser`。

## Evidence
- 2026-02-28: in_process 模式 CLI 启动失败，ProcessTransport not ready
- Dockerfile 有 useradd --create-home 但无 ENV HOME
- 添加后 CLI 正常启动，Teams 执行 5s 完成
