// Builder 会话相关 mutations

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import { builderKeys } from './queries';
import type {
  BuilderSession,
  ConfirmBuilderSessionResponse,
  CreateBuilderSessionRequest,
} from './types';

// 创建 Builder 会话
export function useCreateBuilderSession() {
  return useMutation({
    mutationFn: async (dto: CreateBuilderSessionRequest) => {
      const { data } = await apiClient.post<BuilderSession>('/api/v1/builder/sessions', dto);
      return data;
    },
  });
}

// 确认创建 Agent（Builder 会话完成后调用）
export function useConfirmBuilderSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sessionId: number) => {
      const { data } = await apiClient.post<ConfirmBuilderSessionResponse>(
        `/api/v1/builder/sessions/${sessionId}/confirm`,
        {},
      );
      return data;
    },
    onSuccess: (_data, sessionId) => {
      // 刷新该会话的缓存
      void queryClient.invalidateQueries({ queryKey: builderKeys.session(sessionId) });
    },
  });
}
