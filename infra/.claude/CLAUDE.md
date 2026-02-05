---
version: 1.0.0
last_updated: 2026-02-04
cdk_version: ">=2.130.0"
node_version: ">=18.0.0"
---

# CLAUDE.md - AWS CDK 基础设施项目规范

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **注意**: 通用规范（响应语言、项目概述）请参考根目录 [../.claude/CLAUDE.md](../../.claude/CLAUDE.md)

---

## 技术栈

**核心**: AWS CDK 2.x | TypeScript 5+ | Node.js 18+

**测试**: Jest | CDK Assertions | CDK Nag

**工具**: pnpm (包管理) | ESLint | Prettier

---

## 开发命令

### 环境管理 (pnpm)

```bash
# 安装依赖
pnpm install

# 添加生产依赖
pnpm add <package>

# 添加开发依赖
pnpm add -D <package>

# 更新所有依赖
pnpm update
```

### CDK 命令

```bash
# 合成 CloudFormation 模板
pnpm cdk synth

# 查看变更 (diff)
pnpm cdk diff

# 部署到 AWS
pnpm cdk deploy

# 部署指定 Stack
pnpm cdk deploy <StackName>

# 部署所有 Stack
pnpm cdk deploy --all

# 销毁 Stack
pnpm cdk destroy <StackName>

# 列出所有 Stack
pnpm cdk list

# Bootstrap CDK (首次使用)
pnpm cdk bootstrap
```

### 代码质量

```bash
# 代码检查 (lint)
pnpm lint

# 代码检查并自动修复
pnpm lint --fix

# 格式化检查
pnpm format:check

# 格式化代码
pnpm format

# 类型检查
pnpm typecheck

# 一键运行所有检查
pnpm lint && pnpm format:check && pnpm typecheck
```

### 测试

```bash
# 运行所有测试
pnpm test

# 运行测试 + 覆盖率报告
pnpm test:coverage

# 监听模式
pnpm test:watch

# 运行特定测试文件
pnpm test lib/constructs/
```

---

## 核心原则

### Construct 设计原则

**核心原则**：分层抽象 + 安全默认 + 最小权限。

详细说明请参考 [rules/construct-design.md](rules/construct-design.md)

### TDD 工作流

本项目全面采用测试驱动开发 (TDD)。

**核心循环**:
```
1. 🔴 Red: 先写失败的测试
2. 🟢 Green: 编写最少代码使测试通过
3. 🔄 Refactor: 重构代码，保持测试通过
```

**测试分层策略**:

| 层级 | 覆盖内容 | 工具 |
|------|---------|------|
| **Unit** | Construct 配置、属性验证 | Jest + CDK Assertions |
| **Snapshot** | 模板结构稳定性 | Jest Snapshot |
| **Compliance** | 安全合规检查 | CDK Nag |

**测试诚信原则**: 切勿为让测试通过而伪造结果。测试失败 = 代码有问题，必须修复代码。

详细说明请参考 [rules/testing.md](rules/testing.md)

---

## 代码风格快速参考

### Props 设计

Props 接口设计规范见 [construct-design.md §1](rules/construct-design.md#1-props-接口设计)

**核心规则**: Props 属性必须使用 `readonly` 修饰

### 命名规范

| 元素 | 规范 | 示例 |
|------|------|------|
| Construct 类 | `PascalCase` | `ApiGatewayConstruct`, `VpcConstruct` |
| Stack 类 | `PascalCase` + `Stack` 后缀 | `NetworkStack`, `ComputeStack` |
| Props 接口 | `PascalCase` + `Props` 后缀 | `VpcConstructProps` |
| CDK ID | `PascalCase` | `'MainVpc'`, `'ApiGateway'` |
| 资源名称 | `kebab-case` | `'ai-platform-api'` |

### JSDoc 原则

```typescript
/**
 * API 网关 Construct - 提供统一的 REST API 入口。
 *
 * @remarks
 * 默认启用访问日志和 WAF 集成。
 */
export class ApiGatewayConstruct extends Construct {
  // ...
}
```

<!-- 代码风格规范已整合到 construct-design.md 等专题文档中 -->

---

## 项目结构

**架构模式**: CDK Construct 分层 (L1 → L2 → L3)

**核心分层**:
- **L1**: CloudFormation 资源 (Cfn* 前缀)
- **L2**: 高级 Construct (aws-* 模块)
- **L3**: 自定义 Construct (业务组合)

详细架构规范、Construct 结构模板请参考 [rules/architecture.md](rules/architecture.md)

**项目目录结构**: 详见 [rules/project-structure.md](rules/project-structure.md)

---

## 安全规范快速参考

**最小权限原则**: 使用 `grantRead()`, `grantWrite()` 等 Grant 方法。

**禁止**: 硬编码密钥、过宽 IAM 权限、公开 S3 Bucket。

速查表和检测命令详见 [rules/security.md](rules/security.md)

---

## 覆盖率要求

| 层级 | 最低覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| Constructs | 90% | 95% |
| Stacks | 85% | 90% |
| **整体** | **85%** | **90%** |

---

## 相关规范文档

| 文档 | 内容 |
|------|------|
| [PROJECT_CONFIG.ai-agents-platform.md](PROJECT_CONFIG.ai-agents-platform.md) | 项目特定配置 (Stack 列表、环境配置) |
| [PROJECT_CONFIG.template.md](PROJECT_CONFIG.template.md) | 项目配置模板 (可复用到其他项目) |
| [rules/architecture.md](rules/architecture.md) | CDK 架构规范 (Construct 分层) |
| [rules/project-structure.md](rules/project-structure.md) | 项目目录结构规范 |
| [rules/construct-design.md](rules/construct-design.md) | Construct 设计规范 |
| [rules/security.md](rules/security.md) | 安全规范 (IAM、Secrets) |
| [rules/testing.md](rules/testing.md) | 测试规范详细说明 |
| [rules/deployment.md](rules/deployment.md) | 部署规范 |
| [rules/cost-optimization.md](rules/cost-optimization.md) | 成本优化规范 |

---

## PR Review 检查清单

完整检查清单见 [rules/checklist.md](rules/checklist.md)

**预提交一键验证**:
```bash
pnpm lint && pnpm format:check && pnpm typecheck && pnpm cdk synth && pnpm test:coverage
```
