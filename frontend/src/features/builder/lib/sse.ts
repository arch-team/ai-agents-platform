// Builder SSE 封装 — 委托给 shared 层通用解析器

import { parseSSEStream } from '@/shared/lib/parseSSEStream';

import type { BlueprintStreamChunk, BuilderStreamChunk, RefineBuilderRequest } from '../api/types';

// V1: 流式生成 Agent 配置
export async function* streamBuilderSSE(
  url: string,
  token: string | null,
  signal?: AbortSignal,
): AsyncGenerator<BuilderStreamChunk> {
  yield* parseSSEStream<BuilderStreamChunk>({ url, token, method: 'POST', body: {}, signal });
}

// V2: 流式生成 Blueprint (SOP 引导式)
export async function* streamBlueprintGenerate(
  url: string,
  token: string | null,
  signal?: AbortSignal,
): AsyncGenerator<BlueprintStreamChunk> {
  yield* parseSSEStream<BlueprintStreamChunk>({ url, token, method: 'POST', body: {}, signal });
}

// V2: 流式 Blueprint 迭代优化
export async function* streamBlueprintRefine(
  url: string,
  token: string | null,
  body: RefineBuilderRequest,
  signal?: AbortSignal,
): AsyncGenerator<BlueprintStreamChunk> {
  yield* parseSSEStream<BlueprintStreamChunk>({ url, token, method: 'POST', body, signal });
}
