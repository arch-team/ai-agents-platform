import type { PageResponse } from '@/shared/types';

// 模板状态
export type TemplateStatus = 'draft' | 'published' | 'archived';

// 模板分类
export type TemplateCategory =
  | 'customer_service'
  | 'data_analysis'
  | 'content_creation'
  | 'code_assistant'
  | 'research'
  | 'automation'
  | 'other';

// 模板实体（后端 API 返回扁平结构，config 字段展开为顶层属性）
export interface Template {
  id: number;
  name: string;
  description: string;
  category: string;
  status: TemplateStatus;
  creator_id: number;
  system_prompt: string;
  model_id: string;
  temperature: number;
  max_tokens: number;
  tool_ids: number[];
  knowledge_base_ids: number[];
  tags: string[];
  usage_count: number;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
}

// 请求类型（后端 API 接受扁平结构）
export interface CreateTemplateRequest {
  name: string;
  description?: string;
  category: string;
  system_prompt: string;
  model_id?: string;
  temperature?: number;
  max_tokens?: number;
  tool_ids?: number[];
  knowledge_base_ids?: number[];
  tags?: string[];
}

export interface UpdateTemplateRequest {
  name?: string;
  description?: string;
  category?: string;
  system_prompt?: string;
  model_id?: string;
  temperature?: number;
  max_tokens?: number;
  tool_ids?: number[];
  knowledge_base_ids?: number[];
  tags?: string[];
}

// 列表响应
export type TemplateListResponse = PageResponse<Template>;

// 筛选器
export interface TemplateFilters {
  category?: TemplateCategory;
  status?: TemplateStatus;
  page?: number;
  page_size?: number;
}
