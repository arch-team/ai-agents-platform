import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';

import { Input } from './Input';

describe('Input', () => {
  it('应该渲染带 label 的输入框', () => {
    render(<Input label="邮箱" />);
    expect(screen.getByLabelText('邮箱')).toBeInTheDocument();
  });

  it('应该显示错误信息', () => {
    render(<Input label="邮箱" error="邮箱格式不正确" />);
    expect(screen.getByRole('alert')).toHaveTextContent('邮箱格式不正确');
  });

  it('应该在有错误时设置 aria-invalid', () => {
    render(<Input label="邮箱" error="必填" />);
    expect(screen.getByLabelText('邮箱')).toHaveAttribute('aria-invalid', 'true');
  });

  it('应该在无错误时不设置 aria-invalid', () => {
    render(<Input label="邮箱" />);
    expect(screen.getByLabelText('邮箱')).not.toHaveAttribute('aria-invalid');
  });

  it('应该使用 aria-describedby 关联错误信息', () => {
    render(<Input label="邮箱" error="必填" />);
    const input = screen.getByLabelText('邮箱');
    const errorId = input.getAttribute('aria-describedby');
    expect(errorId).toBeTruthy();
    expect(document.getElementById(errorId!)).toHaveTextContent('必填');
  });

  it('应该接受用户输入', async () => {
    const user = userEvent.setup();
    render(<Input label="用户名" />);
    const input = screen.getByLabelText('用户名');
    await user.type(input, 'hello');
    expect(input).toHaveValue('hello');
  });
});
