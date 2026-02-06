> **职责**: 测试规范 - TDD 工作流、测试分层、覆盖率要求

# 测试规范 (Testing Standards)

---

## 0. 速查卡片

### 命令

> 测试命令详见 [CLAUDE.md](../CLAUDE.md) §测试

### 命名

| 元素 | 模式 | 示例 |
|------|------|------|
| 测试文件 | `{Component}.test.tsx` | `Button.test.tsx` |
| 测试描述 | `describe('{Component}')` | `describe('Button')` |
| 测试用例 | `it('should {behavior}')` | `it('should render children')` |
| E2E 文件 | `{feature}.spec.ts` | `auth.spec.ts` |

### 分层

| 层级 | 覆盖 | Mock | 工具 |
|------|------|------|------|
| Unit | Hook/组件/工具 | 外部依赖 | Vitest + Testing Library |
| Integration | 页面/API 集成 | 外部服务 | Vitest + MSW |
| E2E | 用户流程 | 无 | Playwright |

### 陷阱 ⚠️

- ❌ 测试实现细节 → ✅ 测试行为
- ❌ `getByTestId` 优先 → ✅ 可访问性查询优先
- ❌ 同步期望异步 → ✅ `waitFor` / `findBy`

### PR Review 检查清单

完整检查清单见 [checklist.md](checklist.md) §测试

---

## 1. 测试文件位置

```
# 单元测试 - 与组件同目录
shared/ui/Button/
├── Button.tsx
└── Button.test.tsx

# E2E 测试 - 独立目录
tests/
├── e2e/auth.spec.ts
└── fixtures/users.json
```

---

## 2. 组件测试

### 2.1 基本模板

```typescript
// Button.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

describe('Button', () => {
  it('should render children', () => {
    render(<Button>点击</Button>);
    expect(screen.getByRole('button', { name: '点击' })).toBeInTheDocument();
  });

  it('should call onClick', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    render(<Button onClick={handleClick}>点击</Button>);
    await user.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### 2.2 查询优先级

```typescript
// ✅ 推荐 (按优先级)
screen.getByRole('button', { name: '提交' });  // 1. 角色
screen.getByLabelText('用户名');               // 2. 标签
screen.getByPlaceholderText('请输入');         // 3. 占位符
screen.getByText('欢迎');                      // 4. 文本
// ❌ 最后选择
screen.getByTestId('custom-element');
```

### 2.3 异步测试

```typescript
it('should load data', async () => {
  render(<AsyncComponent />);
  expect(await screen.findByText('加载完成')).toBeInTheDocument();
});
```

---

## 3. Hook 测试

```typescript
import { renderHook, act } from '@testing-library/react';
import { vi, beforeEach, afterEach } from 'vitest';

describe('useDebounce', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('should debounce value', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'hello' } }
    );
    rerender({ value: 'world' });
    expect(result.current).toBe('hello');
    act(() => vi.advanceTimersByTime(500));
    expect(result.current).toBe('world');
  });
});
```

---

## 4. API Mock (MSW)

### 4.1 配置

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/v1/agents', () => HttpResponse.json([{ id: '1', name: 'Agent 1' }])),
  http.post('/api/v1/auth/login', async ({ request }) => {
    const body = await request.json();
    return body.email === 'test@example.com'
      ? HttpResponse.json({ token: 'fake-token' })
      : HttpResponse.json({ message: '错误' }, { status: 401 });
  }),
];

// tests/mocks/server.ts
import { setupServer } from 'msw/node';
export const server = setupServer(...handlers);

// tests/setup.ts
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### 4.2 集成测试

```typescript
// 测试 wrapper
function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe('LoginForm', () => {
  it('should handle error', async () => {
    server.use(http.post('/api/v1/auth/login', () => HttpResponse.json({ message: '错误' }, { status: 401 })));
    const user = userEvent.setup();
    renderWithProviders(<LoginForm onSuccess={vi.fn()} />);
    await user.type(screen.getByLabelText('邮箱'), 'wrong@example.com');
    await user.type(screen.getByLabelText('密码'), 'wrongpass');
    await user.click(screen.getByRole('button', { name: '登录' }));
    await waitFor(() => expect(screen.getByText(/错误/)).toBeInTheDocument());
  });
});
```

---

## 5. E2E 测试 (Playwright)

### 5.1 基本模板

```typescript
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should login', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('邮箱').fill('test@example.com');
    await page.getByLabel('密码').fill('password123');
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });
});
```

### 5.2 Page Object 模式

```typescript
export class LoginPage {
  constructor(private page: Page) {}
  readonly emailInput = () => this.page.getByLabel('邮箱');
  readonly passwordInput = () => this.page.getByLabel('密码');
  readonly submitButton = () => this.page.getByRole('button', { name: '登录' });

  async goto() { await this.page.goto('/login'); }
  async login(email: string, password: string) {
    await this.emailInput().fill(email);
    await this.passwordInput().fill(password);
    await this.submitButton().click();
  }
}
```

---

## 6. 测试配置

### Vitest

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: { provider: 'v8', reporter: ['text', 'html'] },
  },
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
});
```

### Playwright

```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  use: { baseURL: 'http://localhost:5173', trace: 'on-first-retry' },
  webServer: { command: 'pnpm dev', url: 'http://localhost:5173' },
});
```

---

## 7. 覆盖率要求

| 层级 | 最低 | 目标 |
|------|-----|------|
| Hooks | 90% | 95% |
| Components | 80% | 85% |
| Utils | 95% | 100% |
| **整体** | **80%** | **85%** |

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [component-design.md](component-design.md) | 组件设计模式 |
| [state-management.md](state-management.md) | 状态管理 (React Query Mock) |
| [CLAUDE.md](../CLAUDE.md) | TDD 工作流 |
