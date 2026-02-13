import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

export interface DashboardSummary {
  agents_total: number;
  conversations_total: number;
  team_executions_total: number;
}

export const dashboardKeys = {
  all: ['dashboard'] as const,
  summary: () => [...dashboardKeys.all, 'summary'] as const,
};

export function useDashboardSummary() {
  return useQuery({
    queryKey: dashboardKeys.summary(),
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardSummary>('/api/v1/stats/summary');
      return data;
    },
  });
}
