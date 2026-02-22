// Builder 会话相关 React Query hooks

import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import type { BuilderSession } from './types';

// Query Key Factory
export const builderKeys = {
  all: ['builder'] as const,
  sessions: () => [...builderKeys.all, 'sessions'] as const,
  session: (id: number) => [...builderKeys.sessions(), id] as const,
};

// 获取 Builder 会话详情
export function useGetBuilderSession(sessionId: number | null) {
  return useQuery({
    queryKey: builderKeys.session(sessionId ?? 0),
    queryFn: async () => {
      const { data } = await apiClient.get<BuilderSession>(`/api/v1/builder/sessions/${sessionId}`);
      return data;
    },
    enabled: !!sessionId,
  });
}
