import { describe, it, expect, vi, beforeEach } from 'vitest';

import { streamSSE } from './sse';

// 辅助函数：创建 mock ReadableStream
function createMockStream(chunks: string[]): ReadableStream<Uint8Array> {
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

// 辅助函数：消费生成器中所有数据
async function drain(gen: AsyncGenerator<unknown>): Promise<void> {
  let result = await gen.next();
  while (!result.done) {
    result = await gen.next();
  }
}

describe('streamSSE', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('应该正确解析 SSE 数据块', async () => {
    const mockStream = createMockStream([
      'data: {"content": "你好", "done": false}\n\n',
      'data: {"content": "世界", "done": false}\n\n',
      'data: {"content": "", "done": true, "message_id": 1, "token_count": 10}\n\n',
    ]);

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: mockStream,
    } as Response);

    const chunks = [];
    for await (const chunk of streamSSE('/test', { content: '测试' }, null)) {
      chunks.push(chunk);
    }

    expect(chunks).toHaveLength(3);
    expect(chunks[0]).toEqual({ content: '你好', done: false });
    expect(chunks[1]).toEqual({ content: '世界', done: false });
    expect(chunks[2]).toEqual({ content: '', done: true, message_id: 1, token_count: 10 });
  });

  it('应该在请求失败时抛出错误', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      text: () => Promise.resolve(''),
    } as unknown as Response);

    const generator = streamSSE('/test', { content: '测试' }, null);
    await expect(generator.next()).rejects.toThrow('SSE 请求失败');
  });

  it('应该在无响应体时抛出错误', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: null,
    } as Response);

    const generator = streamSSE('/test', { content: '测试' }, null);
    await expect(generator.next()).rejects.toThrow('无法读取响应流');
  });

  it('应该在请求中携带 Authorization header', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: createMockStream(['data: {"content": "", "done": true}\n\n']),
    } as Response);

    await drain(streamSSE('/test', { content: '测试' }, 'test-token'));

    expect(fetchSpy).toHaveBeenCalledWith('/test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer test-token',
      },
      credentials: 'include',
      body: JSON.stringify({ content: '测试' }),
    });
  });

  it('应该在无 token 时不携带 Authorization header', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: createMockStream(['data: {"content": "", "done": true}\n\n']),
    } as Response);

    await drain(streamSSE('/test', { content: '测试' }, null));

    expect(fetchSpy).toHaveBeenCalledWith('/test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ content: '测试' }),
    });
  });

  it('应该忽略无法解析 JSON 的行', async () => {
    const mockStream = createMockStream([
      'data: {"content": "有效", "done": false}\n\n',
      'data: invalid-json\n\n',
      'data: {"content": "", "done": true}\n\n',
    ]);

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: mockStream,
    } as Response);

    const chunks = [];
    for await (const chunk of streamSSE('/test', {}, null)) {
      chunks.push(chunk);
    }

    expect(chunks).toHaveLength(2);
    expect(chunks[0]).toEqual({ content: '有效', done: false });
    expect(chunks[1]).toEqual({ content: '', done: true });
  });

  it('应该处理跨块的数据', async () => {
    // 模拟数据被分割到多个块中
    const mockStream = createMockStream([
      'data: {"content": "你',
      '好", "done": false}\n\ndata: {"content": "", "done": true}\n\n',
    ]);

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: mockStream,
    } as Response);

    const chunks = [];
    for await (const chunk of streamSSE('/test', {}, null)) {
      chunks.push(chunk);
    }

    expect(chunks).toHaveLength(2);
    expect(chunks[0]).toEqual({ content: '你好', done: false });
    expect(chunks[1]).toEqual({ content: '', done: true });
  });
});
