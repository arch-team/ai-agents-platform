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

describe('team-executions streamSSE', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('应该正确解析 SSE 日志数据块', async () => {
    const mockStream = createMockStream([
      'data: {"content": "开始任务", "agent_name": "Agent-1", "sequence": 1}\n\n',
      'data: {"content": "处理中...", "agent_name": "Agent-1", "sequence": 2}\n\n',
      'data: {"content": "", "done": true}\n\n',
    ]);

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: mockStream,
    } as Response);

    const chunks = [];
    for await (const chunk of streamSSE('/test', null)) {
      chunks.push(chunk);
    }

    expect(chunks).toHaveLength(3);
    expect(chunks[0]).toEqual({ content: '开始任务', agent_name: 'Agent-1', sequence: 1 });
    expect(chunks[1]).toEqual({ content: '处理中...', agent_name: 'Agent-1', sequence: 2 });
    expect(chunks[2]).toEqual({ content: '', done: true });
  });

  it('应该在请求失败时抛出错误', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      text: () => Promise.resolve(''),
    } as unknown as Response);

    const generator = streamSSE('/test', null);
    await expect(generator.next()).rejects.toThrow('SSE 请求失败');
  });

  it('应该在无响应体时抛出错误', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: null,
    } as Response);

    const generator = streamSSE('/test', null);
    await expect(generator.next()).rejects.toThrow('无法读取响应流');
  });

  it('应该使用 GET 方法发送请求', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: createMockStream(['data: {"content": "", "done": true}\n\n']),
    } as Response);

    await drain(streamSSE('/test', 'test-token'));

    expect(fetchSpy).toHaveBeenCalledWith(
      '/test',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
          Accept: 'text/event-stream',
        }),
      }),
    );
  });

  it('应该在无 token 时不携带 Authorization header', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: createMockStream(['data: {"content": "", "done": true}\n\n']),
    } as Response);

    await drain(streamSSE('/test', null));

    const callHeaders = (fetchSpy.mock.calls[0][1] as RequestInit).headers as Record<
      string,
      string
    >;
    expect(callHeaders.Authorization).toBeUndefined();
    expect(callHeaders.Accept).toBe('text/event-stream');
  });

  it('应该支持 AbortSignal 取消', async () => {
    const controller = new AbortController();

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: createMockStream(['data: {"content": "", "done": true}\n\n']),
    } as Response);

    const fetchSpy = vi.spyOn(globalThis, 'fetch');

    await drain(streamSSE('/test', null, controller.signal));

    expect(fetchSpy).toHaveBeenCalledWith(
      '/test',
      expect.objectContaining({
        signal: controller.signal,
      }),
    );
  });

  it('应该忽略无法解析 JSON 的行', async () => {
    const mockStream = createMockStream([
      'data: {"content": "有效", "agent_name": "Agent-1"}\n\n',
      'data: invalid-json\n\n',
      'data: {"content": "", "done": true}\n\n',
    ]);

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: mockStream,
    } as Response);

    const chunks = [];
    for await (const chunk of streamSSE('/test', null)) {
      chunks.push(chunk);
    }

    expect(chunks).toHaveLength(2);
    expect(chunks[0]).toEqual({ content: '有效', agent_name: 'Agent-1' });
    expect(chunks[1]).toEqual({ content: '', done: true });
  });

  it('应该处理跨块的数据', async () => {
    const mockStream = createMockStream([
      'data: {"content": "开',
      '始", "agent_name": "Agent-1"}\n\ndata: {"content": "", "done": true}\n\n',
    ]);

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: mockStream,
    } as Response);

    const chunks = [];
    for await (const chunk of streamSSE('/test', null)) {
      chunks.push(chunk);
    }

    expect(chunks).toHaveLength(2);
    expect(chunks[0]).toEqual({ content: '开始', agent_name: 'Agent-1' });
    expect(chunks[1]).toEqual({ content: '', done: true });
  });
});
