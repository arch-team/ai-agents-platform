import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { ToolSelector } from './ToolSelector';

// Mock useApprovedTools hook
const mockUseApprovedTools = vi.fn();
vi.mock('@/features/tool-catalog', () => ({
  useApprovedTools: () => mockUseApprovedTools(),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

const mockTools = [
  {
    id: '1',
    name: 'Web Search',
    description: '搜索互联网内容',
    tool_type: 'mcp_server' as const,
    status: 'approved' as const,
    version: '1.0',
    configuration: {},
    created_by: '1',
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
  },
  {
    id: '2',
    name: 'Code Runner',
    description: '执行代码片段',
    tool_type: 'function' as const,
    status: 'approved' as const,
    version: '1.0',
    configuration: {},
    created_by: '1',
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
  },
  {
    id: '3',
    name: 'REST API',
    description: '',
    tool_type: 'api' as const,
    status: 'approved' as const,
    version: '2.0',
    configuration: {},
    created_by: '1',
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
  },
];

describe('ToolSelector', () => {
  it('should show loading state', () => {
    mockUseApprovedTools.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderWithProviders(<ToolSelector selectedIds={[]} onChange={vi.fn()} />);

    expect(screen.getByText('加载可用工具...')).toBeInTheDocument();
  });

  it('should show error state', () => {
    mockUseApprovedTools.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Network error'),
    });

    renderWithProviders(<ToolSelector selectedIds={[]} onChange={vi.fn()} />);

    expect(screen.getByText('工具列表加载失败')).toBeInTheDocument();
  });

  it('should show empty state when no tools', () => {
    mockUseApprovedTools.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 20 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ToolSelector selectedIds={[]} onChange={vi.fn()} />);

    expect(screen.getByText(/暂无已审批工具/)).toBeInTheDocument();
  });

  it('should render tool list with names and type labels', () => {
    mockUseApprovedTools.mockReturnValue({
      data: { items: mockTools, total: 3, page: 1, page_size: 20 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ToolSelector selectedIds={[]} onChange={vi.fn()} />);

    expect(screen.getByText('Web Search')).toBeInTheDocument();
    expect(screen.getByText('Code Runner')).toBeInTheDocument();
    expect(screen.getByText('REST API')).toBeInTheDocument();
    // 类型标签
    expect(screen.getByText('MCP Server')).toBeInTheDocument();
    expect(screen.getByText('Function')).toBeInTheDocument();
    expect(screen.getByText('API')).toBeInTheDocument();
    // 描述
    expect(screen.getByText('搜索互联网内容')).toBeInTheDocument();
    expect(screen.getByText('执行代码片段')).toBeInTheDocument();
  });

  it('should show selection count', () => {
    mockUseApprovedTools.mockReturnValue({
      data: { items: mockTools, total: 3, page: 1, page_size: 20 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ToolSelector selectedIds={[1]} onChange={vi.fn()} />);

    expect(screen.getByText('(1/3 已选)')).toBeInTheDocument();
  });

  it('should check selected tools', () => {
    mockUseApprovedTools.mockReturnValue({
      data: { items: mockTools, total: 3, page: 1, page_size: 20 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ToolSelector selectedIds={[1, 3]} onChange={vi.fn()} />);

    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes[0]).toBeChecked(); // id=1
    expect(checkboxes[1]).not.toBeChecked(); // id=2
    expect(checkboxes[2]).toBeChecked(); // id=3
  });

  it('should call onChange with added id when unchecked tool clicked', async () => {
    mockUseApprovedTools.mockReturnValue({
      data: { items: mockTools, total: 3, page: 1, page_size: 20 },
      isLoading: false,
      error: null,
    });

    const handleChange = vi.fn();
    const user = userEvent.setup();

    renderWithProviders(<ToolSelector selectedIds={[1]} onChange={handleChange} />);

    // 点击 Code Runner (id=2) — 当前未选中
    await user.click(screen.getByLabelText(/Code Runner/));

    expect(handleChange).toHaveBeenCalledWith([1, 2]);
  });

  it('should call onChange with removed id when checked tool clicked', async () => {
    mockUseApprovedTools.mockReturnValue({
      data: { items: mockTools, total: 3, page: 1, page_size: 20 },
      isLoading: false,
      error: null,
    });

    const handleChange = vi.fn();
    const user = userEvent.setup();

    renderWithProviders(<ToolSelector selectedIds={[1, 2]} onChange={handleChange} />);

    // 点击 Web Search (id=1) — 当前已选中，取消选中
    await user.click(screen.getByLabelText(/Web Search/));

    expect(handleChange).toHaveBeenCalledWith([2]);
  });

  it('should have accessible group role', () => {
    mockUseApprovedTools.mockReturnValue({
      data: { items: mockTools, total: 3, page: 1, page_size: 20 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ToolSelector selectedIds={[]} onChange={vi.fn()} />);

    expect(screen.getByRole('group', { name: '工具选择' })).toBeInTheDocument();
  });
});
