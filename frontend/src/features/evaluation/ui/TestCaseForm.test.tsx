import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { TestCaseForm } from './TestCaseForm';

// Mock API hooks
const mockCreateMutateAsync = vi.fn();
const mockUpdateMutateAsync = vi.fn();

vi.mock('../api/queries', () => ({
  useCreateTestCase: () => ({
    mutateAsync: mockCreateMutateAsync,
    isPending: false,
    isError: false,
    error: null,
  }),
  useUpdateTestCase: () => ({
    mutateAsync: mockUpdateMutateAsync,
    isPending: false,
    isError: false,
    error: null,
  }),
}));

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

function Wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

const defaultProps = {
  suiteId: 1,
};

describe('TestCaseForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateMutateAsync.mockResolvedValue({});
    mockUpdateMutateAsync.mockResolvedValue({});
  });

  it('应该渲染添加模式的表单', () => {
    render(<TestCaseForm {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByText('添加测试用例')).toBeInTheDocument();
    expect(screen.getByLabelText('输入提示词')).toBeInTheDocument();
    expect(screen.getByLabelText('期望输出')).toBeInTheDocument();
    expect(screen.getByLabelText('评分标准')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '添加' })).toBeInTheDocument();
  });

  it('应该渲染编辑模式的表单', () => {
    const editCase = {
      id: 10,
      suite_id: 1,
      input_prompt: '测试提示词',
      expected_output: '测试输出',
      evaluation_criteria: '测试标准',
      order_index: 0,
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    };

    render(<TestCaseForm {...defaultProps} editCase={editCase} />, { wrapper: Wrapper });

    expect(screen.getByText('编辑测试用例')).toBeInTheDocument();
    expect(screen.getByLabelText('输入提示词')).toHaveValue('测试提示词');
    expect(screen.getByLabelText('期望输出')).toHaveValue('测试输出');
    expect(screen.getByLabelText('评分标准')).toHaveValue('测试标准');
    expect(screen.getByRole('button', { name: '保存' })).toBeInTheDocument();
  });

  it('输入提示词为空时提交按钮应该禁用', () => {
    render(<TestCaseForm {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByRole('button', { name: '添加' })).toBeDisabled();
  });

  it('输入提示词后提交按钮应该启用', async () => {
    const user = userEvent.setup();
    render(<TestCaseForm {...defaultProps} />, { wrapper: Wrapper });

    await user.type(screen.getByLabelText('输入提示词'), '一个测试提示词');

    expect(screen.getByRole('button', { name: '添加' })).toBeEnabled();
  });

  it('添加模式下提交表单应调用 createMutateAsync', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    render(<TestCaseForm {...defaultProps} onSuccess={onSuccess} />, { wrapper: Wrapper });

    await user.type(screen.getByLabelText('输入提示词'), '测试提示词');
    await user.type(screen.getByLabelText('期望输出'), '期望结果');
    await user.click(screen.getByRole('button', { name: '添加' }));

    await waitFor(() => {
      expect(mockCreateMutateAsync).toHaveBeenCalledWith({
        suiteId: 1,
        input_prompt: '测试提示词',
        expected_output: '期望结果',
        evaluation_criteria: undefined,
      });
    });
    expect(onSuccess).toHaveBeenCalled();
  });

  it('编辑模式下提交表单应调用 updateMutateAsync', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    const editCase = {
      id: 10,
      suite_id: 1,
      input_prompt: '原始提示词',
      expected_output: '',
      evaluation_criteria: '',
      order_index: 0,
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    };

    render(<TestCaseForm {...defaultProps} editCase={editCase} onSuccess={onSuccess} />, {
      wrapper: Wrapper,
    });

    const inputField = screen.getByLabelText('输入提示词');
    await user.clear(inputField);
    await user.type(inputField, '更新后的提示词');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => {
      expect(mockUpdateMutateAsync).toHaveBeenCalledWith({
        suiteId: 1,
        caseId: 10,
        input_prompt: '更新后的提示词',
        expected_output: '',
        evaluation_criteria: '',
      });
    });
    expect(onSuccess).toHaveBeenCalled();
  });

  it('点击取消按钮应调用 onCancel', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(<TestCaseForm {...defaultProps} onCancel={onCancel} />, { wrapper: Wrapper });

    await user.click(screen.getByRole('button', { name: '取消' }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('不传 onCancel 时不应渲染取消按钮', () => {
    render(<TestCaseForm {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.queryByRole('button', { name: '取消' })).not.toBeInTheDocument();
  });

  it('提交仅含空白字符的提示词时不应提交', async () => {
    const user = userEvent.setup();
    render(<TestCaseForm {...defaultProps} />, { wrapper: Wrapper });

    await user.type(screen.getByLabelText('输入提示词'), '   ');

    // 按钮仍应禁用（空白字符 trim 后为空）
    expect(screen.getByRole('button', { name: '添加' })).toBeDisabled();
  });
});
