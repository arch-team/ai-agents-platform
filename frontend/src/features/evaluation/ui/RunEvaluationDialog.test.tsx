import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { RunEvaluationDialog } from './RunEvaluationDialog';

const API_BASE = 'http://localhost:8000';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('RunEvaluationDialog', () => {
  it('应渲染对话框内容', () => {
    render(<RunEvaluationDialog suiteId={1} suiteName="回归测试集" onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('发起评估')).toBeInTheDocument();
    expect(screen.getByText('回归测试集')).toBeInTheDocument();
  });

  it('应具有正确的 ARIA 对话框属性', () => {
    render(<RunEvaluationDialog suiteId={1} suiteName="回归测试集" onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'run-evaluation-title');
  });

  it('点击取消应调用 onClose', async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();

    render(<RunEvaluationDialog suiteId={1} suiteName="回归测试集" onClose={handleClose} />, {
      wrapper: createWrapper(),
    });

    await user.click(screen.getByRole('button', { name: '取消' }));
    expect(handleClose).toHaveBeenCalled();
  });

  it('点击确认发起应创建评估运行', async () => {
    const user = userEvent.setup();
    const handleSuccess = vi.fn();
    const handleClose = vi.fn();

    render(
      <RunEvaluationDialog
        suiteId={1}
        suiteName="回归测试集"
        onSuccess={handleSuccess}
        onClose={handleClose}
      />,
      { wrapper: createWrapper() },
    );

    await user.click(screen.getByRole('button', { name: '确认发起' }));

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalledWith(2);
    });
    expect(handleClose).toHaveBeenCalled();
  });

  it('API 错误时应显示错误信息', async () => {
    server.use(
      http.post(`${API_BASE}/api/v1/evaluation-runs`, () =>
        HttpResponse.json({ message: '创建失败' }, { status: 500 }),
      ),
    );

    const user = userEvent.setup();

    render(<RunEvaluationDialog suiteId={1} suiteName="回归测试集" onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    await user.click(screen.getByRole('button', { name: '确认发起' }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
