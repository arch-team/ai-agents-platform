> **职责**: 组件设计规范 - 组件类型、Props 设计、复合组件模式

# 组件设计规范 (Component Design Standards)

---

## 0. 速查卡片

### 组件类型速查

| 类型 | 职责 | 示例 | 位置 |
|------|------|------|------|
| **展示型** | 纯 UI 渲染，无状态 | `Button`, `Card`, `Avatar` | `shared/ui/` |
| **容器型** | 业务逻辑，数据获取 | `AgentList`, `LoginForm` | `features/*/ui/` |
| **复合型** | 多组件组合，共享状态 | `Tabs`, `Dropdown`, `Dialog` | `shared/ui/` |

### 组件决策流程

```
需要创建组件?
    ↓
包含业务逻辑? ──是──► features/{feature}/ui/
    │
   否
    ↓
是复用基础组件? ──是──► shared/ui/
    │
   否
    ↓
组合多个 features? ──是──► widgets/{widget}/ui/
    │
   否
    ↓
实体基础展示? ──是──► entities/{entity}/ui/
```

### Props 设计速查

| 规则 | ✅ 正确 | ❌ 错误 |
|------|--------|--------|
| 使用 interface | `interface ButtonProps {}` | `type ButtonProps = {}` |
| children 类型 | `children: React.ReactNode` | `children: any` |
| 事件命名 | `onClick`, `onSubmit` | `click`, `handleClick` |
| 可选属性 | `disabled?: boolean` | `disabled: boolean \| undefined` |
| 默认值 | 解构默认值 | Props 中定义默认 |

### PR Review 检查清单

- [ ] 组件类型正确（展示/容器/复合）
- [ ] Props 使用 interface 定义
- [ ] 事件处理函数命名以 `handle` 开头
- [ ] 无 `any` 类型
- [ ] children 类型为 `React.ReactNode`
- [ ] 可选 Props 有合理默认值
- [ ] 复合组件使用 Context 共享状态

---

## 1. 组件类型

### 1.1 展示型组件 (Presentational)

**特点**: 纯 UI 渲染，无业务逻辑，完全通过 Props 控制

```typescript
// shared/ui/Button/Button.tsx
import { forwardRef } from 'react';
import { cn } from '@/shared/lib/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, children, className, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-md font-medium transition-colors',
          // variant styles
          variant === 'primary' && 'bg-blue-600 text-white hover:bg-blue-700',
          variant === 'secondary' && 'bg-gray-100 text-gray-900 hover:bg-gray-200',
          variant === 'outline' && 'border border-gray-300 bg-transparent hover:bg-gray-50',
          // size styles
          size === 'sm' && 'h-8 px-3 text-sm',
          size === 'md' && 'h-10 px-4 text-sm',
          size === 'lg' && 'h-12 px-6 text-base',
          // states
          (disabled || loading) && 'cursor-not-allowed opacity-50',
          className
        )}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <span className="mr-2 animate-spin">⏳</span>}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

### 1.2 容器型组件 (Container)

**特点**: 包含业务逻辑、数据获取、状态管理

```typescript
// features/agents/ui/AgentList.tsx
import { useAgents } from '../api/queries';
import { AgentCard } from '@/entities/agent';
import { Spinner } from '@/shared/ui';

interface AgentListProps {
  onSelect?: (id: string) => void;
}

export function AgentList({ onSelect }: AgentListProps) {
  const { data: agents, isLoading, error } = useAgents();

  if (isLoading) {
    return <Spinner />;
  }

  if (error) {
    return <div className="text-red-500">加载失败: {error.message}</div>;
  }

  if (!agents?.length) {
    return <div className="text-gray-500">暂无 Agent</div>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {agents.map((agent) => (
        <AgentCard
          key={agent.id}
          agent={agent}
          onClick={() => onSelect?.(agent.id)}
        />
      ))}
    </div>
  );
}
```

### 1.3 复合组件 (Compound)

**特点**: 多个子组件组合，通过 Context 共享状态

```typescript
// shared/ui/Tabs/Tabs.tsx
import { createContext, useContext, useState, useCallback } from 'react';
import { cn } from '@/shared/lib/cn';

// Context
interface TabsContextValue {
  activeTab: string;
  setActiveTab: (value: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabsContext() {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('Tabs 子组件必须在 Tabs 内使用');
  }
  return context;
}

// Root
interface TabsProps {
  defaultValue: string;
  children: React.ReactNode;
  onChange?: (value: string) => void;
}

function TabsRoot({ defaultValue, children, onChange }: TabsProps) {
  const [activeTab, setActiveTabState] = useState(defaultValue);

  const setActiveTab = useCallback((value: string) => {
    setActiveTabState(value);
    onChange?.(value);
  }, [onChange]);

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className="w-full">{children}</div>
    </TabsContext.Provider>
  );
}

// TabList
interface TabListProps {
  children: React.ReactNode;
  className?: string;
}

