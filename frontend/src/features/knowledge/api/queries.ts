import { useQuery, useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import type {
  KnowledgeBase,
  KnowledgeBaseListResponse,
  KnowledgeDocumentListResponse,
  KnowledgeBaseFilters,
  CreateKnowledgeBaseRequest,
  UpdateKnowledgeBaseRequest,
  QueryKnowledgeBaseRequest,
  QueryKnowledgeBaseResponse,
  KnowledgeDocument,
} from './types';

// Query Key Factory
export const knowledgeKeys = {
  all: ['knowledge-bases'] as const,
  lists: () => [...knowledgeKeys.all, 'list'] as const,
  list: (filters: KnowledgeBaseFilters) => [...knowledgeKeys.lists(), filters] as const,
  details: () => [...knowledgeKeys.all, 'detail'] as const,
  detail: (id: number) => [...knowledgeKeys.details(), id] as const,
  documents: (kbId: number) => [...knowledgeKeys.all, 'documents', kbId] as const,
};

// 刷新列表缓存并更新详情缓存的通用回调
function invalidateAndUpdateDetail(queryClient: QueryClient, kb: KnowledgeBase) {
  queryClient.invalidateQueries({ queryKey: knowledgeKeys.lists() });
  queryClient.setQueryData(knowledgeKeys.detail(kb.id), kb);
}

// 文档变更后刷新文档列表和知识库详情（文档数量变化）
function invalidateDocumentsAndDetail(queryClient: QueryClient, kbId: number) {
  queryClient.invalidateQueries({ queryKey: knowledgeKeys.documents(kbId) });
  queryClient.invalidateQueries({ queryKey: knowledgeKeys.detail(kbId) });
}

// 查询知识库列表
export function useKnowledgeBases(filters?: KnowledgeBaseFilters) {
  return useQuery({
    queryKey: knowledgeKeys.list(filters ?? {}),
    queryFn: async () => {
      const { data } = await apiClient.get<KnowledgeBaseListResponse>('/api/v1/knowledge-bases', {
        params: filters,
      });
      return data;
    },
  });
}

// 查询单个知识库详情
export function useKnowledgeBase(id: number | undefined) {
  return useQuery({
    queryKey: knowledgeKeys.detail(id!),
    queryFn: async () => {
      const { data } = await apiClient.get<KnowledgeBase>(`/api/v1/knowledge-bases/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// 查询知识库文档列表
export function useKnowledgeDocuments(kbId: number | undefined) {
  return useQuery({
    queryKey: knowledgeKeys.documents(kbId!),
    queryFn: async () => {
      const { data } = await apiClient.get<KnowledgeDocumentListResponse>(
        `/api/v1/knowledge-bases/${kbId}/documents`,
      );
      return data;
    },
    enabled: !!kbId,
  });
}

// 创建知识库
export function useCreateKnowledgeBase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dto: CreateKnowledgeBaseRequest) => {
      const { data } = await apiClient.post<KnowledgeBase>('/api/v1/knowledge-bases', dto);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.lists() });
    },
  });
}

// 更新知识库
export function useUpdateKnowledgeBase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...dto }: UpdateKnowledgeBaseRequest & { id: number }) => {
      const { data } = await apiClient.put<KnowledgeBase>(`/api/v1/knowledge-bases/${id}`, dto);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateDetail(queryClient, data),
  });
}

// 删除知识库
export function useDeleteKnowledgeBase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/api/v1/knowledge-bases/${id}`);
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.lists() });
      queryClient.removeQueries({ queryKey: knowledgeKeys.detail(id) });
    },
  });
}

// 上传文档
export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ kbId, file }: { kbId: number; file: File }) => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await apiClient.post<KnowledgeDocument>(
        `/api/v1/knowledge-bases/${kbId}/documents`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      );
      return data;
    },
    onSuccess: (_data, variables) => invalidateDocumentsAndDetail(queryClient, variables.kbId),
  });
}

// 删除文档
export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ kbId, docId }: { kbId: number; docId: number }) => {
      await apiClient.delete(`/api/v1/knowledge-bases/${kbId}/documents/${docId}`);
    },
    onSuccess: (_data, variables) => invalidateDocumentsAndDetail(queryClient, variables.kbId),
  });
}

// 手动同步
export function useSyncKnowledgeBase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<KnowledgeBase>(`/api/v1/knowledge-bases/${id}/sync`);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateDetail(queryClient, data),
  });
}

// RAG 检索
export function useQueryKnowledgeBase() {
  return useMutation({
    mutationFn: async ({ id, ...dto }: QueryKnowledgeBaseRequest & { id: number }) => {
      const { data } = await apiClient.post<QueryKnowledgeBaseResponse>(
        `/api/v1/knowledge-bases/${id}/query`,
        dto,
      );
      return data;
    },
  });
}
