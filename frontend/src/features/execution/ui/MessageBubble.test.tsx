import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { MessageBubble, StreamingBubble } from './MessageBubble';

// Mock formatTime，避免时区和 locale 差异导致测试不稳定
vi.mock('@/shared/lib/formatDate', () => ({
  formatTime: (isoString: string) => `time:${isoString}`,
}));

import type { Message } from '../api/types';

// 工厂函数：创建测试消息
function createMessage(overrides: Partial<Message> = {}): Message {
  return {
    id: 1,
    conversation_id: 1,
    role: 'user',
    content: '你好',
    token_count: 10,
    created_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('MessageBubble', () => {
  it('应正确渲染用户消息内容', () => {
    const message = createMessage({ role: 'user', content: '你好世界' });
    render(<MessageBubble message={message} />);

    expect(screen.getByText('你好世界')).toBeInTheDocument();
  });

  it('应正确渲染助手消息内容', () => {
    const message = createMessage({ role: 'assistant', content: '我是 AI 助手' });
    render(<MessageBubble message={message} />);

    expect(screen.getByText('我是 AI 助手')).toBeInTheDocument();
  });

  it('应显示格式化后的时间', () => {
    const message = createMessage({ created_at: '2025-06-15T14:30:00Z' });
    render(<MessageBubble message={message} />);

    const timeElement = screen.getByText('time:2025-06-15T14:30:00Z');
    expect(timeElement).toBeInTheDocument();
    expect(timeElement.tagName).toBe('TIME');
    expect(timeElement).toHaveAttribute('dateTime', '2025-06-15T14:30:00Z');
  });

  it('用户消息应右对齐（包含 justify-end 样式）', () => {
    const message = createMessage({ role: 'user' });
    const { container } = render(<MessageBubble message={message} />);

    // 外层 div 应包含 justify-end
    const outerDiv = container.firstElementChild;
    expect(outerDiv).toHaveClass('justify-end');
  });

  it('助手消息应左对齐（包含 justify-start 样式）', () => {
    const message = createMessage({ role: 'assistant', content: '回复' });
    const { container } = render(<MessageBubble message={message} />);

    const outerDiv = container.firstElementChild;
    expect(outerDiv).toHaveClass('justify-start');
  });

  it('应隐藏空内容的助手消息（返回 null）', () => {
    const message = createMessage({ role: 'assistant', content: '' });
    const { container } = render(<MessageBubble message={message} />);

    expect(container.innerHTML).toBe('');
  });

  it('应隐藏仅包含空白字符的助手消息', () => {
    const message = createMessage({ role: 'assistant', content: '   ' });
    const { container } = render(<MessageBubble message={message} />);

    expect(container.innerHTML).toBe('');
  });

  it('应正常显示空内容的用户消息', () => {
    const message = createMessage({ role: 'user', content: '' });
    const { container } = render(<MessageBubble message={message} />);

    // 用户消息即使为空也应渲染
    expect(container.innerHTML).not.toBe('');
  });

  it('应保留消息中的换行符（whitespace-pre-wrap）', () => {
    const message = createMessage({ content: '第一行\n第二行' });
    render(<MessageBubble message={message} />);

    // testing-library 的 getByText 默认对换行做归一化处理，使用函数匹配原始文本
    const textElement = screen.getByText((_content, element) => {
      return element?.textContent === '第一行\n第二行' && element.tagName === 'P';
    });
    expect(textElement).toHaveClass('whitespace-pre-wrap');
  });
});

describe('StreamingBubble', () => {
  it('应正确渲染流式内容', () => {
    render(<StreamingBubble content="正在生成中..." />);

    expect(screen.getByText('正在生成中...')).toBeInTheDocument();
  });

  it('应始终左对齐（助手样式）', () => {
    const { container } = render(<StreamingBubble content="内容" />);

    const outerDiv = container.firstElementChild;
    expect(outerDiv).toHaveClass('justify-start');
  });

  it('应保留换行格式', () => {
    const { container } = render(<StreamingBubble content={'行一\n行二'} />);

    const pElement = container.querySelector('p');
    expect(pElement).toHaveClass('whitespace-pre-wrap');
    expect(pElement).toHaveTextContent('行一');
    expect(pElement).toHaveTextContent('行二');
  });
});
