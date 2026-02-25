// Billing React Query hooks + Key Factory

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import type {
  Budget,
  BudgetListResponse,
  CreateBudgetRequest,
  CreateDepartmentRequest,
  DateRangeParams,
  Department,
  DepartmentCostReport,
  DepartmentListResponse,
  UpdateBudgetRequest,
  UpdateDepartmentRequest,
} from './types';

// Key Factory
export const billingKeys = {
  all: ['billing'] as const,
  departments: () => [...billingKeys.all, 'departments'] as const,
  departmentList: (page: number, pageSize: number) =>
    [...billingKeys.departments(), 'list', page, pageSize] as const,
  budgets: () => [...billingKeys.all, 'budgets'] as const,
  budgetList: (departmentId: number, page: number) =>
    [...billingKeys.budgets(), departmentId, 'list', page] as const,
  currentBudget: (departmentId: number, year: number, month: number) =>
    [...billingKeys.budgets(), departmentId, 'current', year, month] as const,
  costReport: (departmentId: number, params: DateRangeParams) =>
    [...billingKeys.all, 'cost-report', departmentId, params] as const,
};

// ── Department Queries ──

export function useDepartments(page = 1, pageSize = 50) {
  return useQuery({
    queryKey: billingKeys.departmentList(page, pageSize),
    queryFn: async () => {
      const { data } = await apiClient.get<DepartmentListResponse>('/api/v1/billing/departments', {
        params: { page, page_size: pageSize },
      });
      return data;
    },
  });
}

export function useCreateDepartment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (dto: CreateDepartmentRequest) =>
      apiClient.post<Department>('/api/v1/billing/departments', dto).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: billingKeys.departments() }),
  });
}

export function useUpdateDepartment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...dto }: UpdateDepartmentRequest & { id: number }) =>
      apiClient.put<Department>(`/api/v1/billing/departments/${id}`, dto).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: billingKeys.departments() }),
  });
}

export function useDeleteDepartment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v1/billing/departments/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: billingKeys.departments() }),
  });
}

// ── Budget Queries ──

export function useBudgets(departmentId: number, page = 1) {
  return useQuery({
    queryKey: billingKeys.budgetList(departmentId, page),
    queryFn: async () => {
      const { data } = await apiClient.get<BudgetListResponse>('/api/v1/billing/budgets', {
        params: { department_id: departmentId, page, page_size: 20 },
      });
      return data;
    },
    enabled: departmentId > 0,
  });
}

export function useCurrentBudget(departmentId: number, year: number, month: number) {
  return useQuery({
    queryKey: billingKeys.currentBudget(departmentId, year, month),
    queryFn: async () => {
      const { data } = await apiClient.get<Budget>(
        `/api/v1/billing/departments/${departmentId}/budgets/current`,
        { params: { year, month } },
      );
      return data;
    },
    enabled: departmentId > 0,
  });
}

export function useCreateBudget() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (dto: CreateBudgetRequest) =>
      apiClient.post<Budget>('/api/v1/billing/budgets', dto).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: billingKeys.budgets() }),
  });
}

export function useUpdateBudget() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...dto }: UpdateBudgetRequest & { id: number }) =>
      apiClient.put<Budget>(`/api/v1/billing/budgets/${id}`, dto).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: billingKeys.budgets() }),
  });
}

// ── Cost Report ──

export function useCostReport(departmentId: number, params: DateRangeParams) {
  return useQuery({
    queryKey: billingKeys.costReport(departmentId, params),
    queryFn: async () => {
      const { data } = await apiClient.get<DepartmentCostReport>(
        `/api/v1/billing/departments/${departmentId}/cost-report`,
        { params },
      );
      return data;
    },
    enabled: departmentId > 0,
  });
}
