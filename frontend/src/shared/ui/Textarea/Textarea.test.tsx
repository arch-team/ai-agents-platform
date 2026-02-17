import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

import { Textarea } from './Textarea';

describe('Textarea', () => {
  it('应该渲染 textarea 元素', () => {
    render(<Textarea />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('应该渲染 label 并关联 textarea', () => {
    render(<Textarea label="描述" />);
    expect(screen.getByLabelText('描述')).toBeInTheDocument();
  });

  it('应该支持输入文本', async () => {
    const user = userEvent.setup();
    render(<Textarea label="内容" />);
    const textarea = screen.getByLabelText('内容');
    await user.type(textarea, '测试文本');
    expect(textarea).toHaveValue('测试文本');
  });

  it('应该在有错误时显示错误消息', () => {
    render(<Textarea label="描述" error="必填字段" />);
    expect(screen.getByRole('alert')).toHaveTextContent('必填字段');
  });

  it('应该在有错误时设置 aria-invalid', () => {
    render(<Textarea label="描述" error="错误" />);
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
  });

  it('应该在有错误时设置 aria-describedby 关联错误消息', () => {
    render(<Textarea label="描述" error="错误" id="desc" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('aria-describedby', 'desc-error');
  });

  it('应该在无错误时不设置 aria-invalid', () => {
    render(<Textarea label="描述" />);
    expect(screen.getByRole('textbox')).not.toHaveAttribute('aria-invalid');
  });

  it('应该在 disabled 时不可编辑', () => {
    render(<Textarea label="描述" disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('应该支持 placeholder', () => {
    render(<Textarea placeholder="请输入内容" />);
    expect(screen.getByPlaceholderText('请输入内容')).toBeInTheDocument();
  });

  it('应该转发 ref', () => {
    const ref = vi.fn();
    render(<Textarea ref={ref} />);
    expect(ref).toHaveBeenCalled();
  });
});