function TabList({ children, className }: TabListProps) {
  return (
    <div className={cn('flex border-b border-gray-200', className)}>
      {children}
    </div>
  );
}

// Tab
interface TabProps {
  value: string;
  children: React.ReactNode;
  disabled?: boolean;
}

function Tab({ value, children, disabled }: TabProps) {
  const { activeTab, setActiveTab } = useTabsContext();
  const isActive = activeTab === value;

  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      disabled={disabled}
      onClick={() => setActiveTab(value)}
      className={cn(
        'px-4 py-2 text-sm font-medium transition-colors',
        isActive
          ? 'border-b-2 border-blue-600 text-blue-600'
          : 'text-gray-500 hover:text-gray-700',
        disabled && 'cursor-not-allowed opacity-50'
      )}
    >
      {children}
    </button>
  );
}

// TabPanel
interface TabPanelProps {
  value: string;
  children: React.ReactNode;
}

function TabPanel({ value, children }: TabPanelProps) {
  const { activeTab } = useTabsContext();
  if (activeTab !== value) return null;
  return <div role="tabpanel">{children}</div>;
}

// 导出组合
export const Tabs = Object.assign(TabsRoot, {
  List: TabList,
  Tab: Tab,
  Panel: TabPanel,
});
```

**使用方式**:

```tsx
<Tabs defaultValue="tab1" onChange={handleChange}>
  <Tabs.List>
    <Tabs.Tab value="tab1">标签一</Tabs.Tab>
    <Tabs.Tab value="tab2">标签二</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel value="tab1">内容一</Tabs.Panel>
  <Tabs.Panel value="tab2">内容二</Tabs.Panel>
</Tabs>
```

---

## 2. Props 设计

### 2.1 基本规则

```typescript
// ✅ 正确 - 使用 interface
interface CardProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  onClick?: () => void;
}

// ❌ 错误 - 使用 type alias
type CardProps = {
  title: string;
  // ...
};
```

### 2.2 继承原生属性

```typescript
// ✅ 正确 - 继承原生属性
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

// 组件中展开剩余属性
export function Input({ label, error, className, ...props }: InputProps) {
  return (
    <div>
      {label && <label>{label}</label>}
      <input className={cn('...', className)} {...props} />
      {error && <span className="text-red-500">{error}</span>}
    </div>
  );
}
```

### 2.3 Ref 转发

```typescript
// 需要 ref 转发的组件
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, ...props }, ref) => {
    return (
      <input ref={ref} {...props} />
    );
  }
);

Input.displayName = 'Input';
```

### 2.4 泛型组件

```typescript
// 泛型列表组件
interface ListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
}

export function List<T>({
  items,
  renderItem,
  keyExtractor,
  emptyMessage = '暂无数据',
}: ListProps<T>) {
  if (items.length === 0) {
    return <div className="text-gray-500">{emptyMessage}</div>;
  }

  return (
    <ul>
      {items.map((item, index) => (
        <li key={keyExtractor(item)}>{renderItem(item, index)}</li>
      ))}
    </ul>
  );
}
```

---

## 3. 自定义 Hooks

### 3.1 命名规范

```typescript
// ✅ 正确命名
useAuth          // 认证相关
useDebounce      // 防抖
useLocalStorage  // 本地存储
useAgents        // Agent 数据 (React Query)

// ❌ 错误命名
getAuth          // 不是 hook
authHook         // 不符合规范
```

### 3.2 Hook 模板

```typescript
// shared/hooks/useDebounce.ts
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

### 3.3 返回值设计

```typescript
// 返回对象 - 多个值时
function useAuth() {
  return {
    user,
    isAuthenticated,
    login,
    logout,
  };
}

// 返回元组 - 类似 useState 时
function useToggle(initial = false): [boolean, () => void] {
  const [state, setState] = useState(initial);
  const toggle = useCallback(() => setState(s => !s), []);
  return [state, toggle];
}
```

---

## 4. 组件文件结构

### 4.1 单组件

```
Button/
├── index.ts              # export { Button } from './Button';
├── Button.tsx            # 组件实现
├── Button.test.tsx       # 单元测试
└── Button.types.ts       # 类型定义 (复杂时)
```

### 4.2 复合组件

```
Tabs/
├── index.ts              # 导出 Tabs 和子组件
├── Tabs.tsx              # 主组件 + Context
├── TabList.tsx           # 子组件
├── Tab.tsx               # 子组件
├── TabPanel.tsx          # 子组件
├── Tabs.context.ts       # Context (可选分离)
├── Tabs.types.ts         # 类型定义
└── Tabs.test.tsx         # 测试
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [architecture.md](architecture.md) | FSD 分层，组件放置位置 |
| [code-style.md](code-style.md) | 命名规范、类型定义 |
| [testing.md](testing.md) | 组件测试规范 |
| [performance.md](performance.md) | Memo、useCallback、useMemo 使用规范 |
| [accessibility.md](accessibility.md) | 无障碍要求 |
