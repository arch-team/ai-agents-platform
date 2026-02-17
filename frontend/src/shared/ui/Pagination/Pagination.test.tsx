import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

import { Pagination } from './Pagination';

describe('Pagination', () => {
  it('应该在总页数 <= 1 时不渲染', () => {
    const { container } = render(
      <Pagination page={1} totalPages={1} onPageChange={vi.fn()} />,
    );
    expect(container.innerHTML).toBe('');
  });

  it('应该渲染分页导航', () => {
    render(<Pagination page={1} totalPages={5} onPageChange={vi.fn()} />);
    expect(screen.getByLabelText('分页导航')).toBeInTheDocument();
  });

  it('应该显示当前页码和总页数', () => {
    render(<Pagination page={2} totalPages={5} onPageChange={vi.fn()} />);
    expect(screen.getByText('第 2 / 5 页')).toBeInTheDocument();
  });

  it('应该在第一页时禁用上一页按钮', () => {
    render(<Pagination page={1} totalPages={5} onPageChange={vi.fn()} />);
    expect(screen.getByLabelText('上一页')).toBeDisabled();
    expect(screen.getByLabelText('下一页')).toBeEnabled();
  });

  it('应该在最后一页时禁用下一页按钮', () => {
    render(<Pagination page={5} totalPages={5} onPageChange={vi.fn()} />);
    expect(screen.getByLabelText('下一页')).toBeDisabled();
    expect(screen.getByLabelText('上一页')).toBeEnabled();
  });

  it('应该在点击上一页时回调 page - 1', async () => {
    const onPageChange = vi.fn();
    const user = userEvent.setup();
    render(<Pagination page={3} totalPages={5} onPageChange={onPageChange} />);
    await user.click(screen.getByLabelText('上一页'));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('应该在点击下一页时回调 page + 1', async () => {
    const onPageChange = vi.fn();
    const user = userEvent.setup();
    render(<Pagination page={3} totalPages={5} onPageChange={onPageChange} />);
    await user.click(screen.getByLabelText('下一页'));
    expect(onPageChange).toHaveBeenCalledWith(4);
  });

  it('应该支持自定义 className', () => {
    render(<Pagination page={1} totalPages={3} onPageChange={vi.fn()} className="mt-4" />);
    expect(screen.getByLabelText('分页导航')).toHaveClass('mt-4');
  });
});
