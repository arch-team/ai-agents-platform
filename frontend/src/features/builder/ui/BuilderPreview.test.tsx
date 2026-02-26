// BuilderPreview 组件单元测试

import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';

import { useBuilderStore } from '../model/store';
import type { AgentConfig } from '../api/types';

import { BuilderPreview } from './BuilderPreview';

// 重置 store 状态，确保测试隔离
beforeEach(() => {
  useBuilderStore.getState().reset();
});

const mockConfig: AgentConfig = {
  name: '客服 Agent',
  description: '处理用户问题的客服助手',
  system_prompt: '你是一个专业的客服代表，需要礼貌地回答用户问题。',
  model_id: 'anthropic.us.anthropic.claude-haiku-4-5-20251001-v1:0-20241022-v2:0',
  temperature: 0.7,
  max_tokens: 2048,
};

describe('BuilderPreview', () => {
  it('config 为 null 时显示占位内容', () => {
    render(<BuilderPreview />);

    expect(screen.getByText('生成完成后，Agent 配置将在此处预览')).toBeInTheDocument();
  });

  it('生成中且 config 为 null 时显示生成中占位', () => {
    useBuilderStore.setState({ isGenerating: true });

    render(<BuilderPreview />);

    expect(screen.getByText('正在生成 Agent 配置，请稍候…')).toBeInTheDocument();
  });

  it('有配置时展示 Agent 名称', () => {
    useBuilderStore.setState({ generatedConfig: mockConfig });

    render(<BuilderPreview />);

    expect(screen.getByText('客服 Agent')).toBeInTheDocument();
  });

  it('有配置时展示描述', () => {
    useBuilderStore.setState({ generatedConfig: mockConfig });

    render(<BuilderPreview />);

    expect(screen.getByText('处理用户问题的客服助手')).toBeInTheDocument();
  });

  it('有配置时展示系统提示词', () => {
    useBuilderStore.setState({ generatedConfig: mockConfig });

    render(<BuilderPreview />);

    expect(
      screen.getByText('你是一个专业的客服代表，需要礼貌地回答用户问题。'),
    ).toBeInTheDocument();
  });

  it('有配置时展示温度参数', () => {
    useBuilderStore.setState({ generatedConfig: mockConfig });

    render(<BuilderPreview />);

    expect(screen.getByText('0.7')).toBeInTheDocument();
  });

  it('有配置时展示 max_tokens 参数', () => {
    useBuilderStore.setState({ generatedConfig: mockConfig });

    render(<BuilderPreview />);

    expect(screen.getByText('2048')).toBeInTheDocument();
  });

  it('有配置时显示"Agent 配置预览"标题', () => {
    useBuilderStore.setState({ generatedConfig: mockConfig });

    render(<BuilderPreview />);

    expect(screen.getByText('Agent 配置预览')).toBeInTheDocument();
  });
});
