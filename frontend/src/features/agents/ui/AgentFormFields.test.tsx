import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { AgentFormFields } from './AgentFormFields';
import { createAgentSchema, type CreateAgentFormData } from '../lib/validation';

// Mock ToolSelector，简化测试
vi.mock('./ToolSelector', () => ({
  ToolSelector: ({
    selectedIds,
    onChange,
  }: {
    selectedIds: number[];
    onChange: (ids: number[]) => void;
  }) => (
    <div data-testid="tool-selector">
      <span>已选工具: {selectedIds.length}</span>
      <button onClick={() => onChange([1, 2])}>选择工具</button>
    </div>
  ),
}));

// 测试用 Wrapper 组件，提供 react-hook-form 上下文
function FormWrapper({ defaultValues }: { defaultValues?: Partial<CreateAgentFormData> }) {
  const {
    register,
    formState: { errors },
    watch,
    setValue,
  } = useForm<CreateAgentFormData>({
    resolver: zodResolver(createAgentSchema),
    defaultValues: {
      name: '',
      description: '',
      system_prompt: '',
      model_id: 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
      temperature: 0.7,
      max_tokens: 2048,
      tool_ids: [],
      enable_memory: false,
      ...defaultValues,
    },
  });

  return <AgentFormFields register={register} errors={errors} watch={watch} setValue={setValue} />;
}

describe('AgentFormFields', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该渲染所有基本字段', () => {
    render(<FormWrapper />);

    expect(screen.getByLabelText('名称')).toBeInTheDocument();
    expect(screen.getByLabelText('描述')).toBeInTheDocument();
    expect(screen.getByLabelText('系统提示词')).toBeInTheDocument();
  });

  it('名称字段应标记为必填', () => {
    render(<FormWrapper />);

    const nameInput = screen.getByLabelText('名称');
    expect(nameInput).toHaveAttribute('aria-required', 'true');
  });

  it('应该渲染工具选择器', () => {
    render(<FormWrapper />);

    expect(screen.getByTestId('tool-selector')).toBeInTheDocument();
  });

  it('应该渲染启用记忆复选框', () => {
    render(<FormWrapper />);

    expect(screen.getByRole('checkbox')).toBeInTheDocument();
    expect(screen.getByText('启用记忆')).toBeInTheDocument();
  });

  it('应该渲染高级选项折叠按钮', () => {
    render(<FormWrapper />);

    const advancedButton = screen.getByRole('button', { name: /模型配置/ });
    expect(advancedButton).toBeInTheDocument();
    expect(advancedButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('点击高级选项按钮应展开高级配置', async () => {
    const user = userEvent.setup();
    render(<FormWrapper />);

    const advancedButton = screen.getByRole('button', { name: /模型配置/ });
    await user.click(advancedButton);

    expect(advancedButton).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByLabelText('模型')).toBeInTheDocument();
    expect(screen.getByLabelText(/温度/)).toBeInTheDocument();
    expect(screen.getByLabelText(/最大 Token 数/)).toBeInTheDocument();
  });

  it('高级选项中应显示模型选择列表', async () => {
    const user = userEvent.setup();
    render(<FormWrapper />);

    await user.click(screen.getByRole('button', { name: /模型配置/ }));

    expect(screen.getByRole('option', { name: /Haiku/ })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Sonnet/ })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Opus/ })).toBeInTheDocument();
  });

  it('应该显示系统提示词字符计数', () => {
    render(<FormWrapper defaultValues={{ system_prompt: '测试内容' }} />);

    // 字符计数：4 个字符
    expect(screen.getByText(/4/)).toBeInTheDocument();
    expect(screen.getByText(/10,000/)).toBeInTheDocument();
  });

  it('输入名称时应正确更新', async () => {
    const user = userEvent.setup();
    render(<FormWrapper />);

    const nameInput = screen.getByLabelText('名称');
    await user.type(nameInput, '我的Agent');

    expect(nameInput).toHaveValue('我的Agent');
  });

  it('启用记忆复选框应可切换', async () => {
    const user = userEvent.setup();
    render(<FormWrapper />);

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();

    await user.click(checkbox);

    expect(checkbox).toBeChecked();
  });

  it('温度滑块应有辅助说明', async () => {
    const user = userEvent.setup();
    render(<FormWrapper />);

    await user.click(screen.getByRole('button', { name: /模型配置/ }));

    expect(screen.getByText(/低温度.*精确/)).toBeInTheDocument();
    expect(screen.getByText(/高温度.*创意/)).toBeInTheDocument();
  });

  it('模型成本说明应可见', async () => {
    const user = userEvent.setup();
    render(<FormWrapper />);

    await user.click(screen.getByRole('button', { name: /模型配置/ }));

    // 成本说明在一个 <p> 中包含所有模型信息
    expect(screen.getByText(/Haiku.*最经济.*Sonnet.*均衡.*Opus.*最强/)).toBeInTheDocument();
  });

  it('再次点击高级选项按钮应收起', async () => {
    const user = userEvent.setup();
    render(<FormWrapper />);

    const advancedButton = screen.getByRole('button', { name: /模型配置/ });
    // 展开
    await user.click(advancedButton);
    expect(screen.getByLabelText('模型')).toBeInTheDocument();

    // 收起
    await user.click(advancedButton);
    expect(advancedButton).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByLabelText('模型')).not.toBeInTheDocument();
  });
});
