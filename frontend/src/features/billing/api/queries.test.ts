import { describe, expect, it } from 'vitest';

import { billingKeys } from './queries';

describe('billingKeys', () => {
  it('should generate department list key', () => {
    const key = billingKeys.departmentList(1, 50);
    expect(key).toEqual(['billing', 'departments', 'list', 1, 50]);
  });

  it('should generate budget list key', () => {
    const key = billingKeys.budgetList(1, 1);
    expect(key).toEqual(['billing', 'budgets', 1, 'list', 1]);
  });

  it('should generate current budget key', () => {
    const key = billingKeys.currentBudget(1, 2024, 3);
    expect(key).toEqual(['billing', 'budgets', 1, 'current', 2024, 3]);
  });

  it('should generate cost report key', () => {
    const params = { start_date: '2024-01-01', end_date: '2024-01-31' };
    const key = billingKeys.costReport(1, params);
    expect(key).toEqual(['billing', 'cost-report', 1, params]);
  });
});
