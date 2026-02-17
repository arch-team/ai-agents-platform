import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { EvaluationResults } from './EvaluationResults';

const API_BASE = 'http://localhost:8000';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('EvaluationResults', () => {
  it('应显示加载状态', () => {
    render(<EvaluationResults runId={1} />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示评估运行概览', async () => {
    render(<EvaluationResults runId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('评估运行 #1')).toBeInTheDocument();
    });

    // 通过率
    expect(screen.getByText('80.0%')).toBeInTheDocument();
    // 得分
    expect(screen.getByText('0.85')).toBeInTheDocument();
    // 用例统计
    expect(screen.getByText(/8 通过/)).toBeInTheDocument();
    expect(screen.getByText(/2 失败/)).toBeInTheDocument();
  });

  it('应显示评估结果列表', async () => {
    render(<EvaluationResults runId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('list', { name: '评估结果列表' })).toBeInTheDocument();
    });

    // 通过的结果
    expect(screen.getByText('通过')).toBeInTheDocument();
    // 未通过的结果
    expect(screen.getByText('未通过')).toBeInTheDocument();
    // 错误信息
    expect(screen.getByText('超时未响应')).toBeInTheDocument();
  });

  it('运行详情加载失败时应显示错误', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/evaluation-runs/:id`, () =>
        HttpResponse.json({ message: '未找到' }, { status: 404 }),
      ),
    );

    render(<EvaluationResults runId={999} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
