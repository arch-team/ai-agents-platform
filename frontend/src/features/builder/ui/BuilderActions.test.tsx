// BuilderActions 组件单元测试

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useBuilderStore } from '../model/store';
import type { AgentConfig } from '../api/types';

import { BuilderActions } from './BuilderActions';

// 重置 store 状态，确保测试隔离
beforeEach(() => {
  useBuilderStore.getState().reset();
});

const mockConfig: AgentConfig = {
  name: '测试 Agent',
  description: '测试描述',
  system_prompt: '测试系统提示词',
  model_id: 'anthropic.claude-3-5-sonnet-20241022-v2:0',
  temperature: 0.7,
  max_tokens: 2048,
};

describe('BuilderActions', () => {
  it('sessionId 为 null 时不渲染任何内容', () => {
    const { container } = render(<BuilderActions onConfirm={vi.fn()} onCancel={vi.fn()} />);

    expect(container.firstChild).toBeNull();
  });

  it('有 sessionId 但生成未完成时，确认按钮禁用', () => {
    useBuilderStore.setState({ sessionId: 1, isGenerating: true });

    render(<BuilderActions onConfirm={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByRole('button', { name: '确认创建 Agent' })).toBeDisabled();
  });

  it('有 sessionId 但没有配置时，确认按钮禁用', () => {
    useBuilderStore.setState({ sessionId: 1, generatedConfig: null, isGenerating: false });

    render(<BuilderActions onConfirm={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByRole('button', { name: '确认创建 Agent' })).toBeDisabled();
  });

  it('生成完成且有配置时，确认按钮可用', () => {
    useBuilderStore.setState({
      sessionId: 1,
      generatedConfig: mockConfig,
      isGenerating: false,
    });

    render(<BuilderActions onConfirm={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByRole('button', { name: '确认创建 Agent' })).not.toBeDisabled();
  });

  it('点击确认按钮触发 onConfirm 并传入 sessionId', async () => {
    const handleConfirm = vi.fn();
    const user = userEvent.setup();

    useBuilderStore.setState({
      sessionId: 42,
      generatedConfig: mockConfig,
      isGenerating: false,
    });

    render(<BuilderActions onConfirm={handleConfirm} onCancel={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: '确认创建 Agent' }));

    expect(handleConfirm).toHaveBeenCalledWith(42);
  });

  it('点击取消按钮触发 onCancel', async () => {
    const handleCancel = vi.fn();
    const user = userEvent.setup();

    useBuilderStore.setState({ sessionId: 1 });

    render(<BuilderActions onConfirm={vi.fn()} onCancel={handleCancel} />);

    await user.click(screen.getByRole('button', { name: '取消' }));

    expect(handleCancel).toHaveBeenCalledTimes(1);
  });

  it('正在确认时取消按钮被禁用', () => {
    useBuilderStore.setState({ sessionId: 1, isConfirming: true });

    render(<BuilderActions onConfirm={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByRole('button', { name: '取消' })).toBeDisabled();
  });
});
