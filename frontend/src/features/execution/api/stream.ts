// 流式发送消息 — 通过 SSE + Zustand store 管理

import { useCallback } from 'react';

import { useQueryClient } from '@tanstack/react-query';

import { env } from '@/shared/config/env';

import { streamSSE } from '../lib/sse';
import { useChatActions } from '../model/store';

import { conversationKeys } from './queries';
import type { SendMessageDTO } from './types';

/**
 * 流式发送消息 hook
 * 不使用 React Query mutation（SSE 不适合标准 mutation 模式）
 * 直接调用 streamSSE，通过 Zustand store 管理流式状态
 *
 * @param token - 认证 token，由调用方从 auth store 获取后传入（避免跨 feature 依赖）
 */
export function useSendMessageStream(token: string | null) {
  const { appendStreamContent, clearStream, setStreaming } = useChatActions();
  const queryClient = useQueryClient();

  const sendMessage = useCallback(
    async (conversationId: number, dto: SendMessageDTO) => {
      clearStream();
      setStreaming(true);

      try {
        const url = `${env.VITE_API_BASE_URL}/api/v1/conversations/${conversationId}/messages/stream`;

        for await (const chunk of streamSSE(url, dto, token)) {
          if (chunk.error) {
            throw new Error(chunk.error);
          }

          if (chunk.content) {
            appendStreamContent(chunk.content);
          }

          if (chunk.done) {
            break;
          }
        }
      } finally {
        setStreaming(false);
        // 流结束后刷新对话详情缓存
        queryClient.invalidateQueries({ queryKey: conversationKeys.detail(conversationId) });
      }
    },
    [appendStreamContent, clearStream, setStreaming, queryClient, token],
  );

  return { sendMessage };
}
