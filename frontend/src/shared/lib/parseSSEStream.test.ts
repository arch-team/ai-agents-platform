import { describe, it, expect, vi, beforeEach } from 'vitest';

import { parseSSEStream } from './parseSSEStream';

import type { SSERequestConfig } from './parseSSEStream';

// 创建模拟 ReadableStream 的辅助函数
function createMockReadableStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  let index = 0;
  return new ReadableStream({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(encoder.encode(chunks[index]));
        index++;
      } else {
        controller.close();
      }
    },
  });
}

describe('parseSSEStream', () => {
  const baseConfig: SSERequestConfig = {
    url: 'http://localhost:8000/api/v1/stream',
    token: 'test-token',
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('应该解析 SSE 数据行', async () => {
    const mockStream = createMockReadableStream([
      'data: {"type":"message","content":"Hello"}\n\n',
      'data: {"type":"message","content":"World"}\n\n',
    ]);

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(mockStream, { status: 200 }));

    const results: unknown[] = [];
    for await (const chunk of parseSSEStream<{ type: string; content: string }>(baseConfig)) {
      results.push(chunk);
    }

    expect(results).toEqual([
      { type: 'message', content: 'Hello' },
      { type: 'message', content: 'World' },
    ]);
  });

  it('应该在 HTTP 错误时抛出异常', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: '未授权' }), {
        status: 401,
        statusText: 'Unauthorized',
      }),
    );

    const generator = parseSSEStream(baseConfig);
    await expect(generator.next()).rejects.toThrow('SSE 请求失败: 未授权');
  });

  it('应该在网络错误时抛出友好消息', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Network error'));

    const generator = parseSSEStream(baseConfig);
    await expect(generator.next()).rejects.toThrow('网络连接失败，请检查网络后重试');
  });

  it('应该在 AbortError 时静默返回', async () => {
    const abortError = new DOMException('The operation was aborted', 'AbortError');
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(abortError);

    const results: unknown[] = [];
    for await (const chunk of parseSSEStream(baseConfig)) {
      results.push(chunk);
    }
    expect(results).toEqual([]);
  });

  it('应该发送 GET 请求并设置正确的 headers', async () => {
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(createMockReadableStream([]), { status: 200 }));

    const generator = parseSSEStream(baseConfig);
    // 消费生成器
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    for await (const _ of generator) {
      // 空
    }

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/stream',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
          Accept: 'text/event-stream',
        }),
      }),
    );
  });

  it('应该发送 POST 请求并携带 body', async () => {
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(createMockReadableStream([]), { status: 200 }));

    const postConfig: SSERequestConfig = {
      ...baseConfig,
      method: 'POST',
      body: { message: 'hello' },
    };

    const generator = parseSSEStream(postConfig);
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    for await (const _ of generator) {
      // 空
    }

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/stream',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
          'Content-Type': 'application/json',
        }),
        body: JSON.stringify({ message: 'hello' }),
      }),
    );
  });

  it('应该在无 token 时不发送 Authorization header', async () => {
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(createMockReadableStream([]), { status: 200 }));

    const noTokenConfig: SSERequestConfig = { ...baseConfig, token: null };
    const generator = parseSSEStream(noTokenConfig);
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    for await (const _ of generator) {
      // 空
    }

    const callHeaders = fetchSpy.mock.calls[0][1]?.headers as Record<string, string>;
    expect(callHeaders.Authorization).toBeUndefined();
  });

  it('应该跳过无效 JSON 数据行', async () => {
    const mockStream = createMockReadableStream(['data: not-json\n\n', 'data: {"valid":true}\n\n']);

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(mockStream, { status: 200 }));

    const results: unknown[] = [];
    for await (const chunk of parseSSEStream(baseConfig)) {
      results.push(chunk);
    }

    expect(results).toEqual([{ valid: true }]);
  });

  it('应该处理跨 chunk 的数据分割', async () => {
    // 模拟数据跨 chunk 分割的情况
    const mockStream = createMockReadableStream(['data: {"part', '":"complete"}\n\n']);

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(mockStream, { status: 200 }));

    const results: unknown[] = [];
    for await (const chunk of parseSSEStream(baseConfig)) {
      results.push(chunk);
    }

    expect(results).toEqual([{ part: 'complete' }]);
  });

  it('应该跳过非 data: 开头的行', async () => {
    const mockStream = createMockReadableStream([
      'event: message\n',
      'data: {"type":"msg"}\n\n',
      ': comment line\n',
      'id: 123\n',
    ]);

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(mockStream, { status: 200 }));

    const results: unknown[] = [];
    for await (const chunk of parseSSEStream(baseConfig)) {
      results.push(chunk);
    }

    expect(results).toEqual([{ type: 'msg' }]);
  });

  it('应该在响应无 body 时抛出异常', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 200 }));

    // Response(null) 仍有 body，但 getReader 可能成功
    // 我们需要模拟一个没有 body 的 response
    const mockResponse = {
      ok: true,
      body: null,
      text: () => Promise.resolve(''),
    } as unknown as Response;

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(mockResponse);

    const generator = parseSSEStream(baseConfig);
    await expect(generator.next()).rejects.toThrow('无法读取响应流');
  });

  it('应该在 HTTP 错误响应非 JSON 时使用状态码', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('Not Found', {
        status: 404,
        statusText: 'Not Found',
      }),
    );

    const generator = parseSSEStream(baseConfig);
    await expect(generator.next()).rejects.toThrow('SSE 请求失败: HTTP 404 Not Found');
  });
});
