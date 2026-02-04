# 项目目录结构规范 (Project Structure)

> Claude 初始化或检查项目结构时优先查阅此文档

---

## 0. 速查卡片

### Monorepo 结构概览

```
ai-agents-platform/             # Monorepo 根目录
├── .claude/                    # 根级：通用规范
│   ├── CLAUDE.md               # 全局入口（语言、项目概述）
│   └── rules/
│       └── common.md           # 跨项目通用规则
├── backend/                    # 后端项目
├── frontend/                   # 前端项目
├── infra/                      # 基础设施项目 ← 当前位置
├── doc/                        # 全局文档
├── .gitignore                  # 根级 gitignore
└── README.md                   # 项目总说明
```

### Infra 目录结构

```
infra/                          # CDK 项目根目录
├── .claude/                    # Claude Code 上下文 (规范文档)
│   ├── CLAUDE.md               # 基础设施入口
│   ├── PROJECT_CONFIG.*.md
│   └── rules/                  # Infra 专用规则
├── bin/                        # CDK 应用入口
│   └── app.ts
├── lib/                        # 源代码
│   ├── constructs/             # 自定义 L3 Construct
│   │   ├── vpc/
│   │   │   ├── index.ts
│   │   │   ├── vpc.construct.ts
│   │   │   └── vpc.construct.test.ts
│   │   ├── aurora/
│   │   └── api-gateway/
│   ├── stacks/                 # Stack 定义
│   │   ├── network-stack.ts
│   │   ├── compute-stack.ts
│   │   └── api-stack.ts
│   └── config/                 # 配置和常量
│       ├── environments.ts
│       └── constants.ts
├── test/                       # 集成测试
│   ├── snapshot/               # 快照测试
│   └── compliance/             # CDK Nag 合规测试
├── cdk.json                    # CDK 配置
├── cdk.context.json            # CDK 上下文缓存 (git ignore)
├── jest.config.js              # Jest 配置
├── package.json                # 项目配置
├── pnpm-lock.yaml              # 依赖锁定
├── tsconfig.json               # TypeScript 配置
└── README.md                   # 基础设施说明
```

### 配置文件速查

| 文件 | 用途 | 必须 |
|------|------|:----:|
| `cdk.json` | CDK 应用配置 | ✅ |
| `package.json` | 项目和脚本配置 | ✅ |
| `tsconfig.json` | TypeScript 配置 | ✅ |
| `jest.config.js` | Jest 测试配置 | ✅ |
| `.eslintrc.cjs` | ESLint 配置 | 推荐 |
| `README.md` | 项目说明 | ✅ |

### 禁止事项

| 规则 | 说明 |
|------|------|
| ❌ bin/ 中放业务逻辑 | bin/app.ts 只做 Stack 组装 |
| ❌ Stack 中直接写资源 | 复杂资源应封装为 Construct |
| ❌ 硬编码账户/区域 | 使用 CDK Context 管理 |
| ❌ cdk.context.json 入版本控制 | 应在 .gitignore 中 |

---

## 1. 目录详解

### bin/ - 应用入口

```
bin/
└── app.ts                      # CDK 应用入口
```

**职责**: 创建 CDK App，实例化 Stack，配置环境

```typescript
// bin/app.ts
#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { NetworkStack } from '../lib/stacks/network-stack';
import { ComputeStack } from '../lib/stacks/compute-stack';
import { getEnvironmentConfig } from '../lib/config/environments';

const app = new cdk.App();
const envName = app.node.tryGetContext('env') || 'dev';
const envConfig = getEnvironmentConfig(app, envName);

// 创建 Stacks
const networkStack = new NetworkStack(app, `NetworkStack-${envName}`, {
  env: { account: envConfig.account, region: envConfig.region },
  vpcCidr: envConfig.vpcCidr,
});

const computeStack = new ComputeStack(app, `ComputeStack-${envName}`, {
  env: { account: envConfig.account, region: envConfig.region },
  vpc: networkStack.vpc,
});

computeStack.addDependency(networkStack);

app.synth();
```

