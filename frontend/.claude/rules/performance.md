# 性能优化规范 (Performance Standards)

> Claude 生成代码时优先查阅此文档

---

## 0. 速查卡片

### 优化决策流程

```
性能问题?
    ↓
首先测量 (React DevTools Profiler / Lighthouse)
    ↓
识别瓶颈
    ↓
应用对应优化策略
    ↓
再次测量验证
```

### 常见优化速查

| 问题 | 解决方案 |
|------|---------|
| 首屏加载慢 | 代码分割 / 懒加载 |
| 组件重渲染 | React.memo / useMemo / useCallback |
| 列表卡顿 | 虚拟列表 (react-window) |
| 图片加载慢 | 懒加载 / WebP / 压缩 |
| 状态更新慢 | 细粒度状态 / Selector |

### Memoization 决策

```
需要 memo/useMemo/useCallback?
    ↓
传递给 memo 子组件的 props? ──是──► useCallback/useMemo
    │
   否
    ↓
昂贵计算 (排序/过滤大数组)? ──是──► useMemo
    │
   否
    ↓
❌ 不需要 (过度优化)
```

### PR Review 检查清单

- [ ] 路由级组件使用 lazy 加载
- [ ] 大列表使用虚拟列表
- [ ] memo 使用有明确理由
- [ ] 图片有 loading="lazy"
- [ ] 没有在渲染中创建新对象/函数传给子组件

---

## 1. 代码分割

### 1.1 路由级分割

```typescript
// app/routes/index.tsx
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Spinner } from '@/shared/ui';

// 懒加载页面组件
const LoginPage = lazy(() => import('@/pages/login'));
const DashboardPage = lazy(() => import('@/pages/dashboard'));
const AgentsPage = lazy(() => import('@/pages/agents'));
const AgentDetailPage = lazy(() => import('@/pages/agents/detail'));

export function AppRoutes() {
  return (
    <Suspense fallback={<Spinner fullScreen />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<DashboardPage />} />
        <Route path="/agents" element={<AgentsPage />} />
        <Route path="/agents/:id" element={<AgentDetailPage />} />
      </Routes>
    </Suspense>
  );
}
```

### 1.2 组件级分割

```typescript
// 大型组件懒加载
const RichTextEditor = lazy(() => import('./RichTextEditor'));
const ChartComponent = lazy(() => import('./ChartComponent'));

function DocumentEditor() {
  const [showChart, setShowChart] = useState(false);

  return (
    <div>
      <Suspense fallback={<Spinner />}>
        <RichTextEditor />
      </Suspense>

      {showChart && (
        <Suspense fallback={<Spinner />}>
          <ChartComponent />
        </Suspense>
      )}
    </div>
  );
}
```

### 1.3 预加载

```typescript
// 鼠标悬停时预加载
const AgentDetailPage = lazy(() => import('@/pages/agents/detail'));

function AgentCard({ agent }: { agent: Agent }) {
  const handleMouseEnter = () => {
    // 预加载详情页
    import('@/pages/agents/detail');
  };

  return (
    <Link
      to={`/agents/${agent.id}`}
      onMouseEnter={handleMouseEnter}
    >
      {/* ... */}
    </Link>
  );
}
```

---

## 2. Memoization

### 2.1 React.memo

```typescript
// ✅ 需要 memo - 接收复杂 props 且父组件频繁更新
interface DataGridProps {
  data: Item[];
  columns: Column[];
  onRowClick: (item: Item) => void;
}

export const DataGrid = memo(function DataGrid({
  data,
  columns,
  onRowClick,
}: DataGridProps) {
  // 复杂渲染逻辑
  return (
    <table>
      {/* ... */}
    </table>
  );
});

// ❌ 不需要 memo - 简单组件
export function Button({ children, onClick }: ButtonProps) {
  return <button onClick={onClick}>{children}</button>;
}
```

### 2.2 useMemo

```typescript
// ✅ 需要 useMemo - 昂贵计算
function AgentList({ agents, filter }: Props) {
  const filteredAgents = useMemo(
    () => agents.filter((a) => a.status === filter).sort((a, b) => a.name.localeCompare(b.name)),
    [agents, filter]
  );

  return <List items={filteredAgents} />;
}

// ✅ 需要 useMemo - 传递给 memo 子组件的对象
function ParentComponent() {
  const config = useMemo(
    () => ({ theme: 'dark', size: 'large' }),
    []
  );

  return <MemoizedChild config={config} />;
}

// ❌ 不需要 useMemo - 简单计算
function SimpleComponent({ a, b }: Props) {
  // 不要这样做
  const sum = useMemo(() => a + b, [a, b]);

  // 直接计算
  const sum = a + b;
}
```

### 2.3 useCallback

```typescript
// ✅ 需要 useCallback - 传递给 memo 子组件
function ParentComponent() {
  const [count, setCount] = useState(0);

  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);

  return (
    <>
      <span>{count}</span>
      <MemoizedButton onClick={handleClick} />
    </>
  );
}

// ✅ 需要 useCallback - 作为 useEffect 依赖
function SearchComponent({ onSearch }: Props) {
  const [query, setQuery] = useState('');

  const debouncedSearch = useCallback(
    debounce((q: string) => onSearch(q), 300),
    [onSearch]
  );

  useEffect(() => {
    debouncedSearch(query);
  }, [query, debouncedSearch]);
}

// ❌ 不需要 useCallback - 不传递给子组件
function SimpleForm() {
  const [value, setValue] = useState('');

  // 不需要 useCallback
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
  };

  return <input value={value} onChange={handleChange} />;
}
```

---

## 3. 列表优化

