import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import type {
  Template,
  TemplateListResponse,
  TemplateFilters,
  CreateTemplateRequest,
  UpdateTemplateRequest,
} from './types';

// Query Key Factory
export const templateKeys = {
  all: ['templates'] as const,
  lists: () => [...templateKeys.all, 'list'] as const,
  list: (filters: TemplateFilters) => [...templateKeys.lists(), filters] as const,
  published: () => [...templateKeys.all, 'published'] as const,
  details: () => [...templateKeys.all, 'detail'] as const,
  detail: (id: number) => [...templateKeys.details(), id] as const,
};

// 查询模板列表
export function useTemplates(filters?: TemplateFilters) {
  return useQuery({
    queryKey: templateKeys.list(filters ?? {}),
    queryFn: async () => {
      const { data } = await apiClient.get<TemplateListResponse>('/api/v1/templates', {
        params: filters,
      });
      return data;
    },
  });
}

// 查询已发布模板
export function usePublishedTemplates() {
  return useQuery({
    queryKey: templateKeys.published(),
    queryFn: async () => {
      const { data } = await apiClient.get<TemplateListResponse>('/api/v1/templates/published');
      return data;
    },
  });
}

// 查询单个模板详情
export function useTemplate(id: number | undefined) {
  return useQuery({
    queryKey: templateKeys.detail(id!),
    queryFn: async () => {
      const { data } = await apiClient.get<Template>(`/api/v1/templates/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// 创建模板
export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dto: CreateTemplateRequest) => {
      const { data } = await apiClient.post<Template>('/api/v1/templates', dto);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

// 更新模板
export function useUpdateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...dto }: UpdateTemplateRequest & { id: number }) => {
      const { data } = await apiClient.put<Template>(`/api/v1/templates/${id}`, dto);
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
      queryClient.setQueryData(templateKeys.detail(data.id), data);
    },
  });
}

// 删除模板
export function useDeleteTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/api/v1/templates/${id}`);
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
      queryClient.removeQueries({ queryKey: templateKeys.detail(id) });
    },
  });
}

// 发布模板
export function usePublishTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<Template>(`/api/v1/templates/${id}/publish`);
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
      queryClient.invalidateQueries({ queryKey: templateKeys.published() });
      queryClient.setQueryData(templateKeys.detail(data.id), data);
    },
  });
}

// 归档模板
export function useArchiveTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<Template>(`/api/v1/templates/${id}/archive`);
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
      queryClient.invalidateQueries({ queryKey: templateKeys.published() });
      queryClient.setQueryData(templateKeys.detail(data.id), data);
    },
  });
}