### lib/constructs/ - 自定义 Construct

```
lib/constructs/
├── vpc/
│   ├── index.ts                # 导出入口
│   ├── vpc.construct.ts        # Construct 实现
│   └── vpc.construct.test.ts   # 单元测试
├── aurora/
│   ├── index.ts
│   ├── aurora.construct.ts
│   └── aurora.construct.test.ts
└── api-gateway/
    └── ...
```

**命名规范**:
- 目录名: `kebab-case`
- 文件名: `{name}.construct.ts`
- 类名: `PascalCase` + `Construct` 后缀

### lib/stacks/ - Stack 定义

```
lib/stacks/
├── network-stack.ts
├── compute-stack.ts
├── database-stack.ts
└── api-stack.ts
```

**命名规范**:
- 文件名: `{name}-stack.ts`
- 类名: `PascalCase` + `Stack` 后缀

### lib/config/ - 配置管理

```
lib/config/
├── environments.ts             # 环境配置
└── constants.ts                # 常量定义
```

### test/ - 测试文件

```
test/
├── constructs/                 # Construct 测试
│   ├── vpc.construct.test.ts
│   └── aurora.construct.test.ts
├── stacks/                     # Stack 测试
│   └── network-stack.test.ts
├── snapshot/                   # 快照测试
│   └── main.test.ts
└── compliance/                 # 合规测试
    └── cdk-nag.test.ts
```

---

## 2. 跨文档引用

| 内容 | 参考文档 |
|------|---------|
| Construct 分层规则 | [architecture.md](architecture.md) §0.1 |
| Construct 设计模式 | [construct-design.md](construct-design.md) |
| 测试目录结构 | [testing.md](testing.md) §1 |
| 根级通用规范 | [../../.claude/CLAUDE.md](../../../.claude/CLAUDE.md) |

---

## 3. 新项目初始化检查清单

### 目录
- [ ] `bin/app.ts` 存在且为可执行
- [ ] `lib/constructs/` 和 `lib/stacks/` 已创建
- [ ] `lib/config/environments.ts` 已配置
- [ ] `.claude/CLAUDE.md` 已配置

### 配置文件
- [ ] `cdk.json` 包含应用入口和 context
- [ ] `package.json` 包含所有必要脚本
- [ ] `tsconfig.json` 配置正确
- [ ] `jest.config.js` 配置测试
- [ ] `README.md` 包含项目说明

### Git 配置
- [ ] `.gitignore` 包含 `cdk.context.json`
- [ ] `.gitignore` 包含 `cdk.out/`
- [ ] `.gitignore` 包含 `node_modules/`

---

## 4. cdk.json 配置参考

```json
{
  "app": "npx ts-node --prefer-ts-exts bin/app.ts",
  "watch": {
    "include": ["**"],
    "exclude": [
      "README.md",
      "cdk*.json",
      "**/*.d.ts",
      "**/*.js",
      "tsconfig.json",
      "package*.json",
      "yarn.lock",
      "node_modules",
      "test"
    ]
  },
  "context": {
    "@aws-cdk/aws-apigateway:usagePlanKeyOrderInsensitiveId": true,
    "@aws-cdk/core:stackRelativeExports": true,
    "@aws-cdk/aws-rds:lowercaseDbIdentifier": true,
    "@aws-cdk/core:newStyleStackSynthesis": true,
    "environments": {
      "dev": {
        "account": "123456789012",
        "region": "ap-northeast-1"
      }
    }
  }
}
```

---

## PR Review 检查清单

- [ ] 新 Construct 放在 `lib/constructs/{name}/`
- [ ] 新 Stack 放在 `lib/stacks/`
- [ ] 测试与源码在对应目录
- [ ] 无硬编码的账户或区域
- [ ] cdk.context.json 未被提交
