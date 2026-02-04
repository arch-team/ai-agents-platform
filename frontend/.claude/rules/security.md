# 前端安全规范 (Frontend Security Standards)

> Claude 生成代码时优先查阅此文档

基于 OWASP 前端安全最佳实践的 React + TypeScript 安全规范。

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

- [ ] 没有 `dangerouslySetInnerHTML` (除非必要且使用 DOMPurify)
- [ ] 敏感数据不存储在 localStorage
- [ ] 环境变量使用 `VITE_` 前缀
- [ ] 用户输入有验证
- [ ] API 调用使用 HTTPS
- [ ] 没有硬编码的密钥或密码

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

// <script> 会被转义为 &lt;script&gt;
<Comment text="<script>alert('xss')</script>" />
```

### 2.2 危险操作

```tsx
// ❌ 危险 - 除非绝对必要且经过清洗
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// ✅ 如果必须使用，先清洗
import DOMPurify from 'dompurify';

function RichContent({ html }: { html: string }) {
  const cleanHtml = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
    ALLOWED_ATTR: ['href'],
  });

  return <div dangerouslySetInnerHTML={{ __html: cleanHtml }} />;
}
```

### 2.3 URL 安全

```tsx
// ❌ 危险 - javascript: 协议
<a href={userProvidedUrl}>链接</a>

// ✅ 安全 - 验证 URL
function SafeLink({ href, children }: { href: string; children: React.ReactNode }) {
  const isValidUrl = (url: string): boolean => {
    try {
      const parsed = new URL(url);
      return ['http:', 'https:', 'mailto:'].includes(parsed.protocol);
    } catch {
      return false;
    }
  };

  if (!isValidUrl(href)) {
    return <span>{children}</span>;
  }

  return (
    <a href={href} rel="noopener noreferrer" target="_blank">
      {children}
    </a>
  );
}
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

### 3.2 实现示例

```typescript
// ❌ 错误 - localStorage 存储 token
localStorage.setItem('token', token);

// ✅ 正确 - 内存存储 (Zustand 不持久化)
const useAuthStore = create<AuthState>((set) => ({
  token: null,
  setToken: (token) => set({ token }),
}));

// ✅ 正确 - httpOnly Cookie (后端设置)
// 前端只需发送请求，Cookie 自动携带
const response = await apiClient.get('/api/v1/auth/me', {
  withCredentials: true,
});
```

### 3.3 敏感信息清理

```typescript
// 退出登录时清理
function logout() {
  // 清理内存状态
  useAuthStore.getState().logout();

  // 清理 sessionStorage
  sessionStorage.clear();

  // 通知后端清理 Cookie
  await apiClient.post('/api/v1/auth/logout');
}
```

---

## 4. 环境变量安全

### 4.1 命名规范

```bash
# .env.example

# ✅ 公开配置 - VITE_ 前缀
VITE_API_BASE_URL=https://api.example.com
VITE_APP_TITLE=AI Agents Platform

# ❌ 禁止 - 敏感信息不应出现在前端
# API_SECRET_KEY=xxx  # 永远不要这样做
```

### 4.2 使用方式

```typescript
// ✅ 正确 - 通过 import.meta.env 访问
const apiUrl = import.meta.env.VITE_API_BASE_URL;

// ✅ 正确 - 类型安全
// src/vite-env.d.ts
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_APP_TITLE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

### 4.3 环境变量检查

```typescript
// shared/config/env.ts
function getEnvVar(key: keyof ImportMetaEnv): string {
  const value = import.meta.env[key];
  if (!value) {
    throw new Error(`环境变量 ${key} 未配置`);
  }
  return value;
}

export const config = {
  apiBaseUrl: getEnvVar('VITE_API_BASE_URL'),
  appTitle: getEnvVar('VITE_APP_TITLE'),
};
```

---

## 5. 输入验证

### 5.1 表单验证

```typescript
import { z } from 'zod';

// 定义验证 schema
const loginSchema = z.object({
  email: z
    .string()
    .email('请输入有效的邮箱')
    .max(254, '邮箱过长'),
  password: z
    .string()
    .min(8, '密码至少 8 位')
    .max(128, '密码过长')
    .regex(/[A-Z]/, '需要包含大写字母')
    .regex(/[a-z]/, '需要包含小写字母')
    .regex(/[0-9]/, '需要包含数字'),
});

// 在表单中使用
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(loginSchema),
});
```

### 5.2 URL 参数验证

```typescript
import { useSearchParams } from 'react-router-dom';

function AgentPage() {
  const [searchParams] = useSearchParams();
  const agentId = searchParams.get('id');

  // ✅ 验证参数格式
  const isValidId = agentId && /^[a-zA-Z0-9-]+$/.test(agentId);

  if (!isValidId) {
    return <div>无效的 Agent ID</div>;
  }

  return <AgentDetail id={agentId} />;
}
```

---

## 6. API 安全

### 6.1 请求配置

```typescript
// shared/api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  withCredentials: true, // 发送 Cookie
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加 Token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 处理 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 6.2 CSRF 防护

```typescript
// 如果使用 Cookie 认证，确保后端设置了 CSRF Token
apiClient.interceptors.request.use((config) => {
  // 从 Cookie 或 meta 标签获取 CSRF Token
  const csrfToken = document.querySelector('meta[name="csrf-token"]')
    ?.getAttribute('content');

  if (csrfToken) {
    config.headers['X-CSRF-Token'] = csrfToken;
  }

  return config;
});
```

---

## 7. 第三方依赖安全

### 7.1 依赖审计

```bash
# 检查已知漏洞
pnpm audit

# 自动修复
pnpm audit --fix

# CI 中检查
pnpm audit --audit-level=high
```

### 7.2 SRI 校验

```html
<!-- 对于外部脚本，使用 SRI -->
<script
  src="https://cdn.example.com/lib.js"
  integrity="sha384-..."
  crossorigin="anonymous"
></script>
```

### 7.3 CSP 配置

```html
<!-- index.html -->
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline' 'unsafe-eval';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.example.com;
">
```

---

## 8. 常见漏洞检查清单

### 代码审查

- [ ] 没有 `dangerouslySetInnerHTML` (或已用 DOMPurify 清洗)
- [ ] 没有 `eval()`, `new Function()`
- [ ] URL 跳转有验证
- [ ] 用户输入有验证和限制
- [ ] 敏感数据不在 localStorage
- [ ] 没有硬编码的密钥

### 配置检查

- [ ] 所有环境变量使用 `VITE_` 前缀
- [ ] `.env` 文件在 `.gitignore` 中
- [ ] 依赖定期更新和审计
- [ ] 生产构建移除 console.log

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [state-management.md](state-management.md) | Token 存储策略 |
| [testing.md](testing.md) | 安全测试 |
| [OWASP 前端安全清单](https://cheatsheetseries.owasp.org/cheatsheets/AJAX_Security_Cheat_Sheet.html) | 外部参考 |
