> **职责**: 无障碍规范 - WCAG 2.1 AA、ARIA 使用、键盘导航 (基于 POUR 原则)

# 无障碍规范 (Accessibility Standards)

---

## 0. 速查卡片

### POUR 原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **可感知** | 信息可被用户感知 | 图片有 alt，视频有字幕 |
| **可操作** | 界面可被用户操作 | 键盘可访问，无时间限制 |
| **可理解** | 内容可被用户理解 | 清晰标签，一致导航 |
| **健壮性** | 兼容辅助技术 | 语义化 HTML，ARIA |

### ARIA 属性速查

| 属性 | 用途 | 示例 |
|------|------|------|
| `aria-label` | 为元素提供标签 | `<button aria-label="关闭">×</button>` |
| `aria-labelledby` | 引用其他元素作为标签 | `<div aria-labelledby="title-id">` |
| `aria-describedby` | 引用描述性文本 | `<input aria-describedby="error-id">` |
| `aria-hidden` | 从无障碍树中隐藏 | `<span aria-hidden="true">🎨</span>` |
| `aria-expanded` | 展开/折叠状态 | `<button aria-expanded="true">` |
| `aria-current` | 当前项目标记 | `<a aria-current="page">` |
| `aria-invalid` | 无效输入状态 | `<input aria-invalid="true">` |
| `aria-required` | 必填字段 | `<input aria-required="true">` |

### Alt 文本规则

| 图片类型 | Alt 处理 | 示例 |
|---------|---------|------|
| 有意义的图片 | 描述性文本 | `alt="Agent 头像: 机器人图标"` |
| 装饰性图片 | 空 alt | `alt=""` |
| 功能性图片 | 描述功能 | `alt="搜索"` |
| SVG 图标 | `aria-hidden` 或 `role="img"` | `<svg aria-hidden="true">` |

### PR Review 检查清单

- [ ] 图片有描述性 alt 文本
- [ ] 表单控件有关联的 label
- [ ] 可交互元素可通过键盘访问
- [ ] 颜色对比度 >= 4.5:1
- [ ] 焦点顺序合理且可见
- [ ] 错误信息与输入框关联 (`aria-describedby`)
- [ ] 图标按钮有 `aria-label`

---

## 1. 语义化规则

### 元素选择规则

| 场景 | ✅ 正确 | ❌ 错误 |
|------|--------|--------|
| 页面结构 | `<header>`, `<main>`, `<footer>` | `<div class="header">` |
| 导航 | `<nav>` | `<div class="nav">` |
| 执行操作 | `<button onClick={}>` | `<div onClick={}>` |
| 页面跳转 | `<a href="">`, `<Link to="">` | `<a href="#" onClick={}>` |

**按钮 vs 链接**: 操作用 `<button>`，导航用 `<a>` 或 `<Link>`

---

## 2. 表单无障碍

### 2.1 标签关联

```tsx
// ✅ 显式关联
<label htmlFor="email">邮箱</label>
<input id="email" type="email" />

// ✅ 隐式关联
<label>
  邮箱
  <input type="email" />
</label>

// ✅ 无可见标签时使用 aria-label
<input type="search" aria-label="搜索 Agents" placeholder="搜索..." />

// ❌ 错误 - placeholder 不是标签
<input type="email" placeholder="邮箱" />
```

### 2.2 错误提示组件

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
<input id="name" required aria-required="true" />
```

---

## 3. ARIA 模式

### 3.1 图标按钮

```tsx
// ✅ 正确 - aria-label 描述功能
<button aria-label="关闭对话框" onClick={onClose}>
  <CloseIcon aria-hidden="true" />
</button>

// ❌ 错误 - 无标签
<button onClick={onClose}>
  <CloseIcon />
</button>
```

### 3.2 自定义组件 ARIA 属性表

| 组件 | 必需属性 | 可选属性 |
|------|---------|---------|
| **Dropdown** | `role="listbox"`, `aria-expanded`, `aria-labelledby` | `aria-activedescendant` |
| **Option** | `role="option"`, `aria-selected` | - |
| **Tab** | `role="tab"`, `aria-selected`, `aria-controls` | `tabIndex` |
| **TabPanel** | `role="tabpanel"`, `aria-labelledby` | `hidden` |
| **TabList** | `role="tablist"`, `aria-label` | - |
| **Dialog** | `role="dialog"`, `aria-modal`, `aria-labelledby` | `aria-describedby` |

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
// 使用 @headlessui/react 或类似库
import { FocusTrap } from '@headlessui/react';

function Modal({ isOpen, children }: ModalProps) {
  return (
    <dialog open={isOpen}>
      <FocusTrap>
        <div className="modal-content">{children}</div>
      </FocusTrap>
    </dialog>
  );
}
```

### 4.3 跳过链接

```tsx
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
```

---

## 5. 视觉无障碍

### 5.1 颜色规则

| 规则 | 要求 |
|------|------|
| 文本对比度 | >= 4.5:1 (正常文本), >= 3:1 (大文本) |
| 不仅依赖颜色 | 颜色 + 图标 + 文字组合区分状态 |

```tsx
// ✅ 正确 - 颜色 + 图标 + 文字
<span className={status === 'active' ? 'text-green-500' : 'text-gray-500'}>
  {status === 'active' ? '● 活跃' : '○ 未激活'}
</span>

// ❌ 错误 - 仅用颜色区分
<span className={status === 'active' ? 'text-green-500' : 'text-red-500'}>
  状态
</span>
```

### 5.2 焦点样式

```css
/* 确保焦点可见 */
:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

/* ❌ 禁止移除焦点样式 */
/* :focus { outline: none; } */
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [component-design.md](component-design.md) | 组件设计 |
| [testing.md](testing.md) | 无障碍测试 (jest-axe) |
| [WCAG 2.1](https://www.w3.org/WAI/WCAG21/quickref/) | 官方指南 |
