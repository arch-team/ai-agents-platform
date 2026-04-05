import { useQuery, useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import type { Agent } from '@/entities/agent';
import { apiClient } from '@/shared/api';

import type { AgentFilters } from '../model/types';

import type {
  AgentListResponse,
  AgentPreviewResponse,
  BlueprintDetail,
  CreateAgentRequest,
  UpdateAgentRequest,
} from './types';

// Query Key Factory
export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (filters: AgentFilters) => [...agentKeys.lists(), filters] as const,
  details: () => [...agentKeys.all, 'detail'] as const,
  detail: (id: number) => [...agentKeys.details(), id] as const,
  blueprint: (id: number) => [...agentKeys.all, 'blueprint', id] as const,
};

// 刷新列表缓存并更新详情缓存的通用回调
function invalidateAndUpdateDetail(queryClient: QueryClient, agent: Agent) {
  queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
  queryClient.setQueryData(agentKeys.detail(agent.id), agent);
}

// 查询 Agent 列表
export function useAgents(filters?: AgentFilters) {
  return useQuery({
    queryKey: agentKeys.list(filters ?? {}),
    queryFn: async () => {
      const { data } = await apiClient.get<AgentListResponse>('/api/v1/agents', {
        params: filters,
      });
      return data;
    },
  });
}

// 查询单个 Agent 详情
export function useAgent(id: number | undefined) {
  return useQuery({
    queryKey: agentKeys.detail(id ?? 0),
    queryFn: async () => {
      const { data } = await apiClient.get<Agent>(`/api/v1/agents/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// 创建 Agent
export function useCreateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dto: CreateAgentRequest) => {
      const { data } = await apiClient.post<Agent>('/api/v1/agents', dto);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
  });
}

// 更新 Agent
export function useUpdateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...dto }: UpdateAgentRequest & { id: number }) => {
      const { data } = await apiClient.put<Agent>(`/api/v1/agents/${id}`, dto);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateDetail(queryClient, data),
  });
}

// 删除 Agent
export function useDeleteAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/api/v1/agents/${id}`);
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      queryClient.removeQueries({ queryKey: agentKeys.detail(id) });
    },
  });
}

// 激活 Agent
export function useActivateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<Agent>(`/api/v1/agents/${id}/activate`);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateDetail(queryClient, data),
  });
}

// 归档 Agent
export function useArchiveAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<Agent>(`/api/v1/agents/${id}/archive`);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateDetail(queryClient, data),
  });
}

// 查询 Agent Blueprint 详情
export function useAgentBlueprint(agentId: number | undefined) {
  return useQuery({
    queryKey: agentKeys.blueprint(agentId ?? 0),
    queryFn: async () => {
      const { data } = await apiClient.get<BlueprintDetail>(`/api/v1/agents/${agentId}/blueprint`);
      return data;
    },
    enabled: !!agentId,
  });
}

// 预览 Agent（单轮测试对话，不持久化）
export function usePreviewAgent() {
  return useMutation({
    mutationFn: async ({ agentId, prompt }: { agentId: number; prompt: string }) => {
      const { data } = await apiClient.post<AgentPreviewResponse>(
        `/api/v1/agents/${agentId}/preview`,
        { prompt },
      );
      return data;
    },
  });
}

// ── Blueprint 生命周期 mutations ──

// 开始测试 (DRAFT → TESTING)
export function useStartTesting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<Agent>(`/api/v1/agents/${id}/start-testing`);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateDetail(queryClient, data),
  });
}

// 上线发布 (TESTING → ACTIVE)
export function useGoLive() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<Agent>(`/api/v1/agents/${id}/go-live`);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateDetail(queryClient, data),
  });
}

// 下线归档 (ACTIVE → ARCHIVED)
export function useTakeOffline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<Agent>(`/api/v1/agents/${id}/take-offline`);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateDetail(queryClient, data),
  });
}
