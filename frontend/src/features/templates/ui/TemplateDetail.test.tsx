import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import type { Template } from '../api/types';

// mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

// mock 模板数据
const mockTemplate: Template = {
  id: 1,
  name: '测试模板',
  description: '这是一个测试模板',
  category: 'code_assistant',
  status: 'draft',
  creator_id: 100,
  system_prompt: '你是一个编程助手',
  model_id: 'claude-3-sonnet',
  temperature: 0.7,
  max_tokens: 4096,
  tool_ids: [],
  knowledge_base_ids: [],
  tags: [],
  usage_count: 10,
  is_featured: false,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-02T00:00:00Z',
};

let mockTemplateData: Template | undefined = mockTemplate;
let mockIsLoading = false;
let mockError: Error | null = null;

const mockPublishMutate = vi.fn();
const mockArchiveMutate = vi.fn();

vi.mock('../api/queries', () => ({
  useTemplate: () => ({
    data: mockTemplateData,
    isLoading: mockIsLoading,
    error: mockError,
  }),
  usePublishTemplate: () => ({
    mutate: mockPublishMutate,
    isPending: false,
    isError: false,
    error: null,
  }),
  useArchiveTemplate: () => ({
    mutate: mockArchiveMutate,
    isPending: false,
    isError: false,
    error: null,
  }),
}));

// mock TemplateStatusBadge
vi.mock('./TemplateStatusBadge', () => ({
  TemplateStatusBadge: ({ status }: { status: string }) => (
    <span data-testid="template-status-badge">{status}</span>
  ),
}));

import { TemplateDetail } from './TemplateDetail';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('TemplateDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTemplateData = { ...mockTemplate };
    mockIsLoading = false;
    mockError = null;
  });

  it('应该渲染模板基本信息', () => {
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText('测试模板')).toBeInTheDocument();
    expect(screen.getByText('这是一个测试模板')).toBeInTheDocument();
  });

  it('应该显示加载状态', () => {
    mockIsLoading = true;
    mockTemplateData = undefined;
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('应该显示错误信息', () => {
    mockError = new Error('加载模板详情失败');
    mockTemplateData = undefined;
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText('加载模板详情失败')).toBeInTheDocument();
  });

  it('应该在模板不存在时显示错误', () => {
    mockTemplateData = undefined;
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText('加载模板详情失败')).toBeInTheDocument();
  });

  it('应该显示基本信息区域', () => {
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText('基本信息')).toBeInTheDocument();
    expect(screen.getByText('分类')).toBeInTheDocument();
    expect(screen.getByText('编程助手')).toBeInTheDocument();
    expect(screen.getByText('创建者 ID')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('使用次数')).toBeInTheDocument();
    expect(screen.getByText('10 次')).toBeInTheDocument();
  });

  it('应该显示系统提示词', () => {
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText('系统提示词')).toBeInTheDocument();
    expect(screen.getByText('你是一个编程助手')).toBeInTheDocument();
  });

  it('应该显示配置预览', () => {
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText('配置预览')).toBeInTheDocument();
    expect(screen.getByText('模型')).toBeInTheDocument();
    expect(screen.getByText('claude-3-sonnet')).toBeInTheDocument();
    expect(screen.getByText('温度')).toBeInTheDocument();
    expect(screen.getByText('0.7')).toBeInTheDocument();
    expect(screen.getByText('最大 Token 数')).toBeInTheDocument();
    expect(screen.getByText('4096')).toBeInTheDocument();
  });

  it('应该在 draft 状态显示发布按钮', () => {
    mockTemplateData = { ...mockTemplate, status: 'draft' };
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(screen.getByRole('button', { name: '发布 测试模板' })).toBeInTheDocument();
  });

  it('应该在 published 状态显示使用此模板和归档按钮', () => {
    mockTemplateData = { ...mockTemplate, status: 'published' };
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(
      screen.getByRole('button', { name: '使用 测试模板 模板创建 Agent' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '归档 测试模板' })).toBeInTheDocument();
  });

  it('应该在 archived 状态不显示操作按钮', () => {
    mockTemplateData = { ...mockTemplate, status: 'archived' };
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(screen.queryByRole('button', { name: '发布 测试模板' })).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: '使用 测试模板 模板创建 Agent' }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '归档 测试模板' })).not.toBeInTheDocument();
  });

  it('应该点击发布按钮调用 publishMutation', async () => {
    const user = userEvent.setup();
    mockTemplateData = { ...mockTemplate, status: 'draft' };
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '发布 测试模板' }));
    expect(mockPublishMutate).toHaveBeenCalledWith(1);
  });

  it('应该点击归档按钮调用 archiveMutation', async () => {
    const user = userEvent.setup();
    mockTemplateData = { ...mockTemplate, status: 'published' };
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '归档 测试模板' }));
    expect(mockArchiveMutate).toHaveBeenCalledWith(1);
  });

  it('应该点击使用此模板按钮跳转到创建 Agent 页面', async () => {
    const user = userEvent.setup();
    mockTemplateData = { ...mockTemplate, status: 'published' };
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    await user.click(screen.getByRole('button', { name: '使用 测试模板 模板创建 Agent' }));

    expect(mockNavigate).toHaveBeenCalledWith('/agents/create', {
      state: {
        fromTemplate: {
          system_prompt: '你是一个编程助手',
          model_id: 'claude-3-sonnet',
          temperature: 0.7,
          max_tokens: 4096,
        },
      },
    });
  });

  it('应该显示返回列表按钮并触发回调', async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<TemplateDetail templateId={1} onBack={onBack} />, { wrapper: createWrapper() });

    const backButton = screen.getByRole('button', { name: '返回列表' });
    await user.click(backButton);
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('应该在有工具 ID 时显示工具信息', () => {
    mockTemplateData = { ...mockTemplate, tool_ids: [1, 2, 3] };
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText('工具')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('应该在有知识库 ID 时显示关联知识库', () => {
    mockTemplateData = { ...mockTemplate, knowledge_base_ids: [10, 20] };
    render(<TemplateDetail templateId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText('关联知识库')).toBeInTheDocument();
    expect(screen.getByText('10, 20')).toBeInTheDocument();
  });
});
