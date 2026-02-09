import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

import { MessageInput } from './MessageInput';

describe('MessageInput', () => {
  it('应该渲染输入框和发送按钮', () => {
    render(<MessageInput onSend={vi.fn()} />);
    expect(screen.getByLabelText('消息输入')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '发送消息' })).toBeInTheDocument();
  });

  it('应该在输入内容后点击发送按钮触发 onSend', async () => {
    const handleSend = vi.fn();
    const user = userEvent.setup();
    render(<MessageInput onSend={handleSend} />);

    await user.type(screen.getByLabelText('消息输入'), '你好');
    await user.click(screen.getByRole('button', { name: '发送消息' }));

    expect(handleSend).toHaveBeenCalledWith('你好');
  });

  it('应该在按下 Enter 键时发送消息', async () => {
    const handleSend = vi.fn();
    const user = userEvent.setup();
    render(<MessageInput onSend={handleSend} />);

    await user.type(screen.getByLabelText('消息输入'), '测试消息{Enter}');

    expect(handleSend).toHaveBeenCalledWith('测试消息');
  });

  it('应该在按下 Shift+Enter 时换行而非发送', async () => {
    const handleSend = vi.fn();
    const user = userEvent.setup();
    render(<MessageInput onSend={handleSend} />);

    await user.type(screen.getByLabelText('消息输入'), '第一行{Shift>}{Enter}{/Shift}第二行');

    expect(handleSend).not.toHaveBeenCalled();
  });

  it('应该在空内容时禁用发送按钮', () => {
    render(<MessageInput onSend={vi.fn()} />);
    expect(screen.getByRole('button', { name: '发送消息' })).toBeDisabled();
  });

  it('应该在 disabled 时禁用输入和发送', () => {
    render(<MessageInput onSend={vi.fn()} disabled />);
    expect(screen.getByLabelText('消息输入')).toBeDisabled();
    expect(screen.getByRole('button', { name: '发送消息' })).toBeDisabled();
  });

  it('应该在发送后清空输入框', async () => {
    const handleSend = vi.fn();
    const user = userEvent.setup();
    render(<MessageInput onSend={handleSend} />);

    const input = screen.getByLabelText('消息输入');
    await user.type(input, '你好');
    await user.click(screen.getByRole('button', { name: '发送消息' }));

    expect(input).toHaveValue('');
  });

  it('应该忽略仅包含空格的消息', async () => {
    const handleSend = vi.fn();
    const user = userEvent.setup();
    render(<MessageInput onSend={handleSend} />);

    await user.type(screen.getByLabelText('消息输入'), '   ');
    await user.click(screen.getByRole('button', { name: '发送消息' }));

    expect(handleSend).not.toHaveBeenCalled();
  });
});
