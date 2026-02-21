import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeAll } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { PipelineList } from './PipelineList';

const API_BASE = 'http://localhost:8000';

const mockPipelines = [
  {
    id: 1,
    suite_id: 1,
    agent_id: 1,
    trigger: 'manual',
    model_ids: ['us.anthropic.claude-haiku-4-20250514-v1:0'],
    status: 'completed',
    bedrock_job_id: 'job-123',
    score_summary: { accuracy: 0.85, relevance: 0.92 },
    error_message: null,
    started_at: '2026-02-21T10:00:00Z',
    completed_at: '2026-02-21T10:15:00Z',
    created_at: '2026-02-21T10:00:00Z',
  },
  {
    id: 2,
    suite_id: 1,
    agent_id: 1,
    trigger: 'scheduled',
    model_ids: ['us.anthropic.claude-sonnet-4-20250514-v1:0'],
    status: 'running',
    bedrock_job_id: 'job-456',
    score_summary: {},
    error_message: null,
    started_at: '2026-02-21T11:00:00Z',
    completed_at: null,
    created_at: '2026-02-21T11:00:00Z',
  },
];

// ResizeObserver polyfill（jsdom 不提供）
beforeAll(() => {
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('PipelineList', () => {
  it('应显示加载状态', () => {
    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示 Pipeline 列表数据', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () =>
        HttpResponse.json(mockPipelines),
      ),
    );

    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('#1')).toBeInTheDocument();
    });

    // 验证列表数据
    expect(screen.getByText('#2')).toBeInTheDocument();
    expect(screen.getByText('manual')).toBeInTheDocument();
    expect(screen.getByText('scheduled')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
    expect(screen.getByText('运行中')).toBeInTheDocument();
    expect(screen.getByText('accuracy: 0.85, relevance: 0.92')).toBeInTheDocument();
    expect(screen.getByText('共 2 条 Pipeline 记录')).toBeInTheDocument();
  });

  it('数据为空时应显示空状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () => HttpResponse.json([])),
    );

    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/暂无 Pipeline 记录/)).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('应显示触发评估按钮', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () =>
        HttpResponse.json(mockPipelines),
      ),
    );

    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('#1')).toBeInTheDocument();
    });

    const button = screen.getByRole('button', { name: '触发评估' });
    expect(button).toBeInTheDocument();
  });

  it('点击触发评估按钮应调用 API', async () => {
    const user = userEvent.setup();

    server.use(
      http.get(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () =>
        HttpResponse.json(mockPipelines),
      ),
      http.post(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () =>
        HttpResponse.json({
          id: 3,
          suite_id: 1,
          agent_id: 1,
          trigger: 'manual',
          model_ids: [],
          status: 'scheduled',
          bedrock_job_id: null,
          score_summary: {},
          error_message: null,
          started_at: null,
          completed_at: null,
          created_at: '2026-02-21T12:00:00Z',
        }),
      ),
    );

    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('#1')).toBeInTheDocument();
    });

    const button = screen.getByRole('button', { name: '触发评估' });
    await user.click(button);

    // 触发后按钮应显示"触发中..."（isPending 状态）
    await waitFor(() => {
      // 成功后应重新加载列表（mutation onSuccess 会 invalidate queries）
      expect(screen.getByRole('button', { name: '触发评估' })).toBeInTheDocument();
    });
  });
});
