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
// shared/ui/Button/Button.tsx - 结构骨架
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
        className={cn(/* variant + size + state 样式 */, className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Spinner />}
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
// features/agents/ui/AgentList.tsx - 结构骨架
interface AgentListProps {
  onSelect?: (id: string) => void;
}

export function AgentList({ onSelect }: AgentListProps) {
  const { data: agents, isLoading, error } = useAgents();

  if (isLoading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!agents?.length) return <EmptyState />;

  return (
    <div className="grid gap-4">
      {agents.map((agent) => (
        <AgentCard key={agent.id} agent={agent} onClick={() => onSelect?.(agent.id)} />
      ))}
    </div>
  );
}
```

### 1.3 复合组件 (Compound)

**特点**: 多个子组件组合，通过 Context 共享状态

```typescript
// shared/ui/Tabs/Tabs.tsx - 结构骨架

// 1. Context
interface TabsContextValue {
  activeTab: string;
  setActiveTab: (value: string) => void;
}
const TabsContext = createContext<TabsContextValue | null>(null);

// 2. Root 组件
function TabsRoot({ defaultValue, children, onChange }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultValue);
  // ... onChange 回调
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      {children}
    </TabsContext.Provider>
  );
}

// 3. 子组件 (TabList, Tab, TabPanel)
function Tab({ value, children }: TabProps) {
  const { activeTab, setActiveTab } = useTabsContext();
  return <button role="tab" aria-selected={activeTab === value} onClick={() => setActiveTab(value)}>{children}</button>;
}

// 4. 导出组合
export const Tabs = Object.assign(TabsRoot, { List: TabList, Tab, Panel: TabPanel });
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

## 2. Props 高级模式

### 2.1 继承原生属性

```typescript
// 继承原生属性并扩展
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

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

### 2.2 Ref 转发

```typescript
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, ...props }, ref) => {
    return <input ref={ref} {...props} />;
  }
);
Input.displayName = 'Input';
```

### 2.3 泛型组件

```typescript
interface ListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
}

export function List<T>({ items, renderItem, keyExtractor, emptyMessage = '暂无数据' }: ListProps<T>) {
  if (!items.length) return <div>{emptyMessage}</div>;
  return <ul>{items.map((item, i) => <li key={keyExtractor(item)}>{renderItem(item, i)}</li>)}</ul>;
}
```

---

## 3. 自定义 Hooks

### 返回值设计规则

| 场景 | 返回类型 | 示例 |
|------|---------|------|
| 多个值 | 对象 | `{ user, isAuthenticated, login, logout }` |
| 类似 useState | 元组 | `[state, toggle]` |
| 单个值 | 直接返回 | `debouncedValue` |

```typescript
// 返回对象 - 多个值
function useAuth() {
  return { user, isAuthenticated, login, logout };
}

// 返回元组 - 类似 useState
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
| [code-style.md](code-style.md) | 命名规范、TypeScript 规范 |
| [testing.md](testing.md) | 组件测试规范 |
| [performance.md](performance.md) | Memo、useCallback、useMemo 使用规范 |
| [accessibility.md](accessibility.md) | 无障碍要求 |
