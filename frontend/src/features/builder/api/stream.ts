// Builder SSE 流式 hook — 通过 Zustand store 管理生成状态

import { useCallback, useRef } from 'react';

import { useQueryClient } from '@tanstack/react-query';

import { env } from '@/shared/config/env';
import { extractApiError } from '@/shared/lib/extractApiError';

import { streamBuilderSSE } from '../lib/sse';
import { useBuilderActions } from '../model/store';

import { builderKeys } from './queries';

/**
 * Builder 流式生成 hook
 * 不使用 React Query mutation（SSE 不适合标准 mutation 模式）
 * 直接调用 streamBuilderSSE，通过 Zustand store 管理流式状态
 *
 * @param token - 认证 token，由调用方从 auth store 获取后传入（避免跨 feature 依赖）
 * @returns startGeneration 启动生成函数、abort 取消当前 SSE 连接的函数
 */
export function useBuilderStream(token: string | null) {
  const { appendStreamContent, setGeneratedConfig, setGenerating, setError } = useBuilderActions();
  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);

  const abort = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  const startGeneration = useCallback(
    async (sessionId: number) => {
      // 取消上一次未完成的 SSE 连接
      abort();

      const controller = new AbortController();
      abortControllerRef.current = controller;

      setGenerating(true);
      setError(null);

      try {
        const url = `${env.VITE_API_BASE_URL}/api/v1/builder/sessions/${sessionId}/messages`;

        for await (const chunk of streamBuilderSSE(url, token, controller.signal)) {
          if (chunk.error) {
            throw new Error(chunk.error);
          }

          // 累积流式文本内容
          if (chunk.content) {
            appendStreamContent(chunk.content);
          }

          // 收到完整配置时更新预览
          if (chunk.config) {
            setGeneratedConfig(chunk.config);
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
        setError(extractApiError(err, '生成失败，请重试'));
      } finally {
        abortControllerRef.current = null;
        setGenerating(false);
        // 流结束后刷新会话详情缓存
        void queryClient.invalidateQueries({ queryKey: builderKeys.session(sessionId) });
      }
    },
    [appendStreamContent, setGeneratedConfig, setGenerating, setError, queryClient, token, abort],
  );

  return { startGeneration, abort };
}