### 3.1 虚拟列表

```typescript
// 使用 react-window 处理大列表
import { FixedSizeList } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

interface VirtualListProps {
  items: Item[];
  renderItem: (item: Item) => React.ReactNode;
}

export function VirtualList({ items, renderItem }: VirtualListProps) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>{renderItem(items[index])}</div>
  );

  return (
    <AutoSizer>
      {({ height, width }) => (
        <FixedSizeList
          height={height}
          width={width}
          itemCount={items.length}
          itemSize={50}
        >
          {Row}
        </FixedSizeList>
      )}
    </AutoSizer>
  );
}
```

### 3.2 列表 Key 优化

```typescript
// ✅ 正确 - 使用稳定唯一 ID
{items.map((item) => (
  <ListItem key={item.id} item={item} />
))}

// ❌ 错误 - 使用 index (列表会变化时)
{items.map((item, index) => (
  <ListItem key={index} item={item} />
))}
```

---

## 4. 状态优化

### 4.1 细粒度状态

```typescript
// ❌ 错误 - 大对象状态
const [state, setState] = useState({
  user: null,
  settings: {},
  notifications: [],
  sidebarOpen: true,
});

// ✅ 正确 - 拆分状态
const [user, setUser] = useState(null);
const [sidebarOpen, setSidebarOpen] = useState(true);
// 或使用多个 Zustand store
```

### 4.2 Zustand Selector

```typescript
// ❌ 错误 - 订阅整个 store
function Component() {
  const store = useStore(); // 任何状态变化都会重渲染
}

// ✅ 正确 - 只订阅需要的状态
function Component() {
  const user = useStore((state) => state.user);
  const isOpen = useStore((state) => state.sidebarOpen);
}

// ✅ 正确 - 使用 shallow 比较
import { shallow } from 'zustand/shallow';

function Component() {
  const { user, settings } = useStore(
    (state) => ({ user: state.user, settings: state.settings }),
    shallow
  );
}
```

### 4.3 React Query 优化

```typescript
// 配置合适的 staleTime
const { data } = useQuery({
  queryKey: ['agents'],
  queryFn: fetchAgents,
  staleTime: 1000 * 60 * 5, // 5 分钟内不重新获取
  gcTime: 1000 * 60 * 30,   // 30 分钟后清除缓存
});

// 使用 select 只订阅需要的数据
const { data: agentNames } = useQuery({
  queryKey: ['agents'],
  queryFn: fetchAgents,
  select: (data) => data.map((a) => a.name), // 只订阅名称变化
});
```

---

## 5. 图片优化

### 5.1 懒加载

```tsx
// 原生懒加载
<img src={imageUrl} loading="lazy" alt="描述" />

// 或使用 Intersection Observer
import { useInView } from 'react-intersection-observer';

function LazyImage({ src, alt }: { src: string; alt: string }) {
  const { ref, inView } = useInView({
    triggerOnce: true,
    rootMargin: '200px',
  });

  return (
    <div ref={ref}>
      {inView ? <img src={src} alt={alt} /> : <div className="placeholder" />}
    </div>
  );
}
```

### 5.2 响应式图片

```tsx
<picture>
  <source srcSet="/image.webp" type="image/webp" />
  <source srcSet="/image.jpg" type="image/jpeg" />
  <img
    src="/image.jpg"
    srcSet="/image-320.jpg 320w, /image-640.jpg 640w, /image-1280.jpg 1280w"
    sizes="(max-width: 320px) 280px, (max-width: 640px) 600px, 1200px"
    alt="描述"
    loading="lazy"
  />
</picture>
```

---

## 6. 性能监控

### 6.1 React DevTools Profiler

```typescript
// 开发环境使用 Profiler
import { Profiler } from 'react';

function onRenderCallback(
  id: string,
  phase: 'mount' | 'update',
  actualDuration: number
) {
  console.log({ id, phase, actualDuration });
}

<Profiler id="AgentList" onRender={onRenderCallback}>
  <AgentList />
</Profiler>
```

### 6.2 Web Vitals

```typescript
// app/index.tsx
import { reportWebVitals } from './reportWebVitals';

// 启动应用后报告性能指标
reportWebVitals(console.log);

// reportWebVitals.ts
import { onCLS, onFID, onFCP, onLCP, onTTFB } from 'web-vitals';

export function reportWebVitals(onPerfEntry?: (metric: any) => void) {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    onCLS(onPerfEntry);
    onFID(onPerfEntry);
    onFCP(onPerfEntry);
    onLCP(onPerfEntry);
    onTTFB(onPerfEntry);
  }
}
```

### 6.3 性能指标目标

| 指标 | 目标 | 说明 |
|------|------|------|
| LCP | < 2.5s | 最大内容绘制 |
| FID | < 100ms | 首次输入延迟 |
| CLS | < 0.1 | 累积布局偏移 |
| FCP | < 1.8s | 首次内容绘制 |
| TTI | < 3.8s | 可交互时间 |

---

## 7. Bundle 优化

### 7.1 分析 Bundle

```bash
# 使用 vite-bundle-visualizer
pnpm add -D rollup-plugin-visualizer

# vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    visualizer({
      open: true,
      gzipSize: true,
    }),
  ],
});
```

### 7.2 Tree Shaking

```typescript
// ✅ 正确 - 具名导入 (可 tree shake)
import { debounce } from 'lodash-es';

// ❌ 错误 - 默认导入整个库
import _ from 'lodash';
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [component-design.md](component-design.md) | 组件 memo 使用 |
| [state-management.md](state-management.md) | 状态优化 |
| [architecture.md](architecture.md) | 代码分割边界 |
