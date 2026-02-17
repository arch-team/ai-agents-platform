import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { TestSuiteCreateDialog } from './TestSuiteCreateDialog';

const API_BASE = 'http://localhost:8000';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('TestSuiteCreateDialog', () => {
  it('应渲染对话框标题和表单', () => {
    render(<TestSuiteCreateDialog onClose={vi.fn()} />, { wrapper: createWrapper() });

    expect(screen.getByText('创建测试集')).toBeInTheDocument();
    expect(screen.getByLabelText('名称')).toBeInTheDocument();
    expect(screen.getByLabelText('描述')).toBeInTheDocument();
    expect(screen.getByLabelText('Agent ID')).toBeInTheDocument();
  });

  it('应具有正确的 ARIA 对话框属性', () => {
    render(<TestSuiteCreateDialog onClose={vi.fn()} />, { wrapper: createWrapper() });

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'create-suite-title');
  });

  it('点击取消应调用 onClose', async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();

    render(<TestSuiteCreateDialog onClose={handleClose} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '取消' }));
    expect(handleClose).toHaveBeenCalled();
  });

  it('传入 agentId 时应自动填充 Agent ID', () => {
    render(<TestSuiteCreateDialog agentId={5} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByLabelText('Agent ID')).toHaveValue(5);
  });

  it('应成功创建测试集并调用 onSuccess 和 onClose', async () => {
    const user = userEvent.setup();
    const handleSuccess = vi.fn();
    const handleClose = vi.fn();

    render(
      <TestSuiteCreateDialog onSuccess={handleSuccess} onClose={handleClose} />,
      { wrapper: createWrapper() },
    );

    await user.type(screen.getByLabelText('名称'), '新测试集');
    await user.type(screen.getByLabelText('Agent ID'), '1');
    await user.click(screen.getByRole('button', { name: '创建' }));

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalledWith(3);
    });
    expect(handleClose).toHaveBeenCalled();
  });

  it('API 错误时应显示错误信息', async () => {
    server.use(
      http.post(`${API_BASE}/api/v1/test-suites`, () =>
        HttpResponse.json({ message: '创建失败' }, { status: 500 }),
      ),
    );

    const user = userEvent.setup();

    render(<TestSuiteCreateDialog onClose={vi.fn()} />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText('名称'), '新测试集');
    await user.type(screen.getByLabelText('Agent ID'), '1');
    await user.click(screen.getByRole('button', { name: '创建' }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
