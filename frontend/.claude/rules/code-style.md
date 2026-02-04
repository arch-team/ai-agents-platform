# 代码风格规范 (Code Style Standards)

> Claude 生成代码时优先查阅此文档

本文档定义 React + TypeScript 前端项目的代码风格规范。

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

- [ ] 命名符合规范
- [ ] 没有 `any` 类型
- [ ] Props 使用 `interface` 定义
- [ ] 导入按规范排序
- [ ] 没有未使用的变量/导入
- [ ] 组件有 `displayName` (forwardRef)

---

## 1. 命名规范

### 1.1 组件命名

```typescript
// ✅ 正确 - PascalCase
function UserProfile() { ... }
function LoginForm() { ... }
export const AgentCard = memo(function AgentCard() { ... });

// ❌ 错误
function userProfile() { ... }  // 小写开头
function User_Profile() { ... } // 下划线
```

### 1.2 函数和变量

```typescript
// ✅ 正确 - camelCase
const getUserById = async (id: string) => { ... };
const isLoading = true;
const handleSubmit = () => { ... };

// ❌ 错误
const GetUserById = () => { ... };  // 大写开头
const is_loading = true;            // 下划线
```

### 1.3 常量

```typescript
// ✅ 正确 - UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = 'https://api.example.com';
const DEFAULT_PAGE_SIZE = 20;

// ❌ 错误
const maxRetryCount = 3;  // 应该全大写
```

### 1.4 类型和接口

```typescript
// ✅ 正确 - PascalCase
interface UserProfile { ... }
type ApiResponse<T> = { ... };
enum UserStatus { Active, Inactive }

// ❌ 错误
interface userProfile { ... }  // 小写开头
type api_response = { ... };   // 下划线
```

### 1.5 Hooks

```typescript
// ✅ 正确 - use 前缀
function useAuth() { ... }
function useDebounce<T>(value: T, delay: number) { ... }
function useLocalStorage<T>(key: string) { ... }

// ❌ 错误
function getAuth() { ... }      // 缺少 use 前缀
function authHook() { ... }     // 不符合规范
```

### 1.6 事件处理函数

```typescript
// ✅ 正确 - handle 前缀
const handleClick = () => { ... };
const handleSubmit = (e: FormEvent) => { ... };
const handleInputChange = (value: string) => { ... };

// Props 中的事件 - on 前缀
interface ButtonProps {
  onClick: () => void;
  onHover?: () => void;
}
```

### 1.7 布尔值

```typescript
// ✅ 正确 - is/has/can/should 前缀
const isLoading = true;
const hasPermission = user.role === 'admin';
const canEdit = hasPermission && !isLocked;
const shouldRefetch = staleTime > 0;

// ❌ 错误
const loading = true;     // 不清晰
const permission = true;  // 名词，不清晰
```

---

## 2. TypeScript 规范

### 2.1 类型定义位置

```
组件 Props      → 组件文件内或同目录 .types.ts
实体类型       → entities/{entity}/model/types.ts
API 响应类型   → features/{feature}/api/types.ts 或 model/types.ts
通用类型       → shared/types/
```

### 2.2 Interface vs Type

```typescript
// ✅ interface - 用于对象形状 (推荐)
interface User {
  id: string;
  name: string;
  email: string;
}

interface ButtonProps {
  variant: 'primary' | 'secondary';
  children: React.ReactNode;
}

// ✅ type - 用于联合类型、映射类型、工具类型
type ButtonVariant = 'primary' | 'secondary' | 'outline';
type Nullable<T> = T | null;
type PartialUser = Partial<User>;
```

### 2.3 避免 any

```typescript
// ❌ 错误
function processData(data: any) { ... }
const response: any = await fetch(url);

// ✅ 正确 - 使用具体类型
function processData(data: UserData) { ... }

// ✅ 正确 - 使用 unknown + 类型守卫
function processUnknown(data: unknown) {
  if (isUserData(data)) {
    // data 现在是 UserData 类型
  }
}

// ✅ 正确 - 泛型
function processData<T>(data: T): T { ... }
```

### 2.4 类型导出

```typescript
// ✅ 正确 - 类型单独导出
export type { User, UserProfile };
export type { ButtonProps } from './Button.types';

// 或在 index.ts 中
export { Button } from './Button';
export type { ButtonProps } from './Button.types';
```

### 2.5 泛型命名

```typescript
// 单字母泛型 - 简单场景
function identity<T>(value: T): T { ... }
function map<T, U>(arr: T[], fn: (item: T) => U): U[] { ... }

// 描述性泛型 - 复杂场景
interface Repository<TEntity, TId> {
  findById(id: TId): Promise<TEntity | null>;
}

function createStore<TState, TActions>(
  initialState: TState,
  actions: TActions
) { ... }
```

---

## 3. 导入规范

### 3.1 导入排序

