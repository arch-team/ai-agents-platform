// SsoLoginButton 组件单元测试

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeAll, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';

import { server } from '../../../../tests/mocks/server';
import { renderWithProviders } from '../../../../tests/utils';

import { SsoLoginButton } from './SsoLoginButton';

const BASE_URL = 'http://localhost:8000';

// 用 vi.fn 拦截 window.location.href 赋值
const mockLocationHref = vi.fn();

beforeAll(() => {
  Object.defineProperty(window, 'location', {
    writable: true,
    value: {
      ...window.location,
      set href(url: string) {
        mockLocationHref(url);
      },
    },
  });
});

afterEach(() => {
  mockLocationHref.mockClear();
});

describe('SsoLoginButton', () => {
  it('应渲染"企业 SSO 登录"按钮', () => {
    renderWithProviders(<SsoLoginButton />);

    expect(screen.getByRole('button', { name: /企业 SSO 登录/ })).toBeInTheDocument();
  });

  it('点击按钮后触发 SSO init 并跳转到 redirect_url', async () => {
    server.use(
      http.post(`${BASE_URL}/api/v1/auth/sso/init`, () =>
        HttpResponse.json({ redirect_url: 'https://sso.example.com/login' }),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<SsoLoginButton />);

    await user.click(screen.getByRole('button', { name: /企业 SSO 登录/ }));

    await waitFor(() => {
      expect(mockLocationHref).toHaveBeenCalledWith('https://sso.example.com/login');
    });
  });

  it('SSO init 失败时显示错误信息', async () => {
    server.use(
      http.post(`${BASE_URL}/api/v1/auth/sso/init`, () =>
        HttpResponse.json({ detail: 'SSO 未配置' }, { status: 400 }),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<SsoLoginButton />);

    await user.click(screen.getByRole('button', { name: /企业 SSO 登录/ }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('请求进行中时按钮显示加载状态（disabled）', async () => {
    let resolveRequest!: () => void;
    server.use(
      http.post(`${BASE_URL}/api/v1/auth/sso/init`, async () => {
        await new Promise<void>((resolve) => {
          resolveRequest = resolve;
        });
        return HttpResponse.json({ redirect_url: 'https://sso.example.com/login' });
      }),
    );

    const user = userEvent.setup();
    // 使用本地 QueryClient，避免全局状态干扰
    const { QueryClient, QueryClientProvider } = await import('@tanstack/react-query');
    const queryClient = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
    const { MemoryRouter } = await import('react-router-dom');
    const { render: localRender } = await import('@testing-library/react');
    const { default: React } = await import('react');

    localRender(
      React.createElement(
        QueryClientProvider,
        { client: queryClient },
        React.createElement(MemoryRouter, null, React.createElement(SsoLoginButton)),
      ),
    );

    // 点击后不 await 完成
    await user.click(screen.getByRole('button', { name: /企业 SSO 登录/ }));

    // 请求发出后按钮应进入 disabled 状态
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /企业 SSO 登录/ })).toBeDisabled();
    });

    // 释放挂起请求
    resolveRequest();
  });
});
