// SSE 封装 — 委托给 shared 层通用解析器
// GET 方式的 SSE（订阅执行日志流）

import { parseSSEStream } from '@/shared/lib/parseSSEStream';

import type { TeamExecutionSSEChunk } from '../api/types';

/**
 * SSE 流式日志生成器
 * Team Execution 的 SSE 端点使用 GET 请求
 */
export async function* streamSSE(
  url: string,
  token: string | null,
): AsyncGenerator<TeamExecutionSSEChunk> {
  yield* parseSSEStream<TeamExecutionSSEChunk>({ url, token, method: 'GET' });
}
