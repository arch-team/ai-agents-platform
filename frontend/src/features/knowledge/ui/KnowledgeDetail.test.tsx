import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import type { KnowledgeBase, KnowledgeDocument } from '../api/types';

import { KnowledgeDetail } from './KnowledgeDetail';

const API_BASE = 'http://localhost:8000';

// 测试数据
const mockKnowledgeBase: KnowledgeBase = {
  id: 1,
  name: '产品文档知识库',
  description: '包含所有产品文档',
  status: 'ACTIVE',
  document_count: 2,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-15T10:30:00Z',
};

const mockDocuments: KnowledgeDocument[] = [
  {
    id: 1,
    knowledge_base_id: 1,
    file_name: '产品手册.pdf',
    file_size: 1048576,
    content_type: 'application/pdf',
    status: 'ready',
    created_at: '2025-01-10T00:00:00Z',
  },
  {
    id: 2,
    knowledge_base_id: 1,
    file_name: '技术规格.docx',
    file_size: 2097152,
    content_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    status: 'ready',
    created_at: '2025-01-12T00:00:00Z',
  },
];

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('KnowledgeDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    server.use(
      http.get(`${API_BASE}/api/v1/knowledge-bases/1`, () => HttpResponse.json(mockKnowledgeBase)),
      http.get(`${API_BASE}/api/v1/knowledge-bases/1/documents`, () =>
        HttpResponse.json({
          items: mockDocuments,
          total: 2,
          page: 1,
          page_size: 10,
          total_pages: 1,
        }),
      ),
    );
  });

  it('应显示加载状态', () => {
    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示知识库名称和描述', async () => {
    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '产品文档知识库' })).toBeInTheDocument();
    });
    expect(screen.getByText('包含所有产品文档')).toBeInTheDocument();
  });

  it('应显示知识库状态徽章', async () => {
    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('已激活')).toBeInTheDocument();
    });
  });

  it('应显示基本信息（文档数量、创建时间、更新时间）', async () => {
    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('文档数量')).toBeInTheDocument();
    });
    expect(screen.getByText('2 个')).toBeInTheDocument();
    expect(screen.getByText('创建时间')).toBeInTheDocument();
    expect(screen.getByText('更新时间')).toBeInTheDocument();
  });

  it('应显示文档列表', async () => {
    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('产品手册.pdf')).toBeInTheDocument();
    });
    expect(screen.getByText('技术规格.docx')).toBeInTheDocument();
  });

  it('应显示文档文件大小', async () => {
    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('产品手册.pdf')).toBeInTheDocument();
    });
    // 1048576 bytes = 1.0 MB
    expect(screen.getByText(/1\.0 MB/)).toBeInTheDocument();
  });

  it('文档为空时应显示空提示', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/knowledge-bases/1/documents`, () =>
        HttpResponse.json({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
      ),
    );

    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('暂无文档，请上传文档')).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/knowledge-bases/1`, () =>
        HttpResponse.json({ message: '加载失败' }, { status: 500 }),
      ),
    );

    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('ACTIVE 状态下应显示同步按钮', async () => {
    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '同步知识库' })).toBeInTheDocument();
    });
  });

  it('非 ACTIVE 状态下不应显示同步按钮', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/knowledge-bases/1`, () =>
        HttpResponse.json({ ...mockKnowledgeBase, status: 'CREATING' }),
      ),
    );

    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('产品文档知识库')).toBeInTheDocument();
    });
    expect(screen.queryByRole('button', { name: '同步知识库' })).not.toBeInTheDocument();
  });

  it('点击同步按钮应发起同步请求', async () => {
    const user = userEvent.setup();
    let syncCalled = false;

    server.use(
      http.post(`${API_BASE}/api/v1/knowledge-bases/1/sync`, () => {
        syncCalled = true;
        return HttpResponse.json(mockKnowledgeBase);
      }),
    );

    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '同步知识库' })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: '同步知识库' }));

    await waitFor(() => {
      expect(syncCalled).toBe(true);
    });
  });

  it('点击删除文档按钮应发起删除请求', async () => {
    const user = userEvent.setup();
    let deleteUrl = '';

    server.use(
      http.delete(`${API_BASE}/api/v1/knowledge-bases/1/documents/:docId`, ({ params }) => {
        deleteUrl = `/api/v1/knowledge-bases/1/documents/${params.docId}`;
        return new HttpResponse(null, { status: 204 });
      }),
    );

    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('产品手册.pdf')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: '删除文档 产品手册.pdf' }));

    await waitFor(() => {
      expect(deleteUrl).toBe('/api/v1/knowledge-bases/1/documents/1');
    });
  });

  it('传入 onBack 时应显示返回按钮', async () => {
    const user = userEvent.setup();
    const handleBack = vi.fn();

    render(<KnowledgeDetail knowledgeBaseId={1} onBack={handleBack} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '返回列表' })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: '返回列表' }));
    expect(handleBack).toHaveBeenCalledTimes(1);
  });

  it('未传入 onBack 时不应显示返回按钮', async () => {
    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('产品文档知识库')).toBeInTheDocument();
    });
    expect(screen.queryByRole('button', { name: '返回列表' })).not.toBeInTheDocument();
  });

  it('应显示知识检索区域', async () => {
    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '知识检索' })).toBeInTheDocument();
    });
    expect(screen.getByLabelText('检索问题')).toBeInTheDocument();
  });

  it('检索输入为空时提交按钮应禁用', async () => {
    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByLabelText('检索问题')).toBeInTheDocument();
    });

    const submitButton = screen.getByRole('button', { name: '检索' });
    expect(submitButton).toBeDisabled();
  });

  it('输入检索内容后提交按钮应可用', async () => {
    const user = userEvent.setup();

    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByLabelText('检索问题')).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('检索问题'), '如何使用产品');

    const submitButton = screen.getByRole('button', { name: '检索' });
    expect(submitButton).toBeEnabled();
  });

  it('提交检索应调用查询 API', async () => {
    const user = userEvent.setup();
    let queryCalled = false;

    server.use(
      http.post(`${API_BASE}/api/v1/knowledge-bases/1/query`, () => {
        queryCalled = true;
        return HttpResponse.json({
          results: [{ content: '产品使用说明', score: 0.95, metadata: {} }],
        });
      }),
    );

    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByLabelText('检索问题')).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('检索问题'), '如何使用');
    await user.click(screen.getByRole('button', { name: '检索' }));

    await waitFor(() => {
      expect(queryCalled).toBe(true);
    });
  });

  it('应显示检索结果', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_BASE}/api/v1/knowledge-bases/1/query`, () =>
        HttpResponse.json({
          results: [
            { content: '产品使用说明文档内容', score: 0.95, metadata: {} },
            { content: '安装指南', score: 0.8, metadata: {} },
          ],
        }),
      ),
    );

    render(<KnowledgeDetail knowledgeBaseId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByLabelText('检索问题')).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('检索问题'), '如何使用');
    await user.click(screen.getByRole('button', { name: '检索' }));

    await waitFor(() => {
      expect(screen.getByText('产品使用说明文档内容')).toBeInTheDocument();
    });
    expect(screen.getByText('安装指南')).toBeInTheDocument();
    expect(screen.getByText('检索结果 (2 条)')).toBeInTheDocument();
    expect(screen.getByText('相关度: 95.0%')).toBeInTheDocument();
  });
});
