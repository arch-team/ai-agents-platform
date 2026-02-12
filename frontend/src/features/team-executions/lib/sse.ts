// SSE EventSource 封装 — Team Execution 使用 GET 方式的 SSE
// 与 execution/lib/sse.ts 类似，但使用 GET 请求而非 POST

import type { TeamExecutionSSEChunk } from '../api/types';

/**
 * SSE 流式日志生成器
 * Team Execution 的 SSE 端点使用 GET 请求
 */
export async function* streamSSE(
  url: string,
  token: string | null,
): AsyncGenerator<TeamExecutionSSEChunk> {
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    throw new Error(`SSE 请求失败: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('无法读取响应流');

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (data) {
            try {
              yield JSON.parse(data) as TeamExecutionSSEChunk;
            } catch {
              // 忽略解析失败的行
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
