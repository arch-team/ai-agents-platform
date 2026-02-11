// SSE EventSource 封装 — 使用 fetch + ReadableStream
// 原生 EventSource 不支持自定义 header，因此用 fetch 实现

import type { SSEChunk } from '../api/types';

/**
 * SSE 流式消息生成器
 * 使用 fetch + ReadableStream 解析 SSE 格式数据
 */
export async function* streamSSE(
  url: string,
  body: object,
  token: string | null,
): AsyncGenerator<SSEChunk> {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
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
              yield JSON.parse(data) as SSEChunk;
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
