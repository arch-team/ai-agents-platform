> **职责**: 性能优化规范 - 代码分割、Memoization、列表优化、Bundle 优化

# 性能优化规范 (Performance Standards)

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

// 懒加载页面组件
const LoginPage = lazy(() => import('@/pages/login'));
const DashboardPage = lazy(() => import('@/pages/dashboard'));

export function AppRoutes() {
  return (
    <Suspense fallback={<Spinner fullScreen />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<DashboardPage />} />
      </Routes>
    </Suspense>
  );
}
```

### 1.2 组件级分割

```typescript
// 大型组件懒加载
const RichTextEditor = lazy(() => import('./RichTextEditor'));

function Editor() {
  return (
    <Suspense fallback={<Spinner />}>
      <RichTextEditor />
    </Suspense>
  );
}
```

### 1.3 预加载

```typescript
// 鼠标悬停时预加载
function AgentCard({ agent }: { agent: Agent }) {
  const handleMouseEnter = () => {
    import('@/pages/agents/detail'); // 预加载详情页
  };

  return <Link to={`/agents/${agent.id}`} onMouseEnter={handleMouseEnter}>...</Link>;
}
```

---

## 2. Memoization

### 决策表格

| 场景 | 需要 memo? | 工具 | 示例 |
|------|-----------|------|------|
| 传给 memo 子组件的函数 | ✅ | `useCallback` | `onClick` handler |
| 传给 memo 子组件的对象 | ✅ | `useMemo` | `config` object |
| 昂贵计算 (排序/过滤) | ✅ | `useMemo` | 大数组处理 |
| 频繁更新的父组件下的子组件 | ✅ | `React.memo` | DataGrid |
| 简单计算 | ❌ | - | `a + b` |
| 不传给子组件的函数 | ❌ | - | 本地 handler |
| 简单组件 | ❌ | - | Button |

### 示例

```typescript
// ✅ 需要 - 传递给 memo 子组件
function Parent() {
  const handleClick = useCallback(() => { /* ... */ }, []);
  const config = useMemo(() => ({ theme: 'dark' }), []);
  return <MemoizedChild onClick={handleClick} config={config} />;
}

// ✅ 需要 - 昂贵计算
function List({ items, filter }: Props) {
  const filtered = useMemo(
    () => items.filter(i => i.status === filter).sort((a, b) => a.name.localeCompare(b.name)),
    [items, filter]
  );
  return <ul>{filtered.map(/* ... */)}</ul>;
}

// ❌ 不需要 - 简单计算、不传给子组件
function Simple({ a, b }: Props) {
  const sum = a + b; // 不需要 useMemo
  const handleChange = (e: ChangeEvent) => { /* ... */ }; // 不需要 useCallback
  return <input onChange={handleChange} />;
}
```

---

## 3. 列表优化

### 3.1 虚拟列表

```typescript
// 使用 react-window 处理大列表 (>100 项)
import { FixedSizeList } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

function VirtualList({ items, renderItem }: VirtualListProps) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>{renderItem(items[index])}</div>
  );

  return (
    <AutoSizer>
      {({ height, width }) => (
        <FixedSizeList height={height} width={width} itemCount={items.length} itemSize={50}>
          {Row}
        </FixedSizeList>
      )}
    </AutoSizer>
  );
}
```

### 3.2 Key 规则

```typescript
// ✅ 正确 - 使用稳定唯一 ID
{items.map((item) => <ListItem key={item.id} item={item} />)}

// ❌ 错误 - 使用 index (列表会变化时)
{items.map((item, index) => <ListItem key={index} item={item} />)}
```

---

## 4. 状态优化

### 细粒度状态

```typescript
// ❌ 错误 - 大对象状态 (任何字段变化都导致重渲染)
const [state, setState] = useState({
  user: null,
  settings: {},
  notifications: [],
  sidebarOpen: true,
});

// ✅ 正确 - 拆分状态
const [user, setUser] = useState(null);
const [sidebarOpen, setSidebarOpen] = useState(true);
```

> **Zustand Selector 和 React Query 优化**: 详见 [state-management.md](state-management.md) §2.2 和 §1.1

---

## 5. 图片优化

```tsx
// 原生懒加载 (推荐)
<img src={imageUrl} loading="lazy" alt="描述" />

// 响应式图片
<img
  src="/image.jpg"
  srcSet="/image-320.jpg 320w, /image-640.jpg 640w"
  sizes="(max-width: 320px) 280px, 600px"
  alt="描述"
  loading="lazy"
/>
```

---

## 6. 性能监控

### Profiler 用法

```typescript
import { Profiler } from 'react';

<Profiler id="AgentList" onRender={(id, phase, duration) => console.log({ id, phase, duration })}>
  <AgentList />
</Profiler>
```

### Web Vitals

```bash
# 安装
pnpm add web-vitals

# 使用
import { onCLS, onFCP, onLCP } from 'web-vitals';
onLCP(console.log);
```

### 性能指标目标

| 指标 | 目标 | 说明 |
|------|------|------|
| LCP | < 2.5s | 最大内容绘制 |
| FID | < 100ms | 首次输入延迟 |
| CLS | < 0.1 | 累积布局偏移 |
| FCP | < 1.8s | 首次内容绘制 |
| TTI | < 3.8s | 可交互时间 |

---

## 7. Bundle 优化

### 分析命令

```bash
# 安装
pnpm add -D rollup-plugin-visualizer

# vite.config.ts 中添加
import { visualizer } from 'rollup-plugin-visualizer';
plugins: [visualizer({ open: true, gzipSize: true })]
```

### Tree Shaking

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
| [state-management.md](state-management.md) | Zustand Selector / React Query 优化 |
| [architecture.md](architecture.md) | 代码分割边界 |
