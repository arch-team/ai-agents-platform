// 流式发送消息 — 通过 SSE + Zustand store 管理

import { useCallback, useRef } from 'react';

import { useQueryClient } from '@tanstack/react-query';

import { env } from '@/shared/config/env';
import { extractApiError } from '@/shared/lib/extractApiError';

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
 * @returns sendMessage 发送消息函数、abort 取消当前 SSE 连接的函数
 */
export function useSendMessageStream(token: string | null) {
  const { appendStreamContent, clearStream, setStreaming, setError, clearError } = useChatActions();
  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);

  const abort = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  const sendMessage = useCallback(
    async (conversationId: number, dto: SendMessageDTO) => {
      // 取消上一次未完成的 SSE 连接
      abort();

      const controller = new AbortController();
      abortControllerRef.current = controller;

      clearStream();
      clearError();
      setStreaming(true);

      try {
        const url = `${env.VITE_API_BASE_URL}/api/v1/conversations/${conversationId}/messages/stream`;

        for await (const chunk of streamSSE(url, dto, token, controller.signal)) {
          if (chunk.error) {
            throw new Error(chunk.error);
          }

          if (chunk.content) {
            appendStreamContent(conversationId, chunk.content);
          }

          if (chunk.done) {
            break;
          }
        }
      } catch (err) {
        // 用户主动取消时不显示错误
        if (err instanceof DOMException && err.name === 'AbortError') {
          return;
        }
        setError(extractApiError(err, '发送消息失败，请重试'));
      } finally {
        abortControllerRef.current = null;
        setStreaming(false);
        // 流结束后刷新对话详情缓存
        queryClient.invalidateQueries({ queryKey: conversationKeys.detail(conversationId) });
      }
    },
    [
      appendStreamContent,
      clearStream,
      setStreaming,
      setError,
      clearError,
      queryClient,
      token,
      abort,
    ],
  );

  return { sendMessage, abort };
}
