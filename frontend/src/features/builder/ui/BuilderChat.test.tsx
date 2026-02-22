// BuilderChat 组件单元测试

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest';

import { useBuilderStore } from '../model/store';

import { BuilderChat } from './BuilderChat';

// jsdom 不实现 scrollIntoView，需要 mock 防止测试报错
beforeAll(() => {
  window.HTMLElement.prototype.scrollIntoView = vi.fn();
});

// 重置 store 状态，确保测试隔离
beforeEach(() => {
  useBuilderStore.getState().reset();
});

describe('BuilderChat', () => {
  it('应渲染提示词输入框和生成按钮', () => {
    render(<BuilderChat hasSession={false} onSubmit={vi.fn()} />);

    expect(screen.getByLabelText('描述你需要的 Agent')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '开始生成' })).toBeInTheDocument();
  });

  it('已有会话时按钮文案变为"重新生成"', () => {
    render(<BuilderChat hasSession={true} onSubmit={vi.fn()} />);

    expect(screen.getByRole('button', { name: '重新生成' })).toBeInTheDocument();
  });

  it('输入提示词后点击按钮应触发 onSubmit 回调', async () => {
    const handleSubmit = vi.fn();
    const user = userEvent.setup();

    render(<BuilderChat hasSession={false} onSubmit={handleSubmit} />);

    const textarea = screen.getByLabelText('描述你需要的 Agent');
    await user.type(textarea, '创建一个客服 Agent');
    await user.click(screen.getByRole('button', { name: '开始生成' }));

    expect(handleSubmit).toHaveBeenCalledWith('创建一个客服 Agent');
  });

  it('空提示词时点击按钮不触发 onSubmit', async () => {
    const handleSubmit = vi.fn();
    const user = userEvent.setup();

    render(<BuilderChat hasSession={false} onSubmit={handleSubmit} />);

    await user.click(screen.getByRole('button', { name: '开始生成' }));

    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it('生成中时显示"生成中…"并禁用按钮', () => {
    // 模拟生成中状态
    useBuilderStore.setState({ isGenerating: true });

    render(<BuilderChat hasSession={true} onSubmit={vi.fn()} />);

    const button = screen.getByRole('button', { name: /生成中/ });
    expect(button).toBeDisabled();
  });

  it('有流式内容时显示在消息区域', () => {
    useBuilderStore.setState({ streamContent: '正在分析你的需求…' });

    render(<BuilderChat hasSession={true} onSubmit={vi.fn()} />);

    expect(screen.getByText('正在分析你的需求…')).toBeInTheDocument();
  });

  it('有错误信息时展示错误提示', () => {
    useBuilderStore.setState({ error: '生成失败，请重试' });

    render(<BuilderChat hasSession={true} onSubmit={vi.fn()} />);

    expect(screen.getByRole('alert')).toHaveTextContent('生成失败，请重试');
  });

  it('生成完成后（无流式内容、无生成中）显示空状态占位', () => {
    render(<BuilderChat hasSession={false} onSubmit={vi.fn()} />);

    expect(screen.getByText('输入需求描述后，AI 将实时生成 Agent 配置')).toBeInTheDocument();
  });
});
