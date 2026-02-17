import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { TestSuiteList } from './TestSuiteList';

const API_BASE = 'http://localhost:8000';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('TestSuiteList', () => {
  it('应显示加载状态', () => {
    render(<TestSuiteList />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示测试集列表', async () => {
    render(<TestSuiteList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('回归测试集')).toBeInTheDocument();
    });
    expect(screen.getByText('性能测试集')).toBeInTheDocument();
  });

  it('应显示空状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/test-suites`, () =>
        HttpResponse.json({
          items: [],
          total: 0,
          page: 1,
          page_size: 10,
          total_pages: 0,
        }),
      ),
    );

    render(<TestSuiteList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('暂无测试集')).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/test-suites`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<TestSuiteList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('点击测试集应调用 onSelect', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();

    render(<TestSuiteList onSelect={handleSelect} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('回归测试集')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /查看测试集: 回归测试集/ }));
    expect(handleSelect).toHaveBeenCalledWith(1);
  });

  it('应在 onCreate 传入时显示创建按钮', async () => {
    const handleCreate = vi.fn();
    const user = userEvent.setup();

    render(<TestSuiteList onCreate={handleCreate} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('回归测试集')).toBeInTheDocument();
    });

    const createButton = screen.getByRole('button', { name: '创建测试集' });
    expect(createButton).toBeInTheDocument();
    await user.click(createButton);
    expect(handleCreate).toHaveBeenCalled();
  });

  it('草稿状态测试集应显示激活和删除按钮', async () => {
    render(<TestSuiteList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('回归测试集')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: '激活 回归测试集' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '删除 回归测试集' })).toBeInTheDocument();
  });

  it('激活状态测试集应显示归档按钮', async () => {
    render(<TestSuiteList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('性能测试集')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: '归档 性能测试集' })).toBeInTheDocument();
  });

  it('应显示状态筛选下拉', async () => {
    render(<TestSuiteList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('回归测试集')).toBeInTheDocument();
    });

    const filter = screen.getByLabelText('状态筛选');
    expect(filter).toBeInTheDocument();
    expect(filter).toHaveValue('');
  });
});
