import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { AgentCreateForm } from './AgentCreateForm';

const API_BASE = 'http://localhost:8000';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('AgentCreateForm', () => {
  beforeEach(() => {
    server.use(
      http.post(`${API_BASE}/api/v1/agents`, async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          id: 1,
          name: body.name,
          description: body.description ?? '',
          system_prompt: body.system_prompt ?? '',
          status: 'draft',
          owner_id: 1,
          config: {
            model_id: body.model_id ?? 'claude-3-5-sonnet',
            temperature: body.temperature ?? 0.7,
            max_tokens: body.max_tokens ?? 4096,
            top_p: 1,
          },
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        });
      }),
    );
  });

  it('应渲染表单字段', () => {
    render(<AgentCreateForm />, { wrapper: createWrapper() });

    expect(screen.getByLabelText('名称')).toBeInTheDocument();
    expect(screen.getByLabelText('描述')).toBeInTheDocument();
    expect(screen.getByLabelText('系统提示词')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建 Agent' })).toBeInTheDocument();
  });

  it('名称为空时应显示验证错误', async () => {
    const user = userEvent.setup();
    render(<AgentCreateForm />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '创建 Agent' }));

    await waitFor(() => {
      expect(screen.getByText('名称不能为空')).toBeInTheDocument();
    });
  });

  it('应成功提交表单并调用 onSuccess', async () => {
    const user = userEvent.setup();
    const handleSuccess = vi.fn();

    render(<AgentCreateForm onSuccess={handleSuccess} />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText('名称'), '我的新 Agent');
    await user.type(screen.getByLabelText('描述'), '这是一个测试 Agent');
    await user.click(screen.getByRole('button', { name: '创建 Agent' }));

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalledWith(1);
    });
  });

  it('应显示取消按钮并调用 onCancel', async () => {
    const user = userEvent.setup();
    const handleCancel = vi.fn();

    render(<AgentCreateForm onCancel={handleCancel} />, { wrapper: createWrapper() });

    const cancelButton = screen.getByRole('button', { name: '取消' });
    expect(cancelButton).toBeInTheDocument();
    await user.click(cancelButton);
    expect(handleCancel).toHaveBeenCalled();
  });

  it('应展开高级选项', async () => {
    const user = userEvent.setup();
    render(<AgentCreateForm />, { wrapper: createWrapper() });

    // 高级选项默认折叠
    expect(screen.queryByLabelText('模型')).not.toBeInTheDocument();

    // 展开高级选项
    await user.click(screen.getByRole('button', { name: /模型配置/ }));

    expect(screen.getByLabelText('模型')).toBeInTheDocument();
    expect(screen.getByLabelText(/温度/)).toBeInTheDocument();
    expect(screen.getByLabelText(/最大 Token 数/)).toBeInTheDocument();
  });

  it('API 错误时应显示错误提示', async () => {
    server.use(
      http.post(`${API_BASE}/api/v1/agents`, () =>
        HttpResponse.json({ message: '创建失败' }, { status: 400 }),
      ),
    );

    const user = userEvent.setup();
    render(<AgentCreateForm />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText('名称'), '测试 Agent');
    await user.click(screen.getByRole('button', { name: '创建 Agent' }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
