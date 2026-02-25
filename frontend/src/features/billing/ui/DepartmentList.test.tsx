import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { DepartmentList } from './DepartmentList';

// Mock queries
vi.mock('../api/queries', () => ({
  useDepartments: vi.fn(),
  useCreateDepartment: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUpdateDepartment: () => ({ mutateAsync: vi.fn() }),
  useDeleteDepartment: () => ({ mutateAsync: vi.fn() }),
}));

import { useDepartments } from '../api/queries';

const mockDepartments = {
  items: [
    {
      id: 1,
      name: '工程部',
      code: 'engineering',
      description: '研发',
      is_active: true,
      created_at: '',
      updated_at: '',
    },
    {
      id: 2,
      name: '市场部',
      code: 'marketing',
      description: '营销',
      is_active: false,
      created_at: '',
      updated_at: '',
    },
  ],
  total: 2,
  page: 1,
  page_size: 50,
  total_pages: 1,
};

describe('DepartmentList', () => {
  it('should render department list', () => {
    vi.mocked(useDepartments).mockReturnValue({
      data: mockDepartments,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDepartments>);

    render(<DepartmentList selectedId={null} onSelect={vi.fn()} isAdmin={false} />);

    expect(screen.getByText('工程部')).toBeInTheDocument();
    expect(screen.getByText('市场部')).toBeInTheDocument();
  });

  it('should show loading state', () => {
    vi.mocked(useDepartments).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as ReturnType<typeof useDepartments>);

    render(<DepartmentList selectedId={null} onSelect={vi.fn()} isAdmin={false} />);

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('should show empty state', () => {
    vi.mocked(useDepartments).mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDepartments>);

    render(<DepartmentList selectedId={null} onSelect={vi.fn()} isAdmin={false} />);

    expect(screen.getByText('暂无部门')).toBeInTheDocument();
  });

  it('should highlight selected department', () => {
    vi.mocked(useDepartments).mockReturnValue({
      data: mockDepartments,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDepartments>);

    render(<DepartmentList selectedId={1} onSelect={vi.fn()} isAdmin={false} />);

    const selected = screen.getByText('工程部').closest('[role="button"]');
    expect(selected).toHaveAttribute('aria-current', 'true');
  });

  it('should show admin actions when isAdmin', () => {
    vi.mocked(useDepartments).mockReturnValue({
      data: mockDepartments,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDepartments>);

    render(<DepartmentList selectedId={null} onSelect={vi.fn()} isAdmin={true} />);

    expect(screen.getByText('+ 新建')).toBeInTheDocument();
    // "停用"出现 2 次: 1 次作为非活跃部门的 badge, 1 次作为活跃部门的操作按钮
    expect(screen.getAllByText('停用')).toHaveLength(2);
    expect(screen.getByText('启用')).toBeInTheDocument();
    // admin 可见删除按钮
    expect(screen.getAllByText('删除')).toHaveLength(2);
  });
});
