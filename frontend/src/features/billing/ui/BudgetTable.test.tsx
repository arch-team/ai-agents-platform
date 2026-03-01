import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { BudgetTable } from './BudgetTable';
import type { Budget } from '../api/types';

// Mock 数据
const mockCurrentBudget: Budget = {
  id: 1,
  department_id: 10,
  year: 2025,
  month: 6,
  budget_amount: 10000,
  used_amount: 4000,
  alert_threshold: 0.8,
  created_at: '2025-06-01',
  updated_at: '2025-06-01',
};

const mockBudgetList: Budget[] = [
  mockCurrentBudget,
  {
    id: 2,
    department_id: 10,
    year: 2025,
    month: 5,
    budget_amount: 8000,
    used_amount: 7500,
    alert_threshold: 0.8,
    created_at: '2025-05-01',
    updated_at: '2025-05-31',
  },
];

// Mock hooks
let mockCurrentBudgetReturn: ReturnType<typeof vi.fn>;
let mockBudgetListReturn: ReturnType<typeof vi.fn>;
const mockCreateMutateAsync = vi.fn();
const mockUpdateMutate = vi.fn();

vi.mock('../api/queries', () => ({
  useCurrentBudget: (...args: unknown[]) => mockCurrentBudgetReturn(...args),
  useBudgets: (...args: unknown[]) => mockBudgetListReturn(...args),
  useCreateBudget: () => ({
    mutateAsync: mockCreateMutateAsync,
    isPending: false,
  }),
  useUpdateBudget: () => ({
    mutate: mockUpdateMutate,
    isPending: false,
  }),
}));

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

function Wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

const defaultProps = {
  departmentId: 10,
  departmentName: '研发部',
  isAdmin: true,
};

describe('BudgetTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateMutateAsync.mockResolvedValue({});
    mockCurrentBudgetReturn = vi.fn().mockReturnValue({
      data: mockCurrentBudget,
      isLoading: false,
    });
    mockBudgetListReturn = vi.fn().mockReturnValue({
      data: { items: mockBudgetList, total: 2, page: 1, page_size: 20 },
      isLoading: false,
      error: null,
    });
  });

  it('应该渲染部门名称和预算标题', () => {
    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByText('研发部 — 预算')).toBeInTheDocument();
  });

  it('admin 用户应看到新建预算按钮', () => {
    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByRole('button', { name: '+ 新建预算' })).toBeInTheDocument();
  });

  it('非 admin 用户不应看到新建预算按钮', () => {
    render(<BudgetTable {...defaultProps} isAdmin={false} />, { wrapper: Wrapper });

    expect(screen.queryByRole('button', { name: '+ 新建预算' })).not.toBeInTheDocument();
  });

  it('应该显示当月预算摘要', () => {
    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByText(/当月预算/)).toBeInTheDocument();
    // $10,000 同时出现在摘要和表格中，使用 getAllByText 验证存在
    expect(screen.getAllByText('$10,000').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('$4,000').length).toBeGreaterThanOrEqual(1);
    // 摘要区域的使用率
    expect(screen.getByText('预算额度')).toBeInTheDocument();
    expect(screen.getByText('已使用')).toBeInTheDocument();
  });

  it('当月无预算时应显示提示信息', () => {
    mockCurrentBudgetReturn = vi.fn().mockReturnValue({
      data: undefined,
      isLoading: false,
    });

    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByText('当月暂无预算配置')).toBeInTheDocument();
  });

  it('当月预算 loading 时应显示加载指示器', () => {
    mockCurrentBudgetReturn = vi.fn().mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    const spinners = screen.getAllByRole('status', { name: '加载中' });
    expect(spinners.length).toBeGreaterThanOrEqual(1);
  });

  it('预算列表 loading 时应显示加载指示器', () => {
    mockBudgetListReturn = vi.fn().mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    const spinners = screen.getAllByRole('status', { name: '加载中' });
    expect(spinners.length).toBeGreaterThanOrEqual(1);
  });

  it('错误时应显示错误信息', () => {
    mockBudgetListReturn = vi.fn().mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('网络错误'),
    });

    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('应该渲染预算历史表格', () => {
    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    // 表头
    expect(screen.getByText('月份')).toBeInTheDocument();
    // "预算" 在摘要中也出现（"当月预算"），用精确匹配表头
    const budgetHeaders = screen.getAllByText('预算');
    expect(budgetHeaders.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('已用')).toBeInTheDocument();

    // 数据行
    expect(screen.getByText('2025-06')).toBeInTheDocument();
    expect(screen.getByText('2025-05')).toBeInTheDocument();
  });

  it('admin 用户应看到编辑操作列', () => {
    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByText('操作')).toBeInTheDocument();
    const editButtons = screen.getAllByRole('button', { name: /编辑.*预算/ });
    expect(editButtons.length).toBe(2);
  });

  it('非 admin 用户不应看到操作列', () => {
    render(<BudgetTable {...defaultProps} isAdmin={false} />, { wrapper: Wrapper });

    expect(screen.queryByText('操作')).not.toBeInTheDocument();
  });

  it('点击新建预算按钮应显示创建表单', async () => {
    const user = userEvent.setup();
    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    await user.click(screen.getByRole('button', { name: '+ 新建预算' }));

    // 表单出现后按钮文字变为"取消"
    expect(screen.getByRole('button', { name: '取消' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '确认' })).toBeInTheDocument();
  });

  it('超过告警阈值时应使用警告样式', () => {
    mockCurrentBudgetReturn = vi.fn().mockReturnValue({
      data: { ...mockCurrentBudget, used_amount: 9000 },
      isLoading: false,
    });

    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    // 使用率 90% 超过阈值 80%，应显示警告颜色
    expect(screen.getByText('90.0%')).toHaveClass('text-amber-600');
  });

  it('未超过告警阈值时应使用正常样式', () => {
    render(<BudgetTable {...defaultProps} />, { wrapper: Wrapper });

    // 使用率 40% 未超过阈值 80%，摘要区域显示绿色
    // 40.0% 同时出现在摘要和表格中，摘要区域带有 text-green-600 样式
    const usageTexts = screen.getAllByText('40.0%');
    const greenOne = usageTexts.find((el) => el.classList.contains('text-green-600'));
    expect(greenOne).toBeDefined();
  });
});
