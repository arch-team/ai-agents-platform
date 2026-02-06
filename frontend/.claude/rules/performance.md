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

完整检查清单见 [checklist.md](checklist.md) §性能

---

## 1. 代码分割

### 1.1 路由级分割（必须）

```typescript
// app/routes/index.tsx
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

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

### 1.2 其他分割规则

| 场景 | 方式 |
|------|------|
| 大型组件（编辑器、图表） | `lazy(() => import('./RichTextEditor'))` + `<Suspense>` |
| 预加载 | 鼠标悬停时 `import('@/pages/detail')` 触发预加载 |

---

## 2. Memoization

### ✅/❌ 示例

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

### 规则

| 规则 | 说明 |
|------|------|
| 虚拟列表阈值 | >100 项使用 `react-window` (`FixedSizeList` + `AutoSizer`) |
| Key 必须稳定唯一 | ✅ `key={item.id}` / ❌ `key={index}`（列表会变化时） |

---

## 4. 状态优化

```typescript
// ❌ 错误 - 大对象状态 (任何字段变化都导致重渲染)
const [state, setState] = useState({
  user: null, settings: {}, notifications: [], sidebarOpen: true,
});

// ✅ 正确 - 拆分状态
const [user, setUser] = useState(null);
const [sidebarOpen, setSidebarOpen] = useState(true);
```

> Zustand Selector 优化详见 state-management.md §2.2

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

## 6. 性能指标目标

| 指标 | 目标 | 说明 |
|------|------|------|
| LCP | < 2.5s | 最大内容绘制 |
| FID | < 100ms | 首次输入延迟 |
| CLS | < 0.1 | 累积布局偏移 |
| FCP | < 1.8s | 首次内容绘制 |
| TTI | < 3.8s | 可交互时间 |

---

## 7. Bundle 优化

### Tree Shaking

```typescript
// ✅ 正确 - 具名导入 (可 tree shake)
import { debounce } from 'lodash-es';

// ❌ 错误 - 默认导入整个库
import _ from 'lodash';
```

**分析工具**: `rollup-plugin-visualizer` 可视化 bundle 组成
