# 集成配置

## 环境

| 环境 | 用途 | URL |
|------|------|-----|
| dev | 开发测试 | （待配置） |
| prod | 正式环境 | （待配置） |

## CI/CD

- **工具**：GitHub Actions
- **触发方式**：push (dev) / manual approval (prod)
- **配置文件**：`.github/workflows/`
<!-- source: auto-detect -->

## 发布审批

- **模式**：混合 — dev 自动部署，prod 手动审批

## 外部同步

- **GitHub 仓库**：arch-team/ai-agents-platform
- **同步状态**：待配置（运行 `/pace-sync setup` 启用）
