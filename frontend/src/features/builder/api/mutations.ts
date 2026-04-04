// Builder 会话相关 mutations

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { Agent } from '@/entities/agent';
import { agentKeys } from '@/features/agents';
import { apiClient } from '@/shared/api';

import { builderKeys } from './queries';
import type {
  BuilderSession,
  ConfirmBuilderRequest,
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

// V1: 确认创建 Agent
export function useConfirmBuilderSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      sessionId,
      nameOverride,
    }: {
      sessionId: number;
      nameOverride?: string;
    }) => {
      const { data } = await apiClient.post<ConfirmBuilderSessionResponse>(
        `/api/v1/builder/sessions/${sessionId}/confirm`,
        { name_override: nameOverride },
      );
      return data;
    },
    onSuccess: (_data, { sessionId }) => {
      void queryClient.invalidateQueries({ queryKey: builderKeys.session(sessionId) });
    },
  });
}

// V2: 确认创建 Agent（支持 auto_start_testing）
export function useConfirmAndTest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ sessionId, ...body }: ConfirmBuilderRequest & { sessionId: number }) => {
      const { data } = await apiClient.post<ConfirmBuilderSessionResponse>(
        `/api/v1/builder/sessions/${sessionId}/confirm`,
        body,
      );
      return data;
    },
    onSuccess: (_data, { sessionId }) => {
      void queryClient.invalidateQueries({ queryKey: builderKeys.session(sessionId) });
      void queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
  });
}

// V2: 开始测试 (DRAFT → TESTING)
export function useStartTesting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (agentId: number) => {
      const { data } = await apiClient.post<Agent>(`/api/v1/agents/${agentId}/start-testing`);
      return data;
    },
    onSuccess: (agent) => {
      void queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      queryClient.setQueryData(agentKeys.detail(agent.id), agent);
    },
  });
}

// V2: 上线发布 (TESTING → ACTIVE)
export function useGoLive() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (agentId: number) => {
      const { data } = await apiClient.post<Agent>(`/api/v1/agents/${agentId}/go-live`);
      return data;
    },
    onSuccess: (agent) => {
      void queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      queryClient.setQueryData(agentKeys.detail(agent.id), agent);
    },
  });
}

// 取消 Builder 会话
export function useCancelBuilderSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (sessionId: number) => {
      const { data } = await apiClient.post<BuilderSession>(
        `/api/v1/builder/sessions/${sessionId}/cancel`,
      );
      return data;
    },
    onSuccess: (_data, sessionId) => {
      void queryClient.invalidateQueries({ queryKey: builderKeys.session(sessionId) });
    },
  });
}
