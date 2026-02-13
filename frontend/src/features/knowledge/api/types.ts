import type { PageResponse } from '@/shared/types';

// 知识库状态
export type KnowledgeBaseStatus = 'CREATING' | 'ACTIVE' | 'SYNCING' | 'FAILED';

// 知识库实体
export interface KnowledgeBase {
  id: number;
  name: string;
  description: string;
  status: KnowledgeBaseStatus;
  document_count: number;
  created_at: string;
  updated_at: string;
}

// 文档实体
export interface KnowledgeDocument {
  id: number;
  knowledge_base_id: number;
  file_name: string;
  file_size: number;
  content_type: string;
  status: string;
  created_at: string;
}

// 请求类型
export interface CreateKnowledgeBaseRequest {
  name: string;
  description?: string;
}

export interface UpdateKnowledgeBaseRequest {
  name?: string;
  description?: string;
}

export interface QueryKnowledgeBaseRequest {
  query: string;
  top_k?: number;
}

// RAG 检索结果
export interface QueryResult {
  content: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface QueryKnowledgeBaseResponse {
  results: QueryResult[];
}

// 列表响应
export type KnowledgeBaseListResponse = PageResponse<KnowledgeBase>;
export type KnowledgeDocumentListResponse = PageResponse<KnowledgeDocument>;

// 筛选器
export interface KnowledgeBaseFilters {
  status?: KnowledgeBaseStatus;
  page?: number;
  page_size?: number;
}
