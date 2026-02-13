// Insights API 类型定义

// 时间范围查询参数
export interface DateRangeParams {
  start_date: string;
  end_date: string;
}

// 成本归因项
export interface CostBreakdownItem {
  agent_id: string;
  agent_name: string;
  total_cost: number;
  invocation_count: number;
  avg_cost_per_invocation: number;
}

// 成本归因响应
export interface CostBreakdownResponse {
  items: CostBreakdownItem[];
  total_cost: number;
  period: {
    start_date: string;
    end_date: string;
  };
}

// 使用趋势数据点
export interface UsageTrendPoint {
  date: string;
  invocation_count: number;
  total_cost: number;
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
  total_cost: number;
  avg_response_time_ms: number;
  period: {
    start_date: string;
    end_date: string;
  };
}
