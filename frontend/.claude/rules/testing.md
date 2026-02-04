# 测试规范 (Testing Standards)

> TDD 工作流见 CLAUDE.md

---

## 0. 速查卡片

### 命令

```bash
pnpm test                         # 运行所有测试
pnpm test:coverage                # 测试 + 覆盖率
pnpm test:ui                      # UI 模式
pnpm test:e2e                     # E2E 测试 (Playwright)
pnpm test src/features/auth/      # 指定目录
pnpm test --watch                 # 监听模式
```

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
- ❌ 使用 `getByTestId` 优先 → ✅ 使用可访问性查询优先
- ❌ 同步期望异步操作 → ✅ 使用 `waitFor` / `findBy`

### PR Review 检查清单

- [ ] 测试文件与组件同目录
- [ ] 测试描述清晰
- [ ] 使用可访问性查询
- [ ] 异步操作正确等待
- [ ] Mock 仅边界依赖

---

## 1. 测试文件位置

### 单元测试 (与组件同目录)

```
shared/ui/Button/
├── index.ts
├── Button.tsx
└── Button.test.tsx       # 单元测试

features/auth/ui/
├── LoginForm.tsx
└── LoginForm.test.tsx    # 单元测试

shared/hooks/
├── useDebounce.ts
└── useDebounce.test.ts   # Hook 测试
```

### E2E 测试 (独立目录)

```
tests/
├── e2e/
│   ├── auth.spec.ts      # 认证流程
│   ├── agents.spec.ts    # Agent 管理流程
│   └── setup.ts          # 全局设置
├── fixtures/
│   └── users.json        # 测试数据
└── playwright.config.ts
```

---

## 2. 组件测试

### 2.1 基本模板

```typescript
// shared/ui/Button/Button.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

describe('Button', () => {
  it('should render children', () => {
    render(<Button>点击</Button>);
    expect(screen.getByRole('button', { name: '点击' })).toBeInTheDocument();
  });

  it('should call onClick when clicked', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<Button onClick={handleClick}>点击</Button>);
    await user.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>点击</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('should show loading state', () => {
    render(<Button loading>点击</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText('⏳')).toBeInTheDocument();
  });
});
```

### 2.2 查询优先级

```typescript
// ✅ 推荐 - 可访问性查询 (按优先级)
screen.getByRole('button', { name: '提交' });  // 1. 角色 + 名称
screen.getByLabelText('用户名');               // 2. 标签
screen.getByPlaceholderText('请输入');         // 3. 占位符
screen.getByText('欢迎');                      // 4. 文本
screen.getByDisplayValue('当前值');            // 5. 表单值

// ⚠️ 次选 - 语义查询
screen.getByAltText('头像');                   // 图片 alt
screen.getByTitle('提示');                     // title 属性

// ❌ 最后选择 - 仅当其他方式不可行时
screen.getByTestId('custom-element');          // data-testid
```

### 2.3 异步测试

```typescript
import { render, screen, waitFor } from '@testing-library/react';

describe('AsyncComponent', () => {
  it('should load data', async () => {
    render(<AsyncComponent />);

    // 等待元素出现
    const item = await screen.findByText('加载完成');
    expect(item).toBeInTheDocument();
  });

  it('should wait for state change', async () => {
    const user = userEvent.setup();
    render(<Form />);

    await user.type(screen.getByLabelText('邮箱'), 'test@example.com');
    await user.click(screen.getByRole('button', { name: '提交' }));

    // waitFor 等待断言通过
    await waitFor(() => {
      expect(screen.getByText('提交成功')).toBeInTheDocument();
    });
  });
});
```

---

## 3. Hook 测试

```typescript
// shared/hooks/useDebounce.test.ts
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useDebounce } from './useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should return initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('hello', 500));
    expect(result.current).toBe('hello');
  });

  it('should debounce value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'hello', delay: 500 } }
    );

    // 更新值
    rerender({ value: 'world', delay: 500 });

    // 立即检查 - 还是旧值
    expect(result.current).toBe('hello');

    // 快进时间
    act(() => {
      vi.advanceTimersByTime(500);
    });

    // 现在是新值
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
  http.get('/api/v1/agents', () => {
    return HttpResponse.json([
      { id: '1', name: 'Agent 1', status: 'active' },
      { id: '2', name: 'Agent 2', status: 'inactive' },
    ]);
  }),

  http.post('/api/v1/auth/login', async ({ request }) => {
    const body = await request.json();
    if (body.email === 'test@example.com') {
      return HttpResponse.json({
        user: { id: '1', email: 'test@example.com' },
        token: 'fake-token',
      });
    }
    return HttpResponse.json(
      { message: '用户名或密码错误' },
      { status: 401 }
    );
  }),
];
```

```typescript
// tests/mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

```typescript
// tests/setup.ts
import { beforeAll, afterEach, afterAll } from 'vitest';
import { server } from './mocks/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### 4.2 集成测试

```typescript
// features/auth/ui/LoginForm.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/tests/mocks/server';
import { LoginForm } from './LoginForm';

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe('LoginForm', () => {
  it('should login successfully', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginForm onSuccess={vi.fn()} />);

    await user.type(screen.getByLabelText('邮箱'), 'test@example.com');
    await user.type(screen.getByLabelText('密码'), 'password123');
    await user.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.queryByText('登录失败')).not.toBeInTheDocument();
    });
  });

  it('should show error on invalid credentials', async () => {
    server.use(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.json(
          { message: '用户名或密码错误' },
          { status: 401 }
        );
      })
    );

    const user = userEvent.setup();
    renderWithProviders(<LoginForm onSuccess={vi.fn()} />);

    await user.type(screen.getByLabelText('邮箱'), 'wrong@example.com');
    await user.type(screen.getByLabelText('密码'), 'wrongpass');
    await user.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText(/错误/)).toBeInTheDocument();
    });
  });
});
```

---

## 5. E2E 测试 (Playwright)

### 5.1 基本模板

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel('邮箱').fill('test@example.com');
    await page.getByLabel('密码').fill('password123');
    await page.getByRole('button', { name: '登录' }).click();

    // 等待跳转到首页
    await expect(page).toHaveURL('/');
    await expect(page.getByText('欢迎回来')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel('邮箱').fill('wrong@example.com');
    await page.getByLabel('密码').fill('wrongpass');
    await page.getByRole('button', { name: '登录' }).click();

    await expect(page.getByText('用户名或密码错误')).toBeVisible();
  });
});
```

### 5.2 Page Object 模式

```typescript
// tests/e2e/pages/LoginPage.ts
import type { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('邮箱');
    this.passwordInput = page.getByLabel('密码');
    this.submitButton = page.getByRole('button', { name: '登录' });
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}

// 使用
test('should login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('test@example.com', 'password123');
  await expect(page).toHaveURL('/');
});
```

---

## 6. 测试配置

### 6.1 Vitest 配置

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'tests/', '**/*.d.ts', '**/*.test.{ts,tsx}'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### 6.2 Playwright 配置

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## 7. 覆盖率要求

| 层级 | 最低覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
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
