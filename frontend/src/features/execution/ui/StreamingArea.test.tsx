import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { StreamingArea } from './StreamingArea';

describe('StreamingArea', () => {
  it('正在流式传输且有内容时，应显示流式消息气泡', () => {
    render(<StreamingArea streamingContent="正在生成的内容" isStreaming={true} />);

    expect(screen.getByText('正在生成的内容')).toBeInTheDocument();
    // 有内容时不应显示指示器
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('正在流式传输但无内容时，应显示流式输入指示器', () => {
    render(<StreamingArea streamingContent="" isStreaming={true} />);

    expect(screen.getByRole('status', { name: 'AI 正在输入' })).toBeInTheDocument();
  });

  it('未在流式传输且无内容时，不应显示任何内容', () => {
    const { container } = render(<StreamingArea streamingContent="" isStreaming={false} />);

    expect(container.innerHTML).toBe('');
  });

  it('未在流式传输但有残余内容时，应显示流式消息气泡', () => {
    render(<StreamingArea streamingContent="残余内容" isStreaming={false} />);

    expect(screen.getByText('残余内容')).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('有内容时应优先显示气泡而非指示器', () => {
    render(<StreamingArea streamingContent="有内容" isStreaming={true} />);

    // 只显示气泡，不显示指示器
    expect(screen.getByText('有内容')).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('流式内容更新时应反映最新内容', () => {
    const { rerender } = render(<StreamingArea streamingContent="第一段" isStreaming={true} />);

    expect(screen.getByText('第一段')).toBeInTheDocument();

    rerender(<StreamingArea streamingContent="第一段第二段" isStreaming={true} />);

    expect(screen.getByText('第一段第二段')).toBeInTheDocument();
    expect(screen.queryByText('第一段')).not.toBeInTheDocument();
  });
});
