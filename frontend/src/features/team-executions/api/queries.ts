// React Query hooks: Team Execution CRUD 操作

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';
import type { PageResponse } from '@/shared/types';

import type { CreateTeamExecutionDTO, TeamExecution, TeamExecutionLog } from './types';

// Query Key Factory
export const teamExecutionKeys = {
  all: ['team-executions'] as const,
  lists: () => [...teamExecutionKeys.all, 'list'] as const,
  list: (page?: number) => [...teamExecutionKeys.lists(), { page }] as const,
  details: () => [...teamExecutionKeys.all, 'detail'] as const,
  detail: (id: number) => [...teamExecutionKeys.details(), id] as const,
  logs: (id: number) => [...teamExecutionKeys.all, 'logs', id] as const,
};

// 执行列表
export function useTeamExecutions(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: teamExecutionKeys.list(page),
    queryFn: async () => {
      const { data } = await apiClient.get<PageResponse<TeamExecution>>('/api/v1/team-executions', {
        params: { page, page_size: pageSize },
      });
      return data;
    },
  });
}

// 执行详情
export function useTeamExecution(id: number | null) {
  return useQuery({
    queryKey: teamExecutionKeys.detail(id ?? 0),
    queryFn: async () => {
      const { data } = await apiClient.get<TeamExecution>(`/api/v1/team-executions/${id}`);
      return data;
    },
    enabled: id !== null,
    // 运行中的执行需要轮询
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'running' || status === 'pending' ? 3000 : false;
    },
  });
}

// 执行日志
export function useTeamExecutionLogs(id: number | null) {
  return useQuery({
    queryKey: teamExecutionKeys.logs(id ?? 0),
    queryFn: async () => {
      const { data } = await apiClient.get<TeamExecutionLog[]>(
        `/api/v1/team-executions/${id}/logs`,
      );
      return data;
    },
    enabled: id !== null,
  });
}

// 创建执行
export function useCreateTeamExecution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dto: CreateTeamExecutionDTO) => {
      const { data } = await apiClient.post<TeamExecution>('/api/v1/team-executions', dto);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: teamExecutionKeys.lists() });
    },
  });
}

// 取消执行
export function useCancelTeamExecution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<TeamExecution>(`/api/v1/team-executions/${id}/cancel`);
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: teamExecutionKeys.lists() });
      queryClient.setQueryData(teamExecutionKeys.detail(data.id), data);
    },
  });
}
