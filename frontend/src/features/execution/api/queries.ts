// React Query hooks: 对话 CRUD 操作

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';
import type { PageResponse } from '@/shared/types';

import type { Conversation, ConversationDetail, CreateConversationDTO } from './types';

// Query Key Factory
export const conversationKeys = {
  all: ['conversations'] as const,
  lists: () => [...conversationKeys.all, 'list'] as const,
  list: (agentId?: number) => [...conversationKeys.lists(), { agentId }] as const,
  details: () => [...conversationKeys.all, 'detail'] as const,
  detail: (id: number) => [...conversationKeys.details(), id] as const,
};

// 对话列表
export function useConversations(agentId?: number) {
  return useQuery({
    queryKey: conversationKeys.list(agentId),
    queryFn: async () => {
      const params = agentId ? { agent_id: agentId } : {};
      const { data } = await apiClient.get<PageResponse<Conversation>>('/api/v1/conversations', {
        params,
      });
      return data;
    },
  });
}

// 对话详情（含消息历史）
export function useConversation(id: number | null) {
  return useQuery({
    queryKey: conversationKeys.detail(id ?? 0),
    queryFn: async () => {
      const { data } = await apiClient.get<ConversationDetail>(`/api/v1/conversations/${id}`);
      return data;
    },
    enabled: id !== null,
  });
}

// 创建对话
export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dto: CreateConversationDTO) => {
      const { data } = await apiClient.post<Conversation>('/api/v1/conversations', dto);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.lists() });
    },
  });
}

// 结束对话
export function useCompleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (conversationId: number) => {
      const { data } = await apiClient.post<Conversation>(
        `/api/v1/conversations/${conversationId}/complete`,
      );
      return data;
    },
    onSuccess: (_data, conversationId) => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.lists() });
      queryClient.invalidateQueries({ queryKey: conversationKeys.detail(conversationId) });
    },
  });
}
