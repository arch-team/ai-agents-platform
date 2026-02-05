> **职责**: 前端安全规范 - XSS 防护、敏感数据存储、输入验证 (基于 OWASP)

# 前端安全规范 (Frontend Security Standards)

---

## 0. 速查卡片

### 安全规则速查表

| 规则 | ❌ 禁止 | ✅ 正确 |
|------|--------|--------|
| XSS | `dangerouslySetInnerHTML` | React 自动转义 / DOMPurify |
| 敏感存储 | `localStorage.setItem('token')` | httpOnly Cookie / 内存 |
| API 密钥 | 硬编码在代码中 | `VITE_` 前缀环境变量 |
| URL 参数 | 直接拼接 | `URLSearchParams` / 验证 |
| 第三方脚本 | 直接引入 | SRI 校验 / CSP |

### 检测命令

```bash
# 依赖漏洞检查
pnpm audit

# 敏感信息检测
grep -rE "(password|secret|token|key)\s*[:=]" src/
```

### PR Review 检查清单

**代码审查**:
- [ ] 没有 `dangerouslySetInnerHTML` (除非必要且使用 DOMPurify)
- [ ] 没有 `eval()`, `new Function()`
- [ ] URL 跳转有验证
- [ ] 用户输入有验证和限制
- [ ] 敏感数据不在 localStorage
- [ ] 没有硬编码的密钥

**配置检查**:
- [ ] 所有环境变量使用 `VITE_` 前缀
- [ ] `.env` 文件在 `.gitignore` 中
- [ ] 依赖定期更新和审计
- [ ] 生产构建移除 console.log

---

## 1. 核心原则

| 原则 | 说明 |
|------|------|
| **输入验证** | 所有用户输入都是不可信的 |
| **最小权限** | 只请求必要的 API 权限和数据 |
| **安全默认** | React 默认转义 HTML，保持这个行为 |
| **深度防御** | 前端验证 + 后端验证双重保护 |

---

## 2. XSS 防护

### 2.1 React 自动转义

```tsx
// ✅ 安全 - React 自动转义
function Comment({ text }: { text: string }) {
  return <p>{text}</p>;  // 自动转义 HTML 标签
}
```

### 2.2 危险操作

```tsx
// ❌ 危险 - 除非绝对必要且经过清洗
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// ✅ 如果必须使用，先清洗
import DOMPurify from 'dompurify';

const cleanHtml = DOMPurify.sanitize(html, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
  ALLOWED_ATTR: ['href'],
});
<div dangerouslySetInnerHTML={{ __html: cleanHtml }} />
```

### 2.3 URL 安全

```tsx
// ❌ 危险 - javascript: 协议
<a href={userProvidedUrl}>链接</a>

// ✅ 安全 - 验证协议
const isValidUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:', 'mailto:'].includes(parsed.protocol);
  } catch {
    return false;
  }
};

// 使用时验证并添加安全属性
{isValidUrl(href) && <a href={href} rel="noopener noreferrer" target="_blank">链接</a>}
```

---

## 3. 敏感数据存储

### 3.1 Token 存储策略

| 存储方式 | 安全性 | 推荐场景 |
|---------|-------|---------|
| httpOnly Cookie | ✅ 最安全 | 首选 (需后端配合) |
| 内存 (Zustand 不持久化) | ✅ 安全 | 短期会话 |
| sessionStorage | ⚠️ 中等 | 标签页级别会话 |
| localStorage | ❌ 不安全 | **禁止存储敏感数据** |

### 3.2 实现要点

```typescript
// ❌ 错误 - localStorage 存储 token
localStorage.setItem('token', token);

// ✅ 正确 - 内存存储或 httpOnly Cookie
// 详细实现参考 state-management.md §2.1
```

> **详细实现**: 参考 [state-management.md](state-management.md) §2 Zustand Store 模板

---

## 4. 环境变量安全

### 命名规范

```bash
# .env.example

# ✅ 公开配置 - VITE_ 前缀
VITE_API_BASE_URL=https://api.example.com
VITE_APP_TITLE=AI Agents Platform

# ❌ 禁止 - 敏感信息不应出现在前端
# API_SECRET_KEY=xxx  # 永远不要这样做
```

### 使用方式

```typescript
// ✅ 正确 - 通过 import.meta.env 访问
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

---

## 5. 输入验证

### 验证规则

| 输入类型 | 验证方式 |
|---------|---------|
| 表单输入 | Zod schema + React Hook Form |
| URL 参数 | 正则验证 + 白名单 |
| API 响应 | 类型校验 |

### 示例

```typescript
// 表单验证 - 详细模式参考 state-management.md §3
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email('请输入有效的邮箱'),
  password: z.string().min(8, '密码至少 8 位'),
});

// URL 参数验证
const agentId = searchParams.get('id');
const isValidId = agentId && /^[a-zA-Z0-9-]+$/.test(agentId);
```

> **详细实现**: 参考 [state-management.md](state-management.md) §3 React Hook Form

---

## 6. API 安全

### CSRF 防护

```typescript
// Cookie 认证时，从 meta 标签获取 CSRF Token
const csrfToken = document.querySelector('meta[name="csrf-token"]')
  ?.getAttribute('content');

if (csrfToken) {
  config.headers['X-CSRF-Token'] = csrfToken;
}
```

### 请求配置

> **Axios 配置**: API 客户端配置（拦截器、Token 注入）应放在 `shared/api/client.ts`，
> 参考项目架构规范 [architecture.md](architecture.md) §2.1

---

## 7. 第三方依赖安全

### 依赖审计

```bash
# 检查已知漏洞
pnpm audit

# 自动修复
pnpm audit --fix

# CI 中检查 (高危漏洞阻断)
pnpm audit --audit-level=high
```

### SRI 校验

```html
<!-- 外部脚本使用 SRI -->
<script
  src="https://cdn.example.com/lib.js"
  integrity="sha384-..."
  crossorigin="anonymous"
></script>
```

### CSP 配置

```html
<!-- index.html - 根据项目需求调整 -->
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  connect-src 'self' https://api.example.com;
">
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [state-management.md](state-management.md) | Token 存储实现、表单验证 |
| [testing.md](testing.md) | 安全测试 |
| [OWASP 前端安全清单](https://cheatsheetseries.owasp.org/cheatsheets/AJAX_Security_Cheat_Sheet.html) | 外部参考 |
