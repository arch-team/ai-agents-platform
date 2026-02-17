// 工具目录 API 查询 hooks

import { useQuery, useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import type {
  Tool,
  ToolFilters,
  ToolListResponse,
  CreateToolRequest,
  UpdateToolRequest,
  RejectToolRequest,
} from './types';

// Query Key Factory
export const toolKeys = {
  all: ['tools'] as const,
  lists: () => [...toolKeys.all, 'list'] as const,
  list: (filters: ToolFilters) => [...toolKeys.lists(), filters] as const,
  approved: () => [...toolKeys.all, 'approved'] as const,
  details: () => [...toolKeys.all, 'detail'] as const,
  detail: (id: string) => [...toolKeys.details(), id] as const,
};

// 刷新列表缓存并更新详情缓存的通用回调
function invalidateAndUpdateDetail(queryClient: QueryClient, tool: Tool) {
  queryClient.invalidateQueries({ queryKey: toolKeys.lists() });
  queryClient.setQueryData(toolKeys.detail(tool.id), tool);
}

// 查询工具列表
export function useTools(filters?: ToolFilters) {
  return useQuery({
    queryKey: toolKeys.list(filters ?? {}),
    queryFn: async () => {
      const { data } = await apiClient.get<ToolListResponse>('/api/v1/tools', {
        params: filters,
      });
      return data;
    },
  });
}

// 查询已审批工具列表
export function useApprovedTools() {
  return useQuery({
    queryKey: toolKeys.approved(),
    queryFn: async () => {
      const { data } = await apiClient.get<ToolListResponse>('/api/v1/tools/approved');
      return data;
    },
  });
}

// 查询单个工具详情
export function useTool(id: string | undefined) {
  return useQuery({
    queryKey: toolKeys.detail(id!),
    queryFn: async () => {
      const { data } = await apiClient.get<Tool>(`/api/v1/tools/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// 创建工具
export function useCreateTool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dto: CreateToolRequest) => {
      const { data } = await apiClient.post<Tool>('/api/v1/tools', dto);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: toolKeys.lists() });
    },
  });
}

// 更新工具
export function useUpdateTool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...dto }: UpdateToolRequest & { id: string }) => {
      const { data } = await apiClient.put<Tool>(`/api/v1/tools/${id}`, dto);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateDetail(queryClient, data),
  });
}

// 删除工具
export function useDeleteTool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/api/v1/tools/${id}`);
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: toolKeys.lists() });
      queryClient.removeQueries({ queryKey: toolKeys.detail(id) });
    },
  });
}

// 提交审批
export function useSubmitTool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<Tool>(`/api/v1/tools/${id}/submit`);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateDetail(queryClient, data),
  });
}

// 审批通过
export function useApproveTool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<Tool>(`/api/v1/tools/${id}/approve`);
      return data;
    },
    onSuccess: (data) => {
      invalidateAndUpdateDetail(queryClient, data);
      queryClient.invalidateQueries({ queryKey: toolKeys.approved() });
    },
  });
}

// 审批拒绝
export function useRejectTool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: RejectToolRequest & { id: string }) => {
      const { data } = await apiClient.post<Tool>(`/api/v1/tools/${id}/reject`, { reason });
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateDetail(queryClient, data),
  });
}

// 废弃工具
export function useDeprecateTool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<Tool>(`/api/v1/tools/${id}/deprecate`);
      return data;
    },
    onSuccess: (data) => {
      invalidateAndUpdateDetail(queryClient, data);
      queryClient.invalidateQueries({ queryKey: toolKeys.approved() });
    },
  });
}
