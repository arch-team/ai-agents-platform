import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

import { CategoryFilter } from './CategoryFilter';

describe('CategoryFilter', () => {
  it('应该渲染全部按钮和所有分类按钮', () => {
    const onChange = vi.fn();
    render(<CategoryFilter onChange={onChange} />);

    expect(screen.getByRole('button', { name: '全部' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '客户服务' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '数据分析' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '内容创作' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '编程助手' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '研究助手' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '自动化' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '其他' })).toBeInTheDocument();
  });

  it('应该在没有选中分类时高亮全部按钮', () => {
    const onChange = vi.fn();
    render(<CategoryFilter onChange={onChange} />);

    const allButton = screen.getByRole('button', { name: '全部' });
    expect(allButton).toHaveAttribute('aria-pressed', 'true');
  });

  it('应该在选中分类时高亮对应按钮', () => {
    const onChange = vi.fn();
    render(<CategoryFilter selected="data_analysis" onChange={onChange} />);

    const dataButton = screen.getByRole('button', { name: '数据分析' });
    expect(dataButton).toHaveAttribute('aria-pressed', 'true');

    const allButton = screen.getByRole('button', { name: '全部' });
    expect(allButton).toHaveAttribute('aria-pressed', 'false');
  });

  it('应该点击分类按钮触发 onChange 回调', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<CategoryFilter onChange={onChange} />);

    await user.click(screen.getByRole('button', { name: '数据分析' }));
    expect(onChange).toHaveBeenCalledWith('data_analysis');
  });

  it('应该再次点击已选分类取消选择', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<CategoryFilter selected="data_analysis" onChange={onChange} />);

    await user.click(screen.getByRole('button', { name: '数据分析' }));
    expect(onChange).toHaveBeenCalledWith(undefined);
  });

  it('应该点击全部按钮清除选择', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<CategoryFilter selected="code_assistant" onChange={onChange} />);

    await user.click(screen.getByRole('button', { name: '全部' }));
    expect(onChange).toHaveBeenCalledWith(undefined);
  });

  it('应该有正确的 ARIA group 属性', () => {
    const onChange = vi.fn();
    render(<CategoryFilter onChange={onChange} />);

    expect(screen.getByRole('group', { name: '分类筛选' })).toBeInTheDocument();
  });

  it('应该支持自定义 className', () => {
    const onChange = vi.fn();
    render(<CategoryFilter onChange={onChange} className="mt-4" />);

    const group = screen.getByRole('group', { name: '分类筛选' });
    expect(group).toHaveClass('mt-4');
  });

  it('应该渲染 8 个按钮（1 个全部 + 7 个分类）', () => {
    const onChange = vi.fn();
    render(<CategoryFilter onChange={onChange} />);

    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(8);
  });
});
