import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// mock createTool mutation
const mockCreateMutateAsync = vi.fn();

vi.mock('../api/queries', () => ({
  useCreateTool: () => ({
    mutateAsync: mockCreateMutateAsync,
    isPending: false,
  }),
}));

import { ToolRegisterDialog } from './ToolRegisterDialog';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('ToolRegisterDialog', () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该在 open 为 true 时渲染对话框', () => {
    render(<ToolRegisterDialog {...defaultProps} />, { wrapper: createWrapper() });

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('注册新工具')).toBeInTheDocument();
  });

  it('应该在 open 为 false 时不渲染', () => {
    render(<ToolRegisterDialog {...defaultProps} open={false} />, {
      wrapper: createWrapper(),
    });

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('应该渲染所有表单字段', () => {
    render(<ToolRegisterDialog {...defaultProps} />, { wrapper: createWrapper() });

    expect(screen.getByLabelText('工具名称')).toBeInTheDocument();
    expect(screen.getByLabelText('工具描述')).toBeInTheDocument();
    expect(screen.getByLabelText('工具类型')).toBeInTheDocument();
    expect(screen.getByLabelText('版本号（可选）')).toBeInTheDocument();
  });

  it('应该渲染工具类型选项', () => {
    render(<ToolRegisterDialog {...defaultProps} />, { wrapper: createWrapper() });

    const select = screen.getByLabelText('工具类型');
    expect(select).toBeInTheDocument();
    expect(screen.getByText(/MCP Server/)).toBeInTheDocument();
    expect(screen.getByText(/API/)).toBeInTheDocument();
    expect(screen.getByText(/Function/)).toBeInTheDocument();
  });

  it('应该显示表单验证错误', async () => {
    const user = userEvent.setup();
    render(<ToolRegisterDialog {...defaultProps} />, { wrapper: createWrapper() });

    // 直接点击创建按钮，不填写任何表单
    await user.click(screen.getByRole('button', { name: '创建' }));

    await waitFor(() => {
      expect(screen.getByText('请输入工具名称')).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText('请输入工具描述')).toBeInTheDocument();
    });
  });

  it('应该成功提交表单', async () => {
    const user = userEvent.setup();
    mockCreateMutateAsync.mockResolvedValueOnce({ id: 'new-tool' });

    render(<ToolRegisterDialog {...defaultProps} />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText('工具名称'), '新工具');
    await user.type(screen.getByLabelText('工具描述'), '新工具描述');
    await user.type(screen.getByLabelText('版本号（可选）'), '1.0.0');
    await user.click(screen.getByRole('button', { name: '创建' }));

    await waitFor(() => {
      expect(mockCreateMutateAsync).toHaveBeenCalledWith({
        name: '新工具',
        description: '新工具描述',
        tool_type: 'mcp_server',
        version: '1.0.0',
      });
    });

    expect(defaultProps.onClose).toHaveBeenCalled();
    expect(defaultProps.onSuccess).toHaveBeenCalled();
  });

  it('应该在提交失败时显示 API 错误信息', async () => {
    const user = userEvent.setup();
    mockCreateMutateAsync.mockRejectedValueOnce(new Error('创建工具失败'));

    render(<ToolRegisterDialog {...defaultProps} />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText('工具名称'), '新工具');
    await user.type(screen.getByLabelText('工具描述'), '新工具描述');
    await user.click(screen.getByRole('button', { name: '创建' }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('创建工具失败');
    });
  });

  it('应该点击取消按钮关闭对话框', async () => {
    const user = userEvent.setup();
    render(<ToolRegisterDialog {...defaultProps} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '取消' }));

    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('应该点击遮罩层关闭对话框', async () => {
    const user = userEvent.setup();
    render(<ToolRegisterDialog {...defaultProps} />, { wrapper: createWrapper() });

    // 点击遮罩层（aria-hidden="true" 的 div）
    const overlay = screen.getByRole('dialog').parentElement?.querySelector('[aria-hidden="true"]');
    expect(overlay).not.toBeNull();
    await user.click(overlay!);

    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('应该按 Escape 键关闭对话框', async () => {
    const user = userEvent.setup();
    render(<ToolRegisterDialog {...defaultProps} />, { wrapper: createWrapper() });

    await user.keyboard('{Escape}');

    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('应该有正确的 ARIA 属性', () => {
    render(<ToolRegisterDialog {...defaultProps} />, { wrapper: createWrapper() });

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'register-tool-title');
  });
});
