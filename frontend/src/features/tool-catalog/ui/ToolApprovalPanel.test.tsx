import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import type { Tool } from '../api/types';

// mock API hooks
const mockApproveMutateAsync = vi.fn();
const mockRejectMutateAsync = vi.fn();

vi.mock('../api/queries', () => ({
  useApproveTool: () => ({
    mutateAsync: mockApproveMutateAsync,
    isPending: false,
  }),
  useRejectTool: () => ({
    mutateAsync: mockRejectMutateAsync,
    isPending: false,
  }),
}));

import { ToolApprovalPanel } from './ToolApprovalPanel';

// 创建测试用 QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

// 创建模拟工具数据
function createMockTool(overrides: Partial<Tool> = {}): Tool {
  return {
    id: 'tool-1',
    name: '测试工具',
    description: '测试工具描述',
    tool_type: 'mcp_server',
    status: 'pending_review',
    version: '1.0.0',
    configuration: {},
    created_by: 'user-1',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('ToolApprovalPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该在 pending_review 状态下渲染审批面板', () => {
    const tool = createMockTool({ status: 'pending_review' });
    render(<ToolApprovalPanel tool={tool} />, { wrapper: createWrapper() });

    expect(screen.getByText('审批操作')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '审批通过' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '拒绝' })).toBeInTheDocument();
  });

  it('应该在非 pending_review 状态下不渲染', () => {
    const statuses = ['draft', 'approved', 'rejected', 'deprecated'] as const;
    for (const status of statuses) {
      const tool = createMockTool({ status });
      const { container } = render(<ToolApprovalPanel tool={tool} />, {
        wrapper: createWrapper(),
      });
      expect(container.innerHTML).toBe('');
    }
  });

  it('应该点击审批通过按钮调用 approveMutation', async () => {
    const user = userEvent.setup();
    const tool = createMockTool();
    mockApproveMutateAsync.mockResolvedValueOnce(undefined);

    render(<ToolApprovalPanel tool={tool} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '审批通过' }));

    expect(mockApproveMutateAsync).toHaveBeenCalledWith('tool-1');
  });

  it('应该点击拒绝按钮显示拒绝原因表单', async () => {
    const user = userEvent.setup();
    const tool = createMockTool();

    render(<ToolApprovalPanel tool={tool} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '拒绝' }));

    expect(screen.getByLabelText('拒绝原因')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '确认拒绝' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '取消' })).toBeInTheDocument();
  });

  it('应该在拒绝原因为空时禁用确认拒绝按钮', async () => {
    const user = userEvent.setup();
    const tool = createMockTool();

    render(<ToolApprovalPanel tool={tool} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '拒绝' }));

    expect(screen.getByRole('button', { name: '确认拒绝' })).toBeDisabled();
  });

  it('应该输入拒绝原因后启用确认拒绝按钮', async () => {
    const user = userEvent.setup();
    const tool = createMockTool();

    render(<ToolApprovalPanel tool={tool} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '拒绝' }));
    await user.type(screen.getByLabelText('拒绝原因'), '不符合要求');

    expect(screen.getByRole('button', { name: '确认拒绝' })).toBeEnabled();
  });

  it('应该提交拒绝原因调用 rejectMutation', async () => {
    const user = userEvent.setup();
    const tool = createMockTool();
    mockRejectMutateAsync.mockResolvedValueOnce(undefined);

    render(<ToolApprovalPanel tool={tool} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '拒绝' }));
    await user.type(screen.getByLabelText('拒绝原因'), '不符合要求');
    await user.click(screen.getByRole('button', { name: '确认拒绝' }));

    expect(mockRejectMutateAsync).toHaveBeenCalledWith({
      id: 'tool-1',
      reason: '不符合要求',
    });
  });

  it('应该点击取消按钮关闭拒绝表单并清空输入', async () => {
    const user = userEvent.setup();
    const tool = createMockTool();

    render(<ToolApprovalPanel tool={tool} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '拒绝' }));
    await user.type(screen.getByLabelText('拒绝原因'), '不符合要求');
    await user.click(screen.getByRole('button', { name: '取消' }));

    // 应该回到初始审批按钮状态
    expect(screen.getByRole('button', { name: '审批通过' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '拒绝' })).toBeInTheDocument();
    expect(screen.queryByLabelText('拒绝原因')).not.toBeInTheDocument();
  });

  it('应该在审批通过失败时显示错误信息', async () => {
    const user = userEvent.setup();
    const tool = createMockTool();
    mockApproveMutateAsync.mockRejectedValueOnce(new Error('审批通过失败'));

    render(<ToolApprovalPanel tool={tool} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '审批通过' }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('审批通过失败');
    });
  });

  it('应该在拒绝操作失败时显示错误信息', async () => {
    const user = userEvent.setup();
    const tool = createMockTool();
    mockRejectMutateAsync.mockRejectedValueOnce(new Error('审批拒绝失败'));

    render(<ToolApprovalPanel tool={tool} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '拒绝' }));
    await user.type(screen.getByLabelText('拒绝原因'), '不合格');
    await user.click(screen.getByRole('button', { name: '确认拒绝' }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('审批拒绝失败');
    });
  });
});
