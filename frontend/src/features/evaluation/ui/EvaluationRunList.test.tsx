import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { EvaluationRunList } from './EvaluationRunList';

const API_BASE = 'http://localhost:8000';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('EvaluationRunList', () => {
  it('应显示加载状态', () => {
    render(<EvaluationRunList />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示评估运行列表', async () => {
    render(<EvaluationRunList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('运行 #1')).toBeInTheDocument();
    });

    // 应显示通过率
    expect(screen.getByText('通过率 80.0%')).toBeInTheDocument();
    // 应显示得分
    expect(screen.getByText(/8\/10 通过/)).toBeInTheDocument();
  });

  it('应显示空状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/evaluation-runs`, () =>
        HttpResponse.json({
          items: [],
          total: 0,
          page: 1,
          page_size: 10,
          total_pages: 0,
        }),
      ),
    );

    render(<EvaluationRunList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('暂无评估运行记录')).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/evaluation-runs`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<EvaluationRunList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('点击运行记录应调用 onSelect', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();

    render(<EvaluationRunList onSelect={handleSelect} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('运行 #1')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /查看评估运行 #1/ }));
    expect(handleSelect).toHaveBeenCalledWith(1);
  });
});
