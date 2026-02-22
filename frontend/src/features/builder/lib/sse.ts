// Builder SSE 封装 — 委托给 shared 层通用解析器
// POST 方式的 SSE（发送 Builder 消息并流式接收 Agent 配置）

import { parseSSEStream } from '@/shared/lib/parseSSEStream';

import type { BuilderStreamChunk } from '../api/types';

/**
 * Builder SSE 流式生成器
 * 使用 POST 方法触发 AI 生成，流式接收 Agent 配置
 * @param signal - 可选 AbortSignal，用于取消 SSE 连接
 */
export async function* streamBuilderSSE(
  url: string,
  token: string | null,
  signal?: AbortSignal,
): AsyncGenerator<BuilderStreamChunk> {
  yield* parseSSEStream<BuilderStreamChunk>({ url, token, method: 'POST', body: {}, signal });
}
