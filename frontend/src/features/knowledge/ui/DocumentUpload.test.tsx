import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { DocumentUpload } from './DocumentUpload';

const API_BASE = 'http://localhost:8000';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

// 创建模拟文件的辅助函数
function createMockFile(name: string, size: number, type: string): File {
  const content = new ArrayBuffer(size);
  return new File([content], name, { type });
}

describe('DocumentUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    server.use(
      http.post(`${API_BASE}/api/v1/knowledge-bases/1/documents`, () =>
        HttpResponse.json({
          id: 1,
          knowledge_base_id: 1,
          file_name: '测试文件.pdf',
          file_size: 1024,
          content_type: 'application/pdf',
          status: 'processing',
          created_at: '2025-01-01T00:00:00Z',
        }),
      ),
    );
  });

  it('应正确渲染上传组件', () => {
    render(<DocumentUpload knowledgeBaseId={1} />, { wrapper: createWrapper() });

    expect(screen.getByLabelText('选择文档文件')).toBeInTheDocument();
    expect(screen.getByText(/支持格式/)).toBeInTheDocument();
  });

  it('应显示支持的文件格式说明', () => {
    render(<DocumentUpload knowledgeBaseId={1} />, { wrapper: createWrapper() });

    expect(
      screen.getByText('支持格式: PDF、TXT、Markdown、DOCX、CSV（最大 10MB）'),
    ).toBeInTheDocument();
  });

  it('文件输入应限制 accept 属性', () => {
    render(<DocumentUpload knowledgeBaseId={1} />, { wrapper: createWrapper() });

    const fileInput = screen.getByLabelText('选择文档文件');
    expect(fileInput).toHaveAttribute('accept', '.pdf,.txt,.md,.docx,.csv');
  });

  it('上传有效 PDF 文件应发起上传请求', async () => {
    const user = userEvent.setup();
    let uploadCalled = false;

    server.use(
      http.post(`${API_BASE}/api/v1/knowledge-bases/1/documents`, () => {
        uploadCalled = true;
        return HttpResponse.json({
          id: 1,
          knowledge_base_id: 1,
          file_name: '文档.pdf',
          file_size: 1024,
          content_type: 'application/pdf',
          status: 'processing',
          created_at: '2025-01-01T00:00:00Z',
        });
      }),
    );

    render(<DocumentUpload knowledgeBaseId={1} />, { wrapper: createWrapper() });

    const file = createMockFile('文档.pdf', 1024, 'application/pdf');
    const fileInput = screen.getByLabelText('选择文档文件');
    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(uploadCalled).toBe(true);
    });
  });

  it('上传中应显示"上传中..."提示', async () => {
    const user = userEvent.setup();

    // 延迟响应以观察加载状态
    server.use(
      http.post(`${API_BASE}/api/v1/knowledge-bases/1/documents`, async () => {
        await new Promise((resolve) => setTimeout(resolve, 100));
        return HttpResponse.json({
          id: 1,
          knowledge_base_id: 1,
          file_name: '文档.pdf',
          file_size: 1024,
          content_type: 'application/pdf',
          status: 'processing',
          created_at: '2025-01-01T00:00:00Z',
        });
      }),
    );

    render(<DocumentUpload knowledgeBaseId={1} />, { wrapper: createWrapper() });

    const file = createMockFile('文档.pdf', 1024, 'application/pdf');
    await user.upload(screen.getByLabelText('选择文档文件'), file);

    expect(screen.getByText('上传中...')).toBeInTheDocument();
  });

  it('上传成功后应显示"上传成功"提示', async () => {
    const user = userEvent.setup();

    render(<DocumentUpload knowledgeBaseId={1} />, { wrapper: createWrapper() });

    const file = createMockFile('文档.pdf', 1024, 'application/pdf');
    await user.upload(screen.getByLabelText('选择文档文件'), file);

    await waitFor(() => {
      expect(screen.getByText('上传成功')).toBeInTheDocument();
    });
  });

  it('超过 10MB 的文件应显示大小超限错误', async () => {
    const user = userEvent.setup();

    render(<DocumentUpload knowledgeBaseId={1} />, { wrapper: createWrapper() });

    // 创建超过 10MB 的文件
    const file = createMockFile('大文件.pdf', 11 * 1024 * 1024, 'application/pdf');
    await user.upload(screen.getByLabelText('选择文档文件'), file);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/超过限制/);
    });
  });

  it('不支持的 MIME 类型应显示类型错误', async () => {
    render(<DocumentUpload knowledgeBaseId={1} />, { wrapper: createWrapper() });

    // userEvent.upload 会受 accept 属性过滤，使用 fireEvent 绕过浏览器原生过滤
    const file = createMockFile('图片.png', 1024, 'image/png');
    const fileInput = screen.getByLabelText('选择文档文件');

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('不支持的文件类型');
    });
  });

  it('不支持的文件扩展名应显示格式错误', async () => {
    render(<DocumentUpload knowledgeBaseId={1} />, { wrapper: createWrapper() });

    // 创建一个 MIME 为空但扩展名不支持的文件，使用 fireEvent 绕过 accept 过滤
    const file = createMockFile('脚本.js', 1024, '');
    const fileInput = screen.getByLabelText('选择文档文件');

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('不支持的文件格式');
    });
  });

  it('API 上传失败应显示错误信息', async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_BASE}/api/v1/knowledge-bases/1/documents`, () =>
        HttpResponse.json({ message: '上传失败' }, { status: 500 }),
      ),
    );

    render(<DocumentUpload knowledgeBaseId={1} />, { wrapper: createWrapper() });

    const file = createMockFile('文档.pdf', 1024, 'application/pdf');
    await user.upload(screen.getByLabelText('选择文档文件'), file);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('有效的 TXT 文件应正常上传', async () => {
    const user = userEvent.setup();
    let uploadCalled = false;

    server.use(
      http.post(`${API_BASE}/api/v1/knowledge-bases/1/documents`, () => {
        uploadCalled = true;
        return HttpResponse.json({
          id: 2,
          knowledge_base_id: 1,
          file_name: '说明.txt',
          file_size: 512,
          content_type: 'text/plain',
          status: 'processing',
          created_at: '2025-01-01T00:00:00Z',
        });
      }),
    );

    render(<DocumentUpload knowledgeBaseId={1} />, { wrapper: createWrapper() });

    const file = createMockFile('说明.txt', 512, 'text/plain');
    await user.upload(screen.getByLabelText('选择文档文件'), file);

    await waitFor(() => {
      expect(uploadCalled).toBe(true);
    });
  });
});
