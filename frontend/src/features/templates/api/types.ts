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

// 模板配置
export interface TemplateConfig {
  model_id: string;
  temperature: number;
  max_tokens: number;
  tools?: string[];
  knowledge_base_ids?: number[];
}

// 模板实体
export interface Template {
  id: number;
  name: string;
  description: string;
  category: TemplateCategory;
  status: TemplateStatus;
  system_prompt: string;
  config: TemplateConfig;
  author: string;
  use_count: number;
  created_at: string;
  updated_at: string;
}

// 请求类型
export interface CreateTemplateRequest {
  name: string;
  description?: string;
  category: TemplateCategory;
  system_prompt: string;
  config?: Partial<TemplateConfig>;
}

export interface UpdateTemplateRequest {
  name?: string;
  description?: string;
  category?: TemplateCategory;
  system_prompt?: string;
  config?: Partial<TemplateConfig>;
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
