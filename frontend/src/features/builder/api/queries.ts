// Builder 会话相关 React Query hooks

import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import type { AvailableSkillResponse, AvailableToolResponse, BuilderSession } from './types';

// Query Key Factory
export const builderKeys = {
  all: ['builder'] as const,
  sessions: () => [...builderKeys.all, 'sessions'] as const,
  session: (id: number) => [...builderKeys.sessions(), id] as const,
  availableTools: () => [...builderKeys.all, 'available-tools'] as const,
  availableSkills: () => [...builderKeys.all, 'available-skills'] as const,
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

// 获取可用工具列表
export function useAvailableTools() {
  return useQuery({
    queryKey: builderKeys.availableTools(),
    queryFn: async () => {
      const { data } = await apiClient.get<AvailableToolResponse[]>(
        '/api/v1/builder/available-tools',
      );
      return data;
    },
  });
}

// 获取可用 Skill 列表
export function useAvailableSkills() {
  return useQuery({
    queryKey: builderKeys.availableSkills(),
    queryFn: async () => {
      const { data } = await apiClient.get<AvailableSkillResponse[]>(
        '/api/v1/builder/available-skills',
      );
      return data;
    },
  });
}
