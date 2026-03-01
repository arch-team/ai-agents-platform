import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { TestSuiteDetail } from './TestSuiteDetail';
import type { TestSuite, TestCase, TestCaseListResponse } from '../api/types';

// Mock 数据
const mockSuite: TestSuite = {
  id: 1,
  name: '测试集A',
  description: '这是一个测试集描述',
  agent_id: 42,
  status: 'draft',
  owner_id: 1,
  created_at: '2025-06-01T10:00:00Z',
  updated_at: '2025-06-01T10:00:00Z',
};

const mockCases: TestCase[] = [
  {
    id: 100,
    suite_id: 1,
    input_prompt: '你好世界',
    expected_output: 'Hello World',
    evaluation_criteria: '准确翻译',
    order_index: 0,
    created_at: '2025-06-01T10:00:00Z',
    updated_at: '2025-06-01T10:00:00Z',
  },
];

const mockCasesData: TestCaseListResponse = {
  items: mockCases,
  total: 1,
  page: 1,
  page_size: 20,
};

// Mock hooks 返回值
let mockSuiteReturn: ReturnType<typeof vi.fn>;
let mockCasesReturn: ReturnType<typeof vi.fn>;
const mockDeleteMutate = vi.fn();
const mockActivateMutate = vi.fn();
const mockArchiveMutate = vi.fn();

vi.mock('../api/queries', () => ({
  useTestSuite: (...args: unknown[]) => mockSuiteReturn(...args),
  useTestCases: (...args: unknown[]) => mockCasesReturn(...args),
  useDeleteTestCase: () => ({
    mutate: mockDeleteMutate,
    isPending: false,
  }),
  useActivateTestSuite: () => ({
    mutate: mockActivateMutate,
    isPending: false,
    isError: false,
    error: null,
  }),
  useArchiveTestSuite: () => ({
    mutate: mockArchiveMutate,
    isPending: false,
    isError: false,
    error: null,
  }),
}));

// Mock TestCaseForm，避免嵌套复杂逻辑
vi.mock('./TestCaseForm', () => ({
  TestCaseForm: ({ onSuccess, onCancel }: { onSuccess?: () => void; onCancel?: () => void }) => (
    <div data-testid="test-case-form">
      <button onClick={onSuccess}>模拟提交成功</button>
      <button onClick={onCancel}>模拟取消</button>
    </div>
  ),
}));

// Mock TestSuiteStatusBadge
vi.mock('./TestSuiteStatusBadge', () => ({
  TestSuiteStatusBadge: ({ status }: { status: string }) => <span>状态:{status}</span>,
}));

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

function Wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe('TestSuiteDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSuiteReturn = vi.fn().mockReturnValue({
      data: mockSuite,
      isLoading: false,
      error: null,
    });
    mockCasesReturn = vi.fn().mockReturnValue({
      data: mockCasesData,
      isLoading: false,
    });
  });

  it('应该渲染 loading 状态', () => {
    mockSuiteReturn = vi.fn().mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应该渲染错误状态', () => {
    mockSuiteReturn = vi.fn().mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('网络错误'),
    });

    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('应该渲染测试集详情信息', () => {
    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    expect(screen.getByText('测试集A')).toBeInTheDocument();
    expect(screen.getByText('这是一个测试集描述')).toBeInTheDocument();
    expect(screen.getByText(/Agent ID: 42/)).toBeInTheDocument();
  });

  it('draft 状态下应显示激活按钮', () => {
    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    expect(screen.getByRole('button', { name: /激活/ })).toBeInTheDocument();
  });

  it('active 状态下应显示发起评估和归档按钮', () => {
    mockSuiteReturn = vi.fn().mockReturnValue({
      data: { ...mockSuite, status: 'active' },
      isLoading: false,
      error: null,
    });

    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    expect(screen.getByRole('button', { name: '发起评估' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /归档/ })).toBeInTheDocument();
  });

  it('点击激活按钮应调用 activateMutate', async () => {
    const user = userEvent.setup();
    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    await user.click(screen.getByRole('button', { name: /激活/ }));

    expect(mockActivateMutate).toHaveBeenCalledWith(1);
  });

  it('应该渲染测试用例列表', () => {
    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    expect(screen.getByText('测试用例 (1)')).toBeInTheDocument();
    expect(screen.getByText('你好世界')).toBeInTheDocument();
    expect(screen.getByText('Hello World')).toBeInTheDocument();
    expect(screen.getByText('准确翻译')).toBeInTheDocument();
  });

  it('用例列表为空时应显示空状态', () => {
    mockCasesReturn = vi.fn().mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 20 },
      isLoading: false,
    });

    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    expect(screen.getByText('暂无测试用例')).toBeInTheDocument();
  });

  it('用例 loading 时应显示加载指示器', () => {
    mockCasesReturn = vi.fn().mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    // 套件加载完毕后，用例区域还在加载
    expect(screen.getByText('测试集A')).toBeInTheDocument();
    // 用例区域中存在 Spinner
    const spinners = screen.getAllByRole('status', { name: '加载中' });
    expect(spinners.length).toBeGreaterThanOrEqual(1);
  });

  it('draft 状态下应显示添加用例按钮', async () => {
    const user = userEvent.setup();
    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    const addButton = screen.getByRole('button', { name: '添加用例' });
    expect(addButton).toBeInTheDocument();

    // 点击后显示表单
    await user.click(addButton);
    expect(screen.getByTestId('test-case-form')).toBeInTheDocument();
  });

  it('draft 状态下应显示编辑和删除按钮', () => {
    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    expect(screen.getByRole('button', { name: /编辑用例 #1/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /删除用例 #1/ })).toBeInTheDocument();
  });

  it('点击删除按钮应调用 deleteCaseMutation', async () => {
    const user = userEvent.setup();
    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    await user.click(screen.getByRole('button', { name: /删除用例 #1/ }));

    expect(mockDeleteMutate).toHaveBeenCalledWith({ suiteId: 1, caseId: 100 });
  });

  it('传入 onBack 时应显示返回按钮', async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<TestSuiteDetail suiteId={1} onBack={onBack} />, { wrapper: Wrapper });

    await user.click(screen.getByRole('button', { name: '返回列表' }));

    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('active 状态下点击发起评估应调用 onRunEvaluation', async () => {
    const user = userEvent.setup();
    const onRunEvaluation = vi.fn();
    mockSuiteReturn = vi.fn().mockReturnValue({
      data: { ...mockSuite, status: 'active' },
      isLoading: false,
      error: null,
    });

    render(<TestSuiteDetail suiteId={1} onRunEvaluation={onRunEvaluation} />, {
      wrapper: Wrapper,
    });

    await user.click(screen.getByRole('button', { name: '发起评估' }));

    expect(onRunEvaluation).toHaveBeenCalledWith(1);
  });

  it('archived 状态下不应显示操作按钮', () => {
    mockSuiteReturn = vi.fn().mockReturnValue({
      data: { ...mockSuite, status: 'archived' },
      isLoading: false,
      error: null,
    });

    render(<TestSuiteDetail suiteId={1} />, { wrapper: Wrapper });

    expect(screen.queryByRole('button', { name: /激活/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '发起评估' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /归档/ })).not.toBeInTheDocument();
  });
});
