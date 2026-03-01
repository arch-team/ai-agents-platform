import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

import { ToolSelector, type ToolOption } from './ToolSelector';

const mockTools: ToolOption[] = [
  {
    id: '1',
    name: 'Web Search',
    description: '搜索互联网内容',
    typeLabel: 'MCP Server',
  },
  {
    id: '2',
    name: 'Code Runner',
    description: '执行代码片段',
    typeLabel: 'Function',
  },
  {
    id: '3',
    name: 'REST API',
    description: '',
    typeLabel: 'API',
  },
];

describe('ToolSelector', () => {
  it('should show loading state', () => {
    render(<ToolSelector selectedIds={[]} onChange={vi.fn()} tools={[]} isLoading />);

    expect(screen.getByText('加载可用工具...')).toBeInTheDocument();
  });

  it('should show error state', () => {
    render(<ToolSelector selectedIds={[]} onChange={vi.fn()} tools={[]} error="Network error" />);

    expect(screen.getByText('工具列表加载失败')).toBeInTheDocument();
  });

  it('should show empty state when no tools', () => {
    render(<ToolSelector selectedIds={[]} onChange={vi.fn()} tools={[]} />);

    expect(screen.getByText(/暂无已审批工具/)).toBeInTheDocument();
  });

  it('should render tool list with names and type labels', () => {
    render(<ToolSelector selectedIds={[]} onChange={vi.fn()} tools={mockTools} />);

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
    render(<ToolSelector selectedIds={[1]} onChange={vi.fn()} tools={mockTools} />);

    expect(screen.getByText('(1/3 已选)')).toBeInTheDocument();
  });

  it('should check selected tools', () => {
    render(<ToolSelector selectedIds={[1, 3]} onChange={vi.fn()} tools={mockTools} />);

    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes[0]).toBeChecked(); // id=1
    expect(checkboxes[1]).not.toBeChecked(); // id=2
    expect(checkboxes[2]).toBeChecked(); // id=3
  });

  it('should call onChange with added id when unchecked tool clicked', async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();

    render(<ToolSelector selectedIds={[1]} onChange={handleChange} tools={mockTools} />);

    // 点击 Code Runner (id=2) — 当前未选中
    await user.click(screen.getByLabelText(/Code Runner/));

    expect(handleChange).toHaveBeenCalledWith([1, 2]);
  });

  it('should call onChange with removed id when checked tool clicked', async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();

    render(<ToolSelector selectedIds={[1, 2]} onChange={handleChange} tools={mockTools} />);

    // 点击 Web Search (id=1) — 当前已选中，取消选中
    await user.click(screen.getByLabelText(/Web Search/));

    expect(handleChange).toHaveBeenCalledWith([2]);
  });

  it('should have accessible group role', () => {
    render(<ToolSelector selectedIds={[]} onChange={vi.fn()} tools={mockTools} />);

    expect(screen.getByRole('group', { name: '工具选择' })).toBeInTheDocument();
  });
});
