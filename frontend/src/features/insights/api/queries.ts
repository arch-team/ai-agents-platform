// Insights API 查询 hooks

import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import type {
  DateRangeParams,
  CostBreakdownResponse,
  UsageTrendResponse,
  InsightsSummaryResponse,
} from './types';

// Query Key Factory
export const insightKeys = {
  all: ['insights'] as const,
  costBreakdown: (params: DateRangeParams) =>
    [...insightKeys.all, 'cost-breakdown', params] as const,
  usageTrends: (params: DateRangeParams) => [...insightKeys.all, 'usage-trends', params] as const,
  summary: (params: DateRangeParams) => [...insightKeys.all, 'summary', params] as const,
};

// 查询成本归因
export function useCostBreakdown(params: DateRangeParams) {
  return useQuery({
    queryKey: insightKeys.costBreakdown(params),
    queryFn: async () => {
      const { data } = await apiClient.get<CostBreakdownResponse>(
        '/api/v1/insights/cost-breakdown',
        {
          params,
        },
      );
      return data;
    },
  });
}

// 查询使用趋势
export function useUsageTrends(params: DateRangeParams) {
  return useQuery({
    queryKey: insightKeys.usageTrends(params),
    queryFn: async () => {
      const { data } = await apiClient.get<UsageTrendResponse>('/api/v1/insights/usage-trends', {
        params,
      });
      return data;
    },
  });
}

// 查询概览统计
export function useInsightsSummary(params: DateRangeParams) {
  return useQuery({
    queryKey: insightKeys.summary(params),
    queryFn: async () => {
      const { data } = await apiClient.get<InsightsSummaryResponse>('/api/v1/insights/summary', {
        params,
      });
      return data;
    },
  });
}
