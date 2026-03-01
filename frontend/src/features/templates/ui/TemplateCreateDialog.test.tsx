import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// mock createTemplate mutation
const mockCreateMutateAsync = vi.fn();
const mockMutationReset = vi.fn();

vi.mock('../api/queries', () => ({
  useCreateTemplate: () => ({
    mutateAsync: mockCreateMutateAsync,
    isPending: false,
    isError: false,
    error: null,
    reset: mockMutationReset,
  }),
}));

import { TemplateCreateDialog } from './TemplateCreateDialog';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('TemplateCreateDialog', () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该在 open 为 true 时渲染对话框', () => {
    render(<TemplateCreateDialog {...defaultProps} />, { wrapper: createWrapper() });

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('创建模板')).toBeInTheDocument();
  });

  it('应该在 open 为 false 时不渲染', () => {
    render(<TemplateCreateDialog {...defaultProps} open={false} />, {
      wrapper: createWrapper(),
    });

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('应该渲染所有表单字段', () => {
    render(<TemplateCreateDialog {...defaultProps} />, { wrapper: createWrapper() });

    expect(screen.getByLabelText('名称')).toBeInTheDocument();
    expect(screen.getByLabelText('描述')).toBeInTheDocument();
    expect(screen.getByLabelText('分类')).toBeInTheDocument();
    expect(screen.getByLabelText('系统提示词')).toBeInTheDocument();
  });

  it('应该渲染所有分类选项', () => {
    render(<TemplateCreateDialog {...defaultProps} />, { wrapper: createWrapper() });

    expect(screen.getByText('客户服务')).toBeInTheDocument();
    expect(screen.getByText('数据分析')).toBeInTheDocument();
    expect(screen.getByText('内容创作')).toBeInTheDocument();
    expect(screen.getByText('编程助手')).toBeInTheDocument();
    expect(screen.getByText('研究助手')).toBeInTheDocument();
    expect(screen.getByText('自动化')).toBeInTheDocument();
    expect(screen.getByText('其他')).toBeInTheDocument();
  });

  it('应该显示表单验证错误 - 名称和系统提示词为必填', async () => {
    const user = userEvent.setup();
    render(<TemplateCreateDialog {...defaultProps} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '创建' }));

    await waitFor(() => {
      expect(screen.getByText('名称不能为空')).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText('系统提示词不能为空')).toBeInTheDocument();
    });
  });

  it('应该成功提交表单', async () => {
    const user = userEvent.setup();
    mockCreateMutateAsync.mockResolvedValueOnce({ id: 1 });

    render(<TemplateCreateDialog {...defaultProps} />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText('名称'), '新模板');
    await user.type(screen.getByLabelText('描述'), '模板描述');
    await user.type(screen.getByLabelText('系统提示词'), '你是一个助手');
    await user.click(screen.getByRole('button', { name: '创建' }));

    await waitFor(() => {
      expect(mockCreateMutateAsync).toHaveBeenCalledWith({
        name: '新模板',
        description: '模板描述',
        category: 'other',
        system_prompt: '你是一个助手',
      });
    });

    expect(defaultProps.onSuccess).toHaveBeenCalledWith(1);
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('应该选择不同的分类', async () => {
    const user = userEvent.setup();
    mockCreateMutateAsync.mockResolvedValueOnce({ id: 2 });

    render(<TemplateCreateDialog {...defaultProps} />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText('名称'), '数据模板');
    await user.type(screen.getByLabelText('系统提示词'), '你是数据分析师');

    // 选择分类
    await user.selectOptions(screen.getByLabelText('分类'), 'data_analysis');

    await user.click(screen.getByRole('button', { name: '创建' }));

    await waitFor(() => {
      expect(mockCreateMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({ category: 'data_analysis' }),
      );
    });
  });

  it('应该点击取消按钮关闭对话框', async () => {
    const user = userEvent.setup();
    render(<TemplateCreateDialog {...defaultProps} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '取消' }));

    expect(defaultProps.onClose).toHaveBeenCalled();
    expect(mockMutationReset).toHaveBeenCalled();
  });

  it('应该有正确的 ARIA 属性', () => {
    render(<TemplateCreateDialog {...defaultProps} />, { wrapper: createWrapper() });

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'create-template-title');
  });

  it('应该渲染创建和取消按钮', () => {
    render(<TemplateCreateDialog {...defaultProps} />, { wrapper: createWrapper() });

    expect(screen.getByRole('button', { name: '创建' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '取消' })).toBeInTheDocument();
  });
});
