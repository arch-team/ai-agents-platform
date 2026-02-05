> **职责**: 无障碍规范 - WCAG 2.1 AA、ARIA 使用、键盘导航 (基于 POUR 原则)

# 无障碍规范 (Accessibility Standards)

---

## 0. 速查卡片

### 基本原则 (POUR)

| 原则 | 说明 | 示例 |
|------|------|------|
| **可感知** | 信息可被用户感知 | 图片有 alt，视频有字幕 |
| **可操作** | 界面可被用户操作 | 键盘可访问，无时间限制 |
| **可理解** | 内容可被用户理解 | 清晰标签，一致导航 |
| **健壮性** | 兼容辅助技术 | 语义化 HTML，ARIA |

### 常用 ARIA 速查

| 属性 | 用途 | 示例 |
|------|------|------|
| `aria-label` | 为元素提供标签 | `<button aria-label="关闭">×</button>` |
| `aria-labelledby` | 引用其他元素作为标签 | `<div aria-labelledby="title-id">` |
| `aria-describedby` | 引用描述性文本 | `<input aria-describedby="error-id">` |
| `aria-hidden` | 从无障碍树中隐藏 | `<span aria-hidden="true">🎨</span>` |
| `aria-expanded` | 展开/折叠状态 | `<button aria-expanded="true">` |
| `aria-current` | 当前项目标记 | `<a aria-current="page">` |

### PR Review 检查清单

- [ ] 图片有描述性 alt 文本
- [ ] 表单控件有关联的 label
- [ ] 可交互元素可通过键盘访问
- [ ] 颜色对比度 >= 4.5:1
- [ ] 焦点顺序合理
- [ ] 错误信息与输入框关联

---

## 1. 语义化 HTML

### 1.1 使用正确的元素

```tsx
// ✅ 正确 - 语义化元素
<header>
  <nav>
    <ul>
      <li><a href="/">首页</a></li>
      <li><a href="/agents">Agents</a></li>
    </ul>
  </nav>
</header>

<main>
  <article>
    <h1>Agent 详情</h1>
    <section>
      <h2>基本信息</h2>
      <p>...</p>
    </section>
  </article>
</main>

<footer>
  <p>© 2024 AI Agents Platform</p>
</footer>

// ❌ 错误 - div 滥用
<div className="header">
  <div className="nav">
    <div onClick={...}>首页</div>
  </div>
</div>
```

### 1.2 按钮 vs 链接

```tsx
// ✅ 按钮 - 执行操作
<button onClick={handleSubmit}>提交</button>
<button onClick={handleDelete}>删除</button>

// ✅ 链接 - 导航到其他页面
<a href="/agents">查看 Agents</a>
<Link to="/agents/123">Agent 详情</Link>

// ❌ 错误 - div 作为按钮
<div onClick={handleClick} className="button">点击</div>

// ❌ 错误 - 链接执行操作
<a href="#" onClick={handleSubmit}>提交</a>
```

### 1.3 标题层级

```tsx
// ✅ 正确 - 有序层级
<h1>页面标题</h1>
<section>
  <h2>主要章节</h2>
  <h3>子章节</h3>
</section>
<section>
  <h2>另一个章节</h2>
</section>

// ❌ 错误 - 跳过层级
<h1>页面标题</h1>
<h3>直接到 h3</h3>  {/* 跳过了 h2 */}
```

---

## 2. 表单无障碍

### 2.1 标签关联

```tsx
// ✅ 正确 - 显式关联
<label htmlFor="email">邮箱</label>
<input id="email" type="email" />

// ✅ 正确 - 隐式关联
<label>
  邮箱
  <input type="email" />
</label>

// ✅ 正确 - 使用 aria-label (无可见标签时)
<input type="search" aria-label="搜索 Agents" placeholder="搜索..." />

// ❌ 错误 - 无标签
<input type="email" placeholder="邮箱" />  {/* placeholder 不是标签 */}
```

### 2.2 错误提示

```tsx
interface InputProps {
  id: string;
  label: string;
  error?: string;
}

function FormInput({ id, label, error, ...props }: InputProps) {
  const errorId = `${id}-error`;

  return (
    <div>
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        {...props}
      />
      {error && (
        <span id={errorId} role="alert" className="text-red-500">
          {error}
        </span>
      )}
    </div>
  );
}
```

### 2.3 必填字段

```tsx
<label htmlFor="name">
  姓名
  <span aria-hidden="true" className="text-red-500">*</span>
</label>
<input
  id="name"
  required
  aria-required="true"
/>
```

---

## 3. ARIA 使用

### 3.1 图标按钮

```tsx
// ✅ 正确 - aria-label 描述功能
<button aria-label="关闭对话框" onClick={onClose}>
  <CloseIcon aria-hidden="true" />
</button>

<button aria-label="删除 Agent" onClick={onDelete}>
  <TrashIcon aria-hidden="true" />
</button>

// ❌ 错误 - 无标签
<button onClick={onClose}>
  <CloseIcon />
</button>
```

### 3.2 自定义组件

