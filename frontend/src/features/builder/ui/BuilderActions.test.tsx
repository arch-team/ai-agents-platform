// BuilderActions 组件单元测试 (V2 阶段感知)

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import type { GeneratedBlueprint } from '../api/types';
import { useBuilderStore } from '../model/store';

import { BuilderActions } from './BuilderActions';

beforeEach(() => {
  useBuilderStore.getState().reset();
});

const defaultProps = {
  onCancel: vi.fn(),
  onStartTesting: vi.fn(),
  onGoLive: vi.fn(),
  onBackToEdit: vi.fn(),
};

const mockBlueprint: GeneratedBlueprint = {
  persona: { role: '测试', background: '测试' },
  skills: [],
  tool_bindings: [],
  knowledge_base_ids: [],
  memory_config: null,
  guardrails: [],
};

describe('BuilderActions', () => {
  it('input 阶段且无 session 时不渲染', () => {
    const { container } = render(<BuilderActions {...defaultProps} />);

    expect(container.querySelector('button')).toBeNull();
  });

  it('generating 阶段显示取消按钮', () => {
    useBuilderStore.setState({ sessionId: 1, phase: 'generating' });

    render(<BuilderActions {...defaultProps} />);

    expect(screen.getByRole('button', { name: '取消生成' })).toBeInTheDocument();
  });

  it('点击取消生成触发 onCancel', async () => {
    const handleCancel = vi.fn();
    const user = userEvent.setup();
    useBuilderStore.setState({ sessionId: 1, phase: 'generating' });

    render(<BuilderActions {...defaultProps} onCancel={handleCancel} />);

    await user.click(screen.getByRole('button', { name: '取消生成' }));

    expect(handleCancel).toHaveBeenCalledTimes(1);
  });

  it('configure 阶段显示取消和开始测试按钮', () => {
    useBuilderStore.setState({
      sessionId: 1,
      phase: 'configure',
      generatedBlueprint: mockBlueprint,
    });

    render(<BuilderActions {...defaultProps} />);

    expect(screen.getByRole('button', { name: '取消' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /开始测试/ })).toBeInTheDocument();
  });

  it('configure 阶段无 blueprint 时开始测试按钮禁用', () => {
    useBuilderStore.setState({ sessionId: 1, phase: 'configure', generatedBlueprint: null });

    render(<BuilderActions {...defaultProps} />);

    expect(screen.getByRole('button', { name: /开始测试/ })).toBeDisabled();
  });

  it('点击开始测试触发 onStartTesting', async () => {
    const handleStartTesting = vi.fn();
    const user = userEvent.setup();
    useBuilderStore.setState({
      sessionId: 1,
      phase: 'configure',
      generatedBlueprint: mockBlueprint,
    });

    render(<BuilderActions {...defaultProps} onStartTesting={handleStartTesting} />);

    await user.click(screen.getByRole('button', { name: /开始测试/ }));

    expect(handleStartTesting).toHaveBeenCalledTimes(1);
  });

  it('testing 阶段显示返回修改和上线发布按钮', () => {
    useBuilderStore.setState({ sessionId: 1, phase: 'testing' });

    render(<BuilderActions {...defaultProps} />);

    expect(screen.getByRole('button', { name: /返回修改/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /上线发布/ })).toBeInTheDocument();
  });

  it('点击上线发布触发 onGoLive', async () => {
    const handleGoLive = vi.fn();
    const user = userEvent.setup();
    useBuilderStore.setState({ sessionId: 1, phase: 'testing' });

    render(<BuilderActions {...defaultProps} onGoLive={handleGoLive} />);

    await user.click(screen.getByRole('button', { name: /上线发布/ }));

    expect(handleGoLive).toHaveBeenCalledTimes(1);
  });

  it('点击返回修改触发 onBackToEdit', async () => {
    const handleBackToEdit = vi.fn();
    const user = userEvent.setup();
    useBuilderStore.setState({ sessionId: 1, phase: 'testing' });

    render(<BuilderActions {...defaultProps} onBackToEdit={handleBackToEdit} />);

    await user.click(screen.getByRole('button', { name: /返回修改/ }));

    expect(handleBackToEdit).toHaveBeenCalledTimes(1);
  });
});
