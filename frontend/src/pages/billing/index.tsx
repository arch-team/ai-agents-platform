// BillingPage — 费用管理页面
// 布局: 左侧部门列表 + 右侧预算管理 & 成本报告

import { useState } from 'react';

import { BudgetTable, CostReportChart, DepartmentList } from '@/features/billing';
import type { DateRangeParams, Department } from '@/features/billing';
import { useAuth } from '@/features/auth';

function getDefaultDateRange(): DateRangeParams {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 30);
  return {
    start_date: start.toISOString().split('T')[0],
    end_date: end.toISOString().split('T')[0],
  };
}

export default function BillingPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [selectedDept, setSelectedDept] = useState<Department | null>(null);
  const [dateRange, setDateRange] = useState<DateRangeParams>(getDefaultDateRange);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">费用管理</h1>
        {/* 日期选择 */}
        <div className="flex items-center gap-2 text-sm">
          <label htmlFor="billing-start" className="text-gray-500">
            从
          </label>
          <input
            id="billing-start"
            type="date"
            className="rounded-md border border-gray-300 px-2 py-1 text-sm"
            value={dateRange.start_date}
            onChange={(e) => setDateRange((prev) => ({ ...prev, start_date: e.target.value }))}
          />
          <label htmlFor="billing-end" className="text-gray-500">
            至
          </label>
          <input
            id="billing-end"
            type="date"
            className="rounded-md border border-gray-300 px-2 py-1 text-sm"
            value={dateRange.end_date}
            onChange={(e) => setDateRange((prev) => ({ ...prev, end_date: e.target.value }))}
          />
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* 左侧: 部门列表 */}
        <div className="col-span-4">
          <DepartmentList
            selectedId={selectedDept?.id ?? null}
            onSelect={setSelectedDept}
            isAdmin={isAdmin}
          />
        </div>

        {/* 右侧: 预算 + 成本报告 */}
        <div className="col-span-8 space-y-6">
          {selectedDept ? (
            <>
              <BudgetTable
                departmentId={selectedDept.id}
                departmentName={selectedDept.name}
                isAdmin={isAdmin}
              />
              <CostReportChart departmentId={selectedDept.id} dateRange={dateRange} />
            </>
          ) : (
            <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-gray-200">
              <p className="text-gray-400">请在左侧选择一个部门查看预算和成本</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
