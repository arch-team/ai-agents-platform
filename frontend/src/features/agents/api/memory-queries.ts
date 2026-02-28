// Memory API 查询 hooks

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

// Memory 记忆条目
export interface MemoryItem {
  memory_id: string;
  content: string;
  topic: string;
  relevance_score: number;
}

// 保存记忆请求
export interface SaveMemoryRequest {
  content: string;
  topic?: string;
}

// 搜索记忆请求
export interface SearchMemoryRequest {
  query: string;
  max_results?: number;
}

// Memory Query Key Factory
export const memoryKeys = {
  all: (agentId: number) => ['agents', agentId, 'memories'] as const,
  list: (agentId: number) => [...memoryKeys.all(agentId), 'list'] as const,
  search: (agentId: number, query: string) =>
    [...memoryKeys.all(agentId), 'search', query] as const,
  detail: (agentId: number, memoryId: string) =>
    [...memoryKeys.all(agentId), 'detail', memoryId] as const,
};

// 查询 Agent 记忆列表
export function useAgentMemories(agentId: number | undefined, maxResults?: number) {
  return useQuery({
    queryKey: memoryKeys.list(agentId ?? 0),
    queryFn: async () => {
      const params = maxResults ? { max_results: maxResults } : {};
      const { data } = await apiClient.get<MemoryItem[]>(`/api/v1/agents/${agentId}/memories`, {
        params,
      });
      return data;
    },
    enabled: !!agentId,
  });
}

// 搜索 Agent 记忆
export function useSearchMemories(agentId: number) {
  return useMutation({
    mutationFn: async (dto: SearchMemoryRequest) => {
      const { data } = await apiClient.post<MemoryItem[]>(
        `/api/v1/agents/${agentId}/memories/search`,
        dto,
      );
      return data;
    },
  });
}

// 保存记忆
export function useSaveMemory(agentId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dto: SaveMemoryRequest) => {
      const { data } = await apiClient.post<MemoryItem>(`/api/v1/agents/${agentId}/memories`, dto);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: memoryKeys.list(agentId) });
    },
  });
}

// 删除记忆
export function useDeleteMemory(agentId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (memoryId: string) => {
      await apiClient.delete(`/api/v1/agents/${agentId}/memories/${memoryId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: memoryKeys.list(agentId) });
    },
  });
}
