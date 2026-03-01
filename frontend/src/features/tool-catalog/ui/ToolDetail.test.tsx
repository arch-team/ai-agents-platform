import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import type { Tool } from '../api/types';

// mock 数据
const mockTool: Tool = {
  id: 'tool-1',
  name: '测试工具',
  description: '这是一个测试工具',
  tool_type: 'mcp_server',
  status: 'draft',
  version: '1.0.0',
  configuration: { endpoint: 'https://example.com' },
  created_by: 'user-1',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-02T00:00:00Z',
};

// mock hooks 返回值
let mockToolData: Tool | undefined = mockTool;
let mockIsLoading = false;
let mockError: Error | null = null;

const mockSubmitMutate = vi.fn();
const mockDeprecateMutate = vi.fn();
const mockDeleteMutate = vi.fn();

vi.mock('../api/queries', () => ({
  useTool: () => ({
    data: mockToolData,
    isLoading: mockIsLoading,
    error: mockError,
  }),
  useSubmitTool: () => ({
    mutate: mockSubmitMutate,
    isPending: false,
  }),
  useDeprecateTool: () => ({
    mutate: mockDeprecateMutate,
    isPending: false,
  }),
  useDeleteTool: () => ({
    mutate: mockDeleteMutate,
    isPending: false,
  }),
}));

// mock ToolStatusBadge 和 ToolApprovalPanel 以隔离测试
vi.mock('./ToolStatusBadge', () => ({
  ToolStatusBadge: ({ status }: { status: string }) => (
    <span data-testid="tool-status-badge">{status}</span>
  ),
}));

vi.mock('./ToolApprovalPanel', () => ({
  ToolApprovalPanel: ({ tool }: { tool: Tool }) => (
    <div data-testid="tool-approval-panel">{tool.name}</div>
  ),
}));

import { ToolDetail } from './ToolDetail';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('ToolDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockToolData = { ...mockTool };
    mockIsLoading = false;
    mockError = null;
  });

  it('应该渲染工具基本信息', () => {
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.getByRole('heading', { name: '测试工具' })).toBeInTheDocument();
    expect(screen.getByText('这是一个测试工具')).toBeInTheDocument();
    expect(screen.getByText('MCP Server')).toBeInTheDocument();
    expect(screen.getByText('v1.0.0')).toBeInTheDocument();
  });

  it('应该显示加载状态', () => {
    mockIsLoading = true;
    mockToolData = undefined;
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('应该显示错误信息', () => {
    mockError = new Error('加载失败');
    mockToolData = undefined;
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.getByText('加载失败')).toBeInTheDocument();
  });

  it('应该在工具不存在时显示错误', () => {
    mockToolData = undefined;
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.getByText('工具不存在')).toBeInTheDocument();
  });

  it('应该显示返回列表按钮并触发回调', async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<ToolDetail toolId="tool-1" onBack={onBack} />, { wrapper: createWrapper() });

    const backButton = screen.getByRole('button', { name: '返回列表' });
    expect(backButton).toBeInTheDocument();

    await user.click(backButton);
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('应该在不传 onBack 时不显示返回按钮', () => {
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.queryByRole('button', { name: '返回列表' })).not.toBeInTheDocument();
  });

  it('应该在 draft 状态显示提交审批和删除按钮', () => {
    mockToolData = { ...mockTool, status: 'draft' };
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.getByRole('button', { name: '提交审批' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '删除' })).toBeInTheDocument();
  });

  it('应该在 approved 状态显示废弃按钮', () => {
    mockToolData = { ...mockTool, status: 'approved' };
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.getByRole('button', { name: '废弃' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '提交审批' })).not.toBeInTheDocument();
  });

  it('应该在 rejected 状态显示删除按钮', () => {
    mockToolData = { ...mockTool, status: 'rejected' };
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.getByRole('button', { name: '删除' })).toBeInTheDocument();
  });

  it('应该点击提交审批按钮调用 submitMutation', async () => {
    const user = userEvent.setup();
    mockToolData = { ...mockTool, status: 'draft' };
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '提交审批' }));
    expect(mockSubmitMutate).toHaveBeenCalledWith('tool-1');
  });

  it('应该点击废弃按钮调用 deprecateMutation', async () => {
    const user = userEvent.setup();
    mockToolData = { ...mockTool, status: 'approved' };
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '废弃' }));
    expect(mockDeprecateMutate).toHaveBeenCalledWith('tool-1');
  });

  it('应该点击删除按钮弹出确认框并调用 deleteMutation', async () => {
    const user = userEvent.setup();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    mockToolData = { ...mockTool, status: 'draft' };
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '删除' }));

    expect(window.confirm).toHaveBeenCalledWith('确定要删除这个工具吗？此操作不可撤销。');
    expect(mockDeleteMutate).toHaveBeenCalled();
  });

  it('应该在取消删除确认时不调用 deleteMutation', async () => {
    const user = userEvent.setup();
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    mockToolData = { ...mockTool, status: 'draft' };
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '删除' }));

    expect(mockDeleteMutate).not.toHaveBeenCalled();
  });

  it('应该显示元信息（创建者、创建时间、更新时间）', () => {
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.getByText('创建者')).toBeInTheDocument();
    expect(screen.getByText('user-1')).toBeInTheDocument();
    expect(screen.getByText('创建时间')).toBeInTheDocument();
    expect(screen.getByText('更新时间')).toBeInTheDocument();
  });

  it('应该在有审批者时显示审批者信息', () => {
    mockToolData = { ...mockTool, approved_by: 'admin-1' };
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.getByText('审批者')).toBeInTheDocument();
    expect(screen.getByText('admin-1')).toBeInTheDocument();
  });

  it('应该在 rejected 状态显示拒绝原因', () => {
    mockToolData = {
      ...mockTool,
      status: 'rejected',
      rejected_reason: '安全性不达标',
    };
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.getByText('拒绝原因')).toBeInTheDocument();
    expect(screen.getByText('安全性不达标')).toBeInTheDocument();
  });

  it('应该在有配置信息时显示配置区域', () => {
    mockToolData = {
      ...mockTool,
      configuration: { endpoint: 'https://example.com' },
    };
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.getByText('配置信息')).toBeInTheDocument();
    expect(screen.getByText(/"endpoint": "https:\/\/example.com"/)).toBeInTheDocument();
  });

  it('应该在配置为空时不显示配置区域', () => {
    mockToolData = { ...mockTool, configuration: {} };
    render(<ToolDetail toolId="tool-1" />, { wrapper: createWrapper() });

    expect(screen.queryByText('配置信息')).not.toBeInTheDocument();
  });
});
