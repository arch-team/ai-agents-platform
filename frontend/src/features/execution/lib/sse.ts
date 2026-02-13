// SSE 封装 — 委托给 shared 层通用解析器
// POST 方式的 SSE（发送消息并流式接收响应）

import { parseSSEStream } from '@/shared/lib/parseSSEStream';

import type { SSEChunk } from '../api/types';

/**
 * SSE 流式消息生成器
 * 使用 POST 方法发送消息体，流式接收 AI 响应
 * @param signal - 可选 AbortSignal，用于取消 SSE 连接
 */
export async function* streamSSE(
  url: string,
  body: object,
  token: string | null,
  signal?: AbortSignal,
): AsyncGenerator<SSEChunk> {
  yield* parseSSEStream<SSEChunk>({ url, token, method: 'POST', body, signal });
}
