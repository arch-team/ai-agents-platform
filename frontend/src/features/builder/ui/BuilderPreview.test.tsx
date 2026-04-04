// BuilderPreview 组件单元测试 (V2 Blueprint)

import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';

import type { GeneratedBlueprint } from '../api/types';
import { useBuilderStore } from '../model/store';

import { BuilderPreview } from './BuilderPreview';

beforeEach(() => {
  useBuilderStore.getState().reset();
});

const mockBlueprint: GeneratedBlueprint = {
  persona: {
    role: '客服代表',
    background: '专业处理用户退换货和订单查询',
    tone: '友好且专业',
  },
  skills: [
    {
      name: '退换货处理',
      trigger_description: '用户提出退换货请求时触发',
      steps: ['确认订单信息', '检查退换货政策', '生成退换货单'],
      rules: ['7天无理由退换', '需要订单号'],
    },
  ],
  tool_bindings: [{ tool_id: 1, display_name: '订单查询 API', usage_hint: '查询用户订单状态' }],
  knowledge_base_ids: [101],
  memory_config: { enabled: true, strategy: 'conversation', retain_fields: ['user_id'] },
  guardrails: [{ rule: '不得泄露用户隐私', severity: 'block' }],
};

describe('BuilderPreview', () => {
  it('blueprint 为 null 时显示占位内容', () => {
    render(<BuilderPreview />);

    expect(screen.getByText('描述你的 Agent 需求后，蓝图将在此处预览')).toBeInTheDocument();
  });

  it('生成中且 blueprint 为 null 时显示生成中占位', () => {
    useBuilderStore.setState({ isGenerating: true });

    render(<BuilderPreview />);

    expect(screen.getByText('正在生成 Agent 蓝图，请稍候…')).toBeInTheDocument();
  });

  it('有 blueprint 时展示角色定义', () => {
    useBuilderStore.setState({ generatedBlueprint: mockBlueprint, phase: 'configure' });

    render(<BuilderPreview />);

    expect(screen.getByText('客服代表')).toBeInTheDocument();
    expect(screen.getByText('专业处理用户退换货和订单查询')).toBeInTheDocument();
  });

  it('有 blueprint 时展示技能列表', () => {
    useBuilderStore.setState({ generatedBlueprint: mockBlueprint, phase: 'configure' });

    render(<BuilderPreview />);

    expect(screen.getByText('退换货处理')).toBeInTheDocument();
    expect(screen.getByText('用户提出退换货请求时触发')).toBeInTheDocument();
  });

  it('有 blueprint 时展示工具绑定', () => {
    useBuilderStore.setState({ generatedBlueprint: mockBlueprint, phase: 'configure' });

    render(<BuilderPreview />);

    expect(screen.getByText('订单查询 API')).toBeInTheDocument();
    expect(screen.getByText('查询用户订单状态')).toBeInTheDocument();
  });

  it('有 blueprint 时展示知识库标签', () => {
    useBuilderStore.setState({ generatedBlueprint: mockBlueprint, phase: 'configure' });

    render(<BuilderPreview />);

    expect(screen.getByText('KB-101')).toBeInTheDocument();
  });

  it('有 blueprint 时展示记忆配置', () => {
    useBuilderStore.setState({ generatedBlueprint: mockBlueprint, phase: 'configure' });

    render(<BuilderPreview />);

    expect(screen.getByText('已启用')).toBeInTheDocument();
  });

  it('有 blueprint 时展示护栏规则', () => {
    useBuilderStore.setState({ generatedBlueprint: mockBlueprint, phase: 'configure' });

    render(<BuilderPreview />);

    expect(screen.getByText('不得泄露用户隐私')).toBeInTheDocument();
    expect(screen.getByText('阻断')).toBeInTheDocument();
  });

  it('testing 阶段显示只读标题', () => {
    useBuilderStore.setState({ generatedBlueprint: mockBlueprint, phase: 'testing' });

    render(<BuilderPreview />);

    expect(screen.getByText('Agent 蓝图（只读）')).toBeInTheDocument();
  });
});