```typescript
// 1. React 核心
import React, { useState, useEffect, useCallback } from 'react';

// 2. 第三方库 (按字母排序)
import { useQuery, useMutation } from '@tanstack/react-query';
import { z } from 'zod';
import { clsx } from 'clsx';

// 3. 内部别名导入 (按 FSD 层级：shared → entities → features → widgets → pages)
import { Button, Input } from '@/shared/ui';
import { apiClient } from '@/shared/api';
import { User } from '@/entities/user';
import { useAuth } from '@/features/auth';

// 4. 相对导入
import { useLocalState } from './hooks';
import { formatData } from './utils';

// 5. 类型导入 (单独分组)
import type { FC, ReactNode } from 'react';
import type { User } from '@/entities/user';
import type { LocalState } from './types';

// 6. 样式导入 (最后)
import './styles.css';
```

### 3.2 路径别名

```typescript
// ✅ 正确 - 使用路径别名
import { Button } from '@/shared/ui';
import { useAuth } from '@/features/auth';

// ❌ 错误 - 过长的相对路径
import { Button } from '../../../shared/ui';
```

### 3.3 禁止的导入

```typescript
// ❌ 禁止 - 通配符导入
import * as utils from '@/shared/lib';

// ❌ 禁止 - 导入内部实现
import { validateEmail } from '@/features/auth/lib/validation';

// ✅ 正确 - 从公开 API 导入
import { useAuth } from '@/features/auth';
```

---

## 4. 组件代码组织

### 4.1 组件文件结构

```typescript
// 1. 导入
import { useState, useCallback } from 'react';
import { Button } from '@/shared/ui';
import type { User } from '@/entities/user';

// 2. 类型定义 (简单时直接写在文件中)
interface UserCardProps {
  user: User;
  onEdit?: () => void;
}

// 3. 辅助函数/常量 (组件外)
const MAX_NAME_LENGTH = 50;

function formatUserName(name: string): string {
  return name.length > MAX_NAME_LENGTH
    ? `${name.slice(0, MAX_NAME_LENGTH)}...`
    : name;
}

// 4. 组件定义
export function UserCard({ user, onEdit }: UserCardProps) {
  // 4.1 Hooks (顶部)
  const [isExpanded, setIsExpanded] = useState(false);

  // 4.2 派生状态
  const displayName = formatUserName(user.name);

  // 4.3 事件处理函数
  const handleToggle = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  // 4.4 副作用 (useEffect)
  // ...

  // 4.5 早期返回
  if (!user) {
    return null;
  }

  // 4.6 渲染
  return (
    <div className="user-card">
      {/* ... */}
    </div>
  );
}
```

### 4.2 forwardRef 组件

```typescript
import { forwardRef } from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...props }, ref) => {
    return (
      <div className="input-wrapper">
        {label && <label>{label}</label>}
        <input ref={ref} className={className} {...props} />
        {error && <span className="error">{error}</span>}
      </div>
    );
  }
);

// 必须设置 displayName
Input.displayName = 'Input';
```

---

## 5. JSX 规范

### 5.1 JSX 格式

```tsx
// ✅ 正确 - 多属性换行
<Button
  variant="primary"
  size="lg"
  disabled={isLoading}
  onClick={handleSubmit}
>
  提交
</Button>

// ✅ 正确 - 单属性可单行
<Button variant="primary">提交</Button>

// ❌ 错误 - 过长的单行
<Button variant="primary" size="lg" disabled={isLoading} onClick={handleSubmit}>提交</Button>
```

### 5.2 条件渲染

```tsx
// ✅ 正确 - && 短路
{isLoggedIn && <UserMenu />}

// ✅ 正确 - 三元表达式 (简单)
{isLoading ? <Spinner /> : <Content />}

// ✅ 正确 - 提前返回
if (isLoading) return <Spinner />;
if (error) return <ErrorMessage error={error} />;
return <Content />;

// ❌ 错误 - 嵌套三元
{isLoading ? <Spinner /> : error ? <Error /> : <Content />}
```

### 5.3 列表渲染

```tsx
// ✅ 正确 - 使用唯一且稳定的 key
{users.map((user) => (
  <UserCard key={user.id} user={user} />
))}

// ❌ 错误 - 使用 index 作为 key (除非列表不会变化)
{users.map((user, index) => (
  <UserCard key={index} user={user} />
))}
```

---

## 6. ESLint 和 Prettier 配置

### 6.1 ESLint 配置参考

```javascript
// .eslintrc.cjs
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    'plugin:react/recommended',
    'prettier',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    'react/react-in-jsx-scope': 'off',
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/explicit-function-return-type': 'off',
  },
  settings: {
    react: { version: 'detect' },
  },
};
```

### 6.2 Prettier 配置参考

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "jsxSingleQuote": false
}
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [component-design.md](component-design.md) | 组件设计模式 |
| [architecture.md](architecture.md) | FSD 分层规则 |
| [testing.md](testing.md) | 测试命名规范 |
