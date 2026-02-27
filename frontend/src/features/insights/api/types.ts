// Insights API 类型定义

// DateRangeParams 已移至 @/shared/types，此处重导出以保持向后兼容
export type { DateRangeParams } from '@/shared/types';

// Token 消耗归因项
export interface CostBreakdownItem {
  agent_id: string;
  agent_name: string;
  total_tokens: number;
  tokens_input: number;
  tokens_output: number;
  invocation_count: number;
}

// Token 消耗归因响应
export interface CostBreakdownResponse {
  items: CostBreakdownItem[];
  total_tokens: number;
  period: {
    start_date: string;
    end_date: string;
  };
}

// 使用趋势数据点
export interface UsageTrendPoint {
  date: string;
  invocation_count: number;
  total_tokens: number;
  unique_users: number;
}

// 使用趋势响应
export interface UsageTrendResponse {
  data_points: UsageTrendPoint[];
  period: {
    start_date: string;
    end_date: string;
  };
}

// 概览统计响应
export interface InsightsSummaryResponse {
  total_agents: number;
  active_agents: number;
  total_invocations: number;
  total_tokens: number;
  total_cost: number;
  period: {
    start_date: string;
    end_date: string;
  };
}
