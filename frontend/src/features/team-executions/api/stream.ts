// Team Execution 流式日志 — 通过 SSE + Zustand store 管理

import { useCallback } from 'react';

import { useQueryClient } from '@tanstack/react-query';

import { env } from '@/shared/config/env';
import { extractApiError } from '@/shared/lib/extractApiError';

import { streamSSE } from '../lib/sse';
import { useTeamExecActions } from '../model/store';

import { teamExecutionKeys } from './queries';

/**
 * 流式接收 Team Execution 日志 hook
 * 通过 GET SSE 连接接收实时日志，用 Zustand store 管理状态
 *
 * @param token - 认证 token，由调用方从 auth store 获取后传入（避免跨 feature 依赖）
 */
export function useTeamExecutionStream(token: string | null) {
  const { appendLog, setStreaming, setError, clearError, clearLogs } = useTeamExecActions();
  const queryClient = useQueryClient();

  const startStream = useCallback(
    async (executionId: number) => {
      clearLogs();
      clearError();
      setStreaming(true);

      try {
        const url = `${env.VITE_API_BASE_URL}/api/v1/team-executions/${executionId}/stream`;

        for await (const chunk of streamSSE(url, token)) {
          if (chunk.error) {
            throw new Error(chunk.error);
          }

          if (chunk.content) {
            appendLog({
              sequence: chunk.sequence ?? 0,
              content: chunk.content,
              agentName: chunk.agent_name ?? '',
            });
          }

          if (chunk.done) {
            break;
          }
        }
      } catch (err) {
        setError(extractApiError(err, '接收执行日志失败'));
      } finally {
        setStreaming(false);
        // 流结束后刷新执行详情和日志缓存
        queryClient.invalidateQueries({ queryKey: teamExecutionKeys.detail(executionId) });
        queryClient.invalidateQueries({ queryKey: teamExecutionKeys.logs(executionId) });
      }
    },
    [appendLog, clearLogs, setStreaming, setError, clearError, queryClient, token],
  );

  return { startStream };
}
