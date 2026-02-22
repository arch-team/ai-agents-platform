// 工具目录 API 类型定义

import type { PageResponse } from '@/shared/types';

// 工具类型（与后端 Python ToolType 枚举值一致：小写）
export type ToolType = 'mcp_server' | 'api' | 'function';

// 工具类型显示名
export const TOOL_TYPE_LABELS: Record<ToolType, string> = {
  mcp_server: 'MCP Server',
  api: 'API',
  function: 'Function',
};

// 工具状态（与后端 Python ToolStatus 枚举值一致：小写）
export type ToolStatus = 'draft' | 'pending_review' | 'approved' | 'rejected' | 'deprecated';

// 工具实体
export interface Tool {
  id: string;
  name: string;
  description: string;
  tool_type: ToolType;
  status: ToolStatus;
  version: string;
  configuration: Record<string, unknown>;
  created_by: string;
  created_at: string;
  updated_at: string;
  approved_by?: string;
  approved_at?: string;
  rejected_reason?: string;
}

// 创建工具请求
export interface CreateToolRequest {
  name: string;
  description: string;
  tool_type: ToolType;
  version?: string;
  configuration?: Record<string, unknown>;
}

// 更新工具请求
export type UpdateToolRequest = Partial<CreateToolRequest>;

// 拒绝工具请求
export interface RejectToolRequest {
  reason: string;
}

// 工具列表查询参数
export interface ToolFilters {
  page?: number;
  page_size?: number;
  status?: ToolStatus;
  tool_type?: ToolType;
  search?: string;
}

// 工具列表响应
export type ToolListResponse = PageResponse<Tool>;
