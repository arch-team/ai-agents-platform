// 预算管理表格

import { useState } from 'react';

import { useBudgets, useCreateBudget, useCurrentBudget, useUpdateBudget } from '../api/queries';

import { Button, Card, ErrorMessage, Input, Spinner } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

interface BudgetTableProps {
  departmentId: number;
  departmentName: string;
  isAdmin: boolean;
}

function formatMonth(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, '0')}`;
}

export function BudgetTable({ departmentId, departmentName, isAdmin }: BudgetTableProps) {
  const now = new Date();
  const { data: currentBudget, isLoading: loadingCurrent } = useCurrentBudget(
    departmentId,
    now.getFullYear(),
    now.getMonth() + 1,
  );
  const { data: budgetList, isLoading: loadingList, error } = useBudgets(departmentId);
  const createMutation = useCreateBudget();
  const updateMutation = useUpdateBudget();

  const [showForm, setShowForm] = useState(false);
  const [formYear, setFormYear] = useState(String(now.getFullYear()));
  const [formMonth, setFormMonth] = useState(String(now.getMonth() + 1));
  const [formAmount, setFormAmount] = useState('');
  const [formThreshold, setFormThreshold] = useState('0.8');

  if (error) return <ErrorMessage error={extractApiError(error, '加载预算失败')} />;

  const handleCreate = async () => {
    if (!formAmount) return;
    await createMutation.mutateAsync({
      department_id: departmentId,
      year: Number(formYear),
      month: Number(formMonth),
      budget_amount: Number(formAmount),
      alert_threshold: Number(formThreshold),
    });
    setFormAmount('');
    setShowForm(false);
  };

  const usedPct = currentBudget
    ? (currentBudget.used_amount / currentBudget.budget_amount) * 100
    : 0;
  const isWarning =
    currentBudget &&
    currentBudget.alert_threshold > 0 &&
    usedPct >= currentBudget.alert_threshold * 100;

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">{departmentName} — 预算</h3>
        {isAdmin && (
          <Button size="sm" onClick={() => setShowForm(!showForm)}>
            {showForm ? '取消' : '+ 新建预算'}
          </Button>
        )}
      </div>

      {/* 当月预算摘要 */}
      {loadingCurrent ? (
        <Spinner />
      ) : currentBudget ? (
        <div
          className={`mb-4 rounded-lg p-4 ${isWarning ? 'bg-amber-50 ring-1 ring-amber-200' : 'bg-gray-50'}`}
        >
          <div className="mb-2 text-sm text-gray-500">
            当月预算 ({formatMonth(currentBudget.year, currentBudget.month)})
          </div>
          <div className="flex items-end gap-6">
            <div>
              <div className="text-2xl font-bold text-gray-900">
                ${currentBudget.budget_amount.toLocaleString()}
              </div>
              <div className="text-xs text-gray-400">预算额度</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">
                ${currentBudget.used_amount.toLocaleString()}
              </div>
              <div className="text-xs text-gray-400">已使用</div>
            </div>
            <div>
              <div
                className={`text-2xl font-bold ${isWarning ? 'text-amber-600' : 'text-green-600'}`}
              >
                {usedPct.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-400">使用率</div>
            </div>
          </div>
          {/* 进度条 */}
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-200">
            <div
              className={`h-full rounded-full transition-all ${isWarning ? 'bg-amber-500' : 'bg-blue-500'}`}
              style={{ width: `${Math.min(usedPct, 100)}%` }}
            />
          </div>
        </div>
      ) : (
        <p className="mb-4 text-sm text-gray-500">当月暂无预算配置</p>
      )}

      {/* 创建表单 */}
      {showForm && (
        <div className="mb-4 space-y-2 rounded-lg border border-blue-100 bg-blue-50 p-3">
          <div className="flex gap-2">
            <Input
              placeholder="年份"
              value={formYear}
              onChange={(e) => setFormYear(e.target.value)}
              className="w-24"
            />
            <Input
              placeholder="月份"
              value={formMonth}
              onChange={(e) => setFormMonth(e.target.value)}
              className="w-20"
            />
            <Input
              placeholder="预算金额 (USD)"
              value={formAmount}
              onChange={(e) => setFormAmount(e.target.value)}
              className="flex-1"
            />
            <Input
              placeholder="告警阈值"
              value={formThreshold}
              onChange={(e) => setFormThreshold(e.target.value)}
              className="w-24"
            />
          </div>
          <Button size="sm" onClick={handleCreate} disabled={createMutation.isPending}>
            {createMutation.isPending ? '创建中...' : '确认'}
          </Button>
        </div>
      )}

      {/* 预算历史列表 */}
      {loadingList ? (
        <Spinner />
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="border-b text-xs uppercase text-gray-500">
            <tr>
              <th className="py-2">月份</th>
              <th className="py-2 text-right">预算</th>
              <th className="py-2 text-right">已用</th>
              <th className="py-2 text-right">使用率</th>
              {isAdmin && <th className="py-2 text-right">操作</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {(budgetList?.items ?? []).map((b) => {
              const pct = b.budget_amount > 0 ? (b.used_amount / b.budget_amount) * 100 : 0;
              return (
                <tr key={b.id} className="hover:bg-gray-50">
                  <td className="py-2">{formatMonth(b.year, b.month)}</td>
                  <td className="py-2 text-right">${b.budget_amount.toLocaleString()}</td>
                  <td className="py-2 text-right">${b.used_amount.toLocaleString()}</td>
                  <td className="py-2 text-right">{pct.toFixed(1)}%</td>
                  {isAdmin && (
                    <td className="py-2 text-right">
                      <button
                        className="text-xs text-blue-600 hover:underline"
                        onClick={() => {
                          const newAmount = window.prompt('新预算金额:', String(b.budget_amount));
                          if (newAmount)
                            updateMutation.mutate({ id: b.id, budget_amount: Number(newAmount) });
                        }}
                        aria-label={`编辑 ${formatMonth(b.year, b.month)} 预算`}
                      >
                        编辑
                      </button>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </Card>
  );
}
