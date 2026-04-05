// Builder SSE 流式 hook — V1 + V2 stream hooks

import { useCallback, useEffect, useRef } from 'react';

import { useQueryClient } from '@tanstack/react-query';

import { env } from '@/shared/config/env';
import { extractApiError } from '@/shared/lib/extractApiError';

import { streamBlueprintGenerate, streamBlueprintRefine } from '../lib/sse';
import { useBuilderActions } from '../model/store';

import { builderKeys } from './queries';

// 流式生成 Blueprint + 迭代优化
export function useBlueprintStream(token: string | null) {
  const {
    appendStreamContent,
    setGeneratedBlueprint,
    setGenerating,
    setError,
    addMessage,
    setPhase,
    resetStream,
  } = useBuilderActions();
  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);

  const abort = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  // H7 修复: 组件卸载时清理 SSE 连接防止内存泄漏
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  // 首次 Blueprint 生成
  const startGeneration = useCallback(
    async (sessionId: number) => {
      abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;
      setGenerating(true);
      setPhase('generating');
      resetStream();

      try {
        const url = `${env.VITE_API_BASE_URL}/api/v1/builder/sessions/${sessionId}/generate`;
        let assistantContent = '';

        for await (const chunk of streamBlueprintGenerate(url, token, controller.signal)) {
          if (chunk.error) throw new Error(chunk.error);
          if (chunk.content) {
            appendStreamContent(chunk.content);
            assistantContent += chunk.content;
          }
          if (chunk.blueprint) setGeneratedBlueprint(chunk.blueprint);
          if (chunk.done) break;
        }

        // 生成完成后添加助手消息并切换到 configure 阶段
        if (assistantContent) {
          addMessage({ role: 'assistant', content: assistantContent });
        }
        setPhase('configure');
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          setPhase('input');
          return;
        }
        setError(extractApiError(err, 'Blueprint 生成失败，请重试'));
        setPhase('input');
      } finally {
        abortControllerRef.current = null;
        setGenerating(false);
        void queryClient.invalidateQueries({ queryKey: builderKeys.session(sessionId) });
      }
    },
    [
      appendStreamContent,
      setGeneratedBlueprint,
      setGenerating,
      setError,
      addMessage,
      setPhase,
      resetStream,
      queryClient,
      token,
      abort,
    ],
  );

  // Blueprint 迭代优化
  const startRefinement = useCallback(
    async (sessionId: number, message: string) => {
      abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;
      setGenerating(true);
      resetStream();

      // 先添加用户消息
      addMessage({ role: 'user', content: message });

      try {
        const url = `${env.VITE_API_BASE_URL}/api/v1/builder/sessions/${sessionId}/refine`;
        let assistantContent = '';

        for await (const chunk of streamBlueprintRefine(
          url,
          token,
          { message },
          controller.signal,
        )) {
          if (chunk.error) throw new Error(chunk.error);
          if (chunk.content) {
            appendStreamContent(chunk.content);
            assistantContent += chunk.content;
          }
          if (chunk.blueprint) setGeneratedBlueprint(chunk.blueprint);
          if (chunk.done) break;
        }

        if (assistantContent) {
          addMessage({ role: 'assistant', content: assistantContent });
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        setError(extractApiError(err, '优化失败，请重试'));
      } finally {
        abortControllerRef.current = null;
        setGenerating(false);
        void queryClient.invalidateQueries({ queryKey: builderKeys.session(sessionId) });
      }
    },
    [
      appendStreamContent,
      setGeneratedBlueprint,
      setGenerating,
      setError,
      addMessage,
      resetStream,
      queryClient,
      token,
      abort,
    ],
  );

  return { startGeneration, startRefinement, abort };
}
