// Billing API 类型定义

// ── Department ──

export interface Department {
  id: number;
  name: string;
  code: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DepartmentListResponse {
  items: Department[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CreateDepartmentRequest {
  name: string;
  code: string;
  description?: string;
}

export interface UpdateDepartmentRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
}

// ── Budget ──

export interface Budget {
  id: number;
  department_id: number;
  year: number;
  month: number;
  budget_amount: number;
  used_amount: number;
  alert_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface BudgetListResponse {
  items: Budget[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CreateBudgetRequest {
  department_id: number;
  year: number;
  month: number;
  budget_amount: number;
  alert_threshold?: number;
}

export interface UpdateBudgetRequest {
  budget_amount?: number;
  alert_threshold?: number;
}

// ── Cost Report ──

export interface DepartmentCostPoint {
  date: string;
  department_code: string;
  amount: number;
  currency: string;
}

export interface DepartmentCostReport {
  department_id: number;
  department_code: string;
  department_name: string;
  total_cost: number;
  budget_amount: number;
  used_percentage: number;
  daily_costs: DepartmentCostPoint[];
  start_date: string;
  end_date: string;
  currency: string;
}

// ── 查询参数 ──

export interface DateRangeParams {
  start_date: string;
  end_date: string;
}
