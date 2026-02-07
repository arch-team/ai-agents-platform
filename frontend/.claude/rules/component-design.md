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


---

## 1. 组件类型

### 1.1 展示型组件 (Presentational)

**关键模式**: `forwardRef` + `displayName` + 继承原生属性 + variant/size

```typescript
// shared/ui/Button/Button.tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, children, className, disabled, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(/* variant + size + state 样式 */, className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner />}
      {children}
    </button>
  )
);
Button.displayName = 'Button';
```

### 1.2 容器型组件 (Container)

**关键模式**: React Query 数据获取 + loading/error/empty 三态处理

```typescript
// features/agents/ui/AgentList.tsx
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

**关键模式**: Context 共享状态 + `Object.assign` 组合导出

```typescript
// shared/ui/Tabs/Tabs.tsx - 结构骨架
// 1. Context
const TabsContext = createContext<TabsContextValue | null>(null);

// 2. Root 组件提供 Context
function TabsRoot({ defaultValue, children, onChange }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultValue);
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      {children}
    </TabsContext.Provider>
  );
}

// 3. 子组件消费 Context (TabList, Tab, TabPanel 各自实现)

// 4. 组合导出
export const Tabs = Object.assign(TabsRoot, { List: TabList, Tab, Panel: TabPanel });
```

**使用方式**:

```tsx
<Tabs defaultValue="tab1" onChange={handleChange}>
  <Tabs.List>
    <Tabs.Tab value="tab1">标签一</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel value="tab1">内容一</Tabs.Panel>
</Tabs>
```

---

## 2. Props 高级模式

### 2.1 继承原生属性

```typescript
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

**Ref 转发**: 需要 ref 时用 `forwardRef`，并设置 `displayName`（见 §1.1）

### 2.2 泛型组件

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

## 3. 自定义 Hooks 返回值

| 场景 | 返回类型 | 示例 |
|------|---------|------|
| 多个值 | 对象 | `{ user, isAuthenticated, login, logout }` |
| 类似 useState | 元组 | `[state, toggle]` |
| 单个值 | 直接返回 | `debouncedValue` |

---

## 4. 组件文件结构

### 单组件

```
Button/
├── index.ts              # export { Button } from './Button';
├── Button.tsx            # 组件实现
├── Button.test.tsx       # 单元测试
└── Button.types.ts       # 类型定义 (复杂时)
```

### 复合组件

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
