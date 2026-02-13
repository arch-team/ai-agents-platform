// Evaluation 模块 React Query hooks

import { useQuery, useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import type {
  TestSuite,
  TestSuiteListResponse,
  CreateTestSuiteRequest,
  UpdateTestSuiteRequest,
  TestSuiteFilters,
  TestCase,
  TestCaseListResponse,
  CreateTestCaseRequest,
  UpdateTestCaseRequest,
  EvaluationRun,
  EvaluationRunListResponse,
  CreateEvaluationRunRequest,
  EvaluationRunFilters,
  EvaluationResultListResponse,
} from './types';

// -- Query Key Factory --

export const testSuiteKeys = {
  all: ['test-suites'] as const,
  lists: () => [...testSuiteKeys.all, 'list'] as const,
  list: (filters: TestSuiteFilters) => [...testSuiteKeys.lists(), filters] as const,
  details: () => [...testSuiteKeys.all, 'detail'] as const,
  detail: (id: number) => [...testSuiteKeys.details(), id] as const,
  cases: (suiteId: number) => [...testSuiteKeys.all, suiteId, 'cases'] as const,
};

export const evaluationRunKeys = {
  all: ['evaluation-runs'] as const,
  lists: () => [...evaluationRunKeys.all, 'list'] as const,
  list: (filters: EvaluationRunFilters) => [...evaluationRunKeys.lists(), filters] as const,
  details: () => [...evaluationRunKeys.all, 'detail'] as const,
  detail: (id: number) => [...evaluationRunKeys.details(), id] as const,
  results: (runId: number) => [...evaluationRunKeys.all, runId, 'results'] as const,
};

// -- 通用回调 --

function invalidateAndUpdateSuite(queryClient: QueryClient, suite: TestSuite) {
  queryClient.invalidateQueries({ queryKey: testSuiteKeys.lists() });
  queryClient.setQueryData(testSuiteKeys.detail(suite.id), suite);
}

// -- 测试集 Hooks --

/** 查询测试集列表 */
export function useTestSuites(filters?: TestSuiteFilters) {
  return useQuery({
    queryKey: testSuiteKeys.list(filters ?? {}),
    queryFn: async () => {
      const { data } = await apiClient.get<TestSuiteListResponse>('/api/v1/test-suites', {
        params: filters,
      });
      return data;
    },
  });
}

/** 查询测试集详情 */
export function useTestSuite(id: number | undefined) {
  return useQuery({
    queryKey: testSuiteKeys.detail(id!),
    queryFn: async () => {
      const { data } = await apiClient.get<TestSuite>(`/api/v1/test-suites/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

/** 创建测试集 */
export function useCreateTestSuite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dto: CreateTestSuiteRequest) => {
      const { data } = await apiClient.post<TestSuite>('/api/v1/test-suites', dto);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.lists() });
    },
  });
}

/** 更新测试集 */
export function useUpdateTestSuite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...dto }: UpdateTestSuiteRequest & { id: number }) => {
      const { data } = await apiClient.put<TestSuite>(`/api/v1/test-suites/${id}`, dto);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateSuite(queryClient, data),
  });
}

/** 删除测试集 */
export function useDeleteTestSuite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/api/v1/test-suites/${id}`);
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.lists() });
      queryClient.removeQueries({ queryKey: testSuiteKeys.detail(id) });
    },
  });
}

/** 激活测试集 */
export function useActivateTestSuite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<TestSuite>(`/api/v1/test-suites/${id}/activate`);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateSuite(queryClient, data),
  });
}

/** 归档测试集 */
export function useArchiveTestSuite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<TestSuite>(`/api/v1/test-suites/${id}/archive`);
      return data;
    },
    onSuccess: (data) => invalidateAndUpdateSuite(queryClient, data),
  });
}

// -- 测试用例 Hooks --

/** 查询测试用例列表 */
export function useTestCases(suiteId: number | undefined) {
  return useQuery({
    queryKey: testSuiteKeys.cases(suiteId!),
    queryFn: async () => {
      const { data } = await apiClient.get<TestCaseListResponse>(
        `/api/v1/test-suites/${suiteId}/cases`,
      );
      return data;
    },
    enabled: !!suiteId,
  });
}

/** 添加测试用例 */
export function useCreateTestCase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ suiteId, ...dto }: CreateTestCaseRequest & { suiteId: number }) => {
      const { data } = await apiClient.post<TestCase>(
        `/api/v1/test-suites/${suiteId}/cases`,
        dto,
      );
      return data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.cases(variables.suiteId) });
    },
  });
}

/** 更新测试用例 */
export function useUpdateTestCase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      suiteId,
      caseId,
      ...dto
    }: UpdateTestCaseRequest & { suiteId: number; caseId: number }) => {
      const { data } = await apiClient.put<TestCase>(
        `/api/v1/test-suites/${suiteId}/cases/${caseId}`,
        dto,
      );
      return data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.cases(variables.suiteId) });
    },
  });
}

/** 删除测试用例 */
export function useDeleteTestCase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ suiteId, caseId }: { suiteId: number; caseId: number }) => {
      await apiClient.delete(`/api/v1/test-suites/${suiteId}/cases/${caseId}`);
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.cases(variables.suiteId) });
    },
  });
}

// -- 评估运行 Hooks --

/** 创建评估运行 */
export function useCreateEvaluationRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dto: CreateEvaluationRunRequest) => {
      const { data } = await apiClient.post<EvaluationRun>('/api/v1/evaluation-runs', dto);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: evaluationRunKeys.lists() });
    },
  });
}

/** 查询评估运行列表 */
export function useEvaluationRuns(filters?: EvaluationRunFilters) {
  return useQuery({
    queryKey: evaluationRunKeys.list(filters ?? {}),
    queryFn: async () => {
      const { data } = await apiClient.get<EvaluationRunListResponse>('/api/v1/evaluation-runs', {
        params: filters,
      });
      return data;
    },
  });
}

/** 查询评估运行详情 */
export function useEvaluationRun(id: number | undefined) {
  return useQuery({
    queryKey: evaluationRunKeys.detail(id!),
    queryFn: async () => {
      const { data } = await apiClient.get<EvaluationRun>(`/api/v1/evaluation-runs/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

/** 查询评估结果 */
export function useEvaluationResults(runId: number | undefined) {
  return useQuery({
    queryKey: evaluationRunKeys.results(runId!),
    queryFn: async () => {
      const { data } = await apiClient.get<EvaluationResultListResponse>(
        `/api/v1/evaluation-runs/${runId}/results`,
      );
      return data;
    },
    enabled: !!runId,
  });
}