```tsx
// 自定义下拉菜单
function Dropdown({ label, options, value, onChange }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-labelledby="dropdown-label"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span id="dropdown-label">{label}: </span>
        <span>{value}</span>
      </button>

      {isOpen && (
        <ul
          role="listbox"
          aria-labelledby="dropdown-label"
          className="absolute"
        >
          {options.map((option) => (
            <li
              key={option.value}
              role="option"
              aria-selected={option.value === value}
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### 3.3 Tab 组件

```tsx
function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div>
      <div role="tablist" aria-label="功能选项卡">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {tabs.map((tab) => (
        <div
          key={tab.id}
          role="tabpanel"
          id={`panel-${tab.id}`}
          aria-labelledby={`tab-${tab.id}`}
          hidden={activeTab !== tab.id}
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
}
```

---

## 4. 键盘导航

### 4.1 焦点管理

```tsx
// 模态框打开时聚焦
function Modal({ isOpen, onClose, children }: ModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      closeButtonRef.current?.focus();
    }
  }, [isOpen]);

  return (
    <dialog open={isOpen} aria-modal="true">
      <button ref={closeButtonRef} onClick={onClose} aria-label="关闭">
        ×
      </button>
      {children}
    </dialog>
  );
}
```

### 4.2 焦点陷阱

```tsx
import { FocusTrap } from '@headlessui/react';

function Modal({ isOpen, children }: ModalProps) {
  return (
    <dialog open={isOpen}>
      <FocusTrap>
        <div className="modal-content">
          {children}
        </div>
      </FocusTrap>
    </dialog>
  );
}
```

### 4.3 跳过链接

```tsx
// 跳过导航到主内容
function Layout({ children }: LayoutProps) {
  return (
    <>
      <a href="#main-content" className="skip-link">
        跳过导航到主内容
      </a>
      <header>
        <nav>{/* 导航内容 */}</nav>
      </header>
      <main id="main-content" tabIndex={-1}>
        {children}
      </main>
    </>
  );
}

// CSS
.skip-link {
  position: absolute;
  left: -9999px;
}
.skip-link:focus {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
}
```

---

## 5. 视觉无障碍

### 5.1 颜色对比度

```css
/* ✅ 正确 - 对比度 >= 4.5:1 */
.text-primary {
  color: #1f2937;  /* 深灰 */
  background-color: #ffffff;
}

.error-text {
  color: #dc2626;  /* 红色 */
  /* 确保与背景对比度足够 */
}

/* ❌ 错误 - 对比度不足 */
.low-contrast {
  color: #9ca3af;  /* 浅灰 */
  background-color: #ffffff;
}
```

### 5.2 不仅依赖颜色

```tsx
// ✅ 正确 - 颜色 + 图标 + 文字
<div className="error">
  <ErrorIcon aria-hidden="true" />
  <span className="text-red-500">错误: 邮箱格式无效</span>
</div>

// ✅ 正确 - 状态不仅用颜色区分
<span className={cn('status', status === 'active' ? 'bg-green-500' : 'bg-gray-300')}>
  {status === 'active' ? '● 活跃' : '○ 未激活'}
</span>

// ❌ 错误 - 仅用颜色区分
<span className={status === 'active' ? 'text-green-500' : 'text-red-500'}>
  状态  {/* 色盲用户无法区分 */}
</span>
```

### 5.3 焦点样式

```css
/* 确保焦点可见 */
:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

/* 不要移除焦点样式 */
/* ❌ 禁止 */
:focus {
  outline: none;
}
```

---

## 6. 图片和媒体

### 6.1 Alt 文本

```tsx
// ✅ 有意义的图片 - 描述性 alt
<img src="/agent-avatar.png" alt="Agent 头像: 机器人图标" />

// ✅ 装饰性图片 - 空 alt
<img src="/decorative-pattern.svg" alt="" />

// ✅ 功能性图片 - 描述功能
<img src="/search-icon.svg" alt="搜索" />

// ❌ 错误 - 无用的 alt
<img src="/photo.jpg" alt="图片" />
<img src="/photo.jpg" alt="photo.jpg" />
```

### 6.2 SVG 无障碍

```tsx
// ✅ 正确 - SVG 作为图片
<svg role="img" aria-label="设置图标">
  <title>设置</title>
  <path d="..." />
</svg>

// ✅ 正确 - 装饰性 SVG
<svg aria-hidden="true">
  <path d="..." />
</svg>
```

---

## 7. 测试工具

### 7.1 自动化测试

```bash
# 使用 axe-core
pnpm add -D @axe-core/react

# 在开发环境中使用
```

```typescript
// app/index.tsx (开发环境)
import React from 'react';

if (process.env.NODE_ENV === 'development') {
  import('@axe-core/react').then((axe) => {
    axe.default(React, ReactDOM, 1000);
  });
}
```

### 7.2 测试中检查

```typescript
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

it('should have no accessibility violations', async () => {
  const { container } = render(<LoginForm />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [component-design.md](component-design.md) | 组件设计 |
| [testing.md](testing.md) | 无障碍测试 |
| [WCAG 2.1](https://www.w3.org/WAI/WCAG21/quickref/) | 官方指南 |
