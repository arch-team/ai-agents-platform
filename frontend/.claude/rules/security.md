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

## 2. XSS 防护

### 2.1 dangerouslySetInnerHTML（仅在必要时）

```tsx
// ❌ 危险 - 未经清洗
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// ✅ 如果必须使用，先清洗
import DOMPurify from 'dompurify';

const cleanHtml = DOMPurify.sanitize(html, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
  ALLOWED_ATTR: ['href'],
});
<div dangerouslySetInnerHTML={{ __html: cleanHtml }} />
```

### 2.2 URL 安全

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

{isValidUrl(href) && <a href={href} rel="noopener noreferrer" target="_blank">链接</a>}
```

---

## 3. 敏感数据存储

### Token 存储策略

| 存储方式 | 安全性 | 推荐场景 |
|---------|-------|---------|
| httpOnly Cookie | ✅ 最安全 | 首选 (需后端配合) |
| 内存 (Zustand 不持久化) | ✅ 安全 | 短期会话 |
| sessionStorage | ⚠️ 中等 | 标签页级别会话 |
| localStorage | ❌ 不安全 | **禁止存储敏感数据** |

> Zustand Store 持久化实现详见 state-management.md §2.1

---

## 4. 环境变量安全

```bash
# .env.example

# ✅ 公开配置 - VITE_ 前缀
VITE_API_BASE_URL=https://api.example.com
VITE_APP_TITLE=AI Agents Platform

# ❌ 禁止 - 敏感信息不应出现在前端
# API_SECRET_KEY=xxx  # 永远不要这样做
```

```typescript
// ✅ 通过 import.meta.env 访问
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

---

## 5. 输入验证

| 输入类型 | 验证方式 |
|---------|---------|
| 表单输入 | Zod schema + React Hook Form（详见 state-management.md §3） |
| URL 参数 | 正则验证 + 白名单 |
| API 响应 | 类型校验 |

```typescript
// URL 参数验证
const agentId = searchParams.get('id');
const isValidId = agentId && /^[a-zA-Z0-9-]+$/.test(agentId);
```

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

---

## 7. 第三方依赖安全

### SRI 校验

```html
<!-- 外部脚本必须使用 SRI -->
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
