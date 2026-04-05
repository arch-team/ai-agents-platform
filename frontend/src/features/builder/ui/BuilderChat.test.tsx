// BuilderChat 组件单元测试 (V2 多轮对话)

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest';

import { useBuilderStore } from '../model/store';

import { BuilderChat } from './BuilderChat';

beforeAll(() => {
  window.HTMLElement.prototype.scrollIntoView = vi.fn();
});

beforeEach(() => {
  useBuilderStore.getState().reset();
});

const defaultProps = {
  onSubmitInitial: vi.fn(),
  onSubmitRefine: vi.fn(),
};

describe('BuilderChat', () => {
  it('空状态显示欢迎提示', () => {
    render(<BuilderChat {...defaultProps} />);

    expect(screen.getByText('输入需求描述，AI 将帮你构建 Agent 蓝图')).toBeInTheDocument();
  });

  it('输入阶段按钮文案为"开始生成"', () => {
    render(<BuilderChat {...defaultProps} />);

    expect(screen.getByRole('button', { name: '开始生成' })).toBeInTheDocument();
  });

  it('输入提示词后点击按钮触发 onSubmitInitial', async () => {
    const handleInitial = vi.fn();
    const user = userEvent.setup();

    render(<BuilderChat {...defaultProps} onSubmitInitial={handleInitial} />);

    const textarea = screen.getByPlaceholderText(/创建一个能够回答客服问题/);
    await user.type(textarea, '创建一个客服 Agent');
    await user.click(screen.getByRole('button', { name: '开始生成' }));

    expect(handleInitial).toHaveBeenCalledWith('创建一个客服 Agent');
  });

  it('空提示词时按钮禁用', () => {
    render(<BuilderChat {...defaultProps} />);

    expect(screen.getByRole('button', { name: '开始生成' })).toBeDisabled();
  });

  it('生成中时显示"生成中…"并禁用按钮', () => {
    useBuilderStore.setState({ isGenerating: true });

    render(<BuilderChat {...defaultProps} />);

    const button = screen.getByRole('button', { name: /生成中/ });
    expect(button).toBeDisabled();
  });

  it('有流式内容时显示在对话区域', () => {
    useBuilderStore.setState({ isGenerating: true, streamContent: '正在分析你的需求…' });

    render(<BuilderChat {...defaultProps} />);

    expect(screen.getByText('正在分析你的需求…')).toBeInTheDocument();
  });

  it('有错误信息时展示错误提示', () => {
    useBuilderStore.setState({ error: '生成失败，请重试' });

    render(<BuilderChat {...defaultProps} />);

    expect(screen.getByRole('alert')).toHaveTextContent('生成失败，请重试');
  });

  it('configure 阶段按钮文案变为"发送调整"', () => {
    useBuilderStore.setState({
      phase: 'configure',
      messages: [{ role: 'assistant', content: '已生成蓝图' }],
    });

    render(<BuilderChat {...defaultProps} />);

    expect(screen.getByRole('button', { name: '发送调整' })).toBeInTheDocument();
  });

  it('configure 阶段提交触发 onSubmitRefine', async () => {
    const handleRefine = vi.fn();
    const user = userEvent.setup();
    useBuilderStore.setState({
      phase: 'configure',
      messages: [{ role: 'assistant', content: '已生成' }],
    });

    render(<BuilderChat {...defaultProps} onSubmitRefine={handleRefine} />);

    const textarea = screen.getByPlaceholderText('描述需要的调整…');
    await user.type(textarea, '增加一个退货处理技能');
    await user.click(screen.getByRole('button', { name: '发送调整' }));

    expect(handleRefine).toHaveBeenCalledWith('增加一个退货处理技能');
  });

  it('渲染历史消息气泡', () => {
    useBuilderStore.setState({
      phase: 'configure',
      messages: [
        { role: 'user', content: '创建一个客服 Agent' },
        { role: 'assistant', content: '好的，已为你生成蓝图' },
      ],
    });

    render(<BuilderChat {...defaultProps} />);

    expect(screen.getByText('创建一个客服 Agent')).toBeInTheDocument();
    expect(screen.getByText('好的，已为你生成蓝图')).toBeInTheDocument();
  });
});
