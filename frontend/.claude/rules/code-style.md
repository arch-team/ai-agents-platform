> **职责**: 代码风格规范 - 命名规范、TypeScript 规范、导入排序

# 代码风格规范 (Code Style Standards)

---

## 0. 速查卡片

### 命名速查

| 元素 | 样式 | 示例 |
|------|------|------|
| 组件 | `PascalCase` | `UserProfile`, `LoginForm` |
| 函数/变量 | `camelCase` | `getUserData`, `isLoading` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| 类型/接口 | `PascalCase` | `UserData`, `ApiResponse` |
| Hooks | `use` + `camelCase` | `useAuth`, `useFetch` |
| CSS 类 | `kebab-case` | `user-profile`, `login-form` |
| 文件 (组件) | `PascalCase.tsx` | `UserProfile.tsx` |
| 文件 (工具) | `camelCase.ts` | `formatDate.ts` |
| 目录 | `kebab-case` | `user-profile/`, `auth/` |

### TypeScript 速查

| 规则 | ✅ 正确 | ❌ 错误 |
|------|--------|--------|
| Props 定义 | `interface ButtonProps {}` | `type ButtonProps = {}` |
| 导出类型 | `export type { User }` | `export { User }` |
| 避免 any | 具体类型 / unknown | `any` |
| 联合类型 | `'sm' \| 'md' \| 'lg'` | `string` |

### 导入排序

```typescript
// 1. React 核心
import { useState, useEffect } from 'react';

// 2. 第三方库
import { useQuery } from '@tanstack/react-query';
import { clsx } from 'clsx';

// 3. 内部别名 (按 FSD 层级)
import { Button } from '@/shared/ui';
import { useAuth } from '@/features/auth';
import { AgentCard } from '@/entities/agent';

// 4. 相对导入
import { useLocalState } from './hooks';

// 5. 类型导入 (单独行)
import type { User } from '@/entities/user';
```

### PR Review 检查清单

完整检查清单见 [checklist.md](checklist.md) §代码风格

---

## 1. 命名规范补充

### 1.1 事件处理函数

```typescript
// 组件内部 - handle 前缀
const handleClick = () => { ... };
const handleSubmit = (e: FormEvent) => { ... };

// Props 中的事件 - on 前缀
interface ButtonProps {
  onClick: () => void;
  onHover?: () => void;
}
```

### 1.2 布尔值命名

| 前缀 | 用途 | 示例 |
|------|------|------|
| `is` | 状态判断 | `isLoading`, `isVisible` |
| `has` | 所有权判断 | `hasPermission`, `hasError` |
| `can` | 能力判断 | `canEdit`, `canSubmit` |
| `should` | 条件判断 | `shouldRefetch`, `shouldShow` |

---

## 2. TypeScript 规范

### 2.1 类型定义位置

| 类型 | 位置 |
|------|------|
| 组件 Props | 组件文件内或同目录 `.types.ts` |
| 实体类型 | `entities/{entity}/model/types.ts` |
| API 响应类型 | `features/{feature}/api/types.ts` |
| 通用类型 | `shared/types/` |

### 2.2 Interface vs Type 决策

| 场景 | 选择 |
|------|------|
| 对象形状、Props | `interface` |
| 联合类型 | `type` |
| 映射类型、工具类型 | `type` |

### 2.3 泛型命名

| 场景 | 命名 | 示例 |
|------|------|------|
| 简单场景 | 单字母 | `T`, `U`, `K`, `V` |
| 复杂场景 | 描述性 + `T` 前缀 | `TEntity`, `TState`, `TActions` |

---

## 3. 导入规范

### 3.1 路径别名

使用 `@/` 替代深层相对路径：

```typescript
// ✅ 正确
import { Button } from '@/shared/ui';

// ❌ 错误
import { Button } from '../../../shared/ui';
```

### 3.2 禁止的导入模式

| 模式 | 原因 |
|------|------|
| `import * as utils from '...'` | 不利于 Tree Shaking |
| 导入内部实现文件 | 破坏模块封装 |

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [component-design.md](component-design.md) | 组件设计模式、组件代码组织 |
| [architecture.md](architecture.md) | FSD 分层规则 |
| [testing.md](testing.md) | 测试命名规范 |
