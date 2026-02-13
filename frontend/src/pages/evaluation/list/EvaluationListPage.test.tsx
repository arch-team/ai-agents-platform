// 评估列表页面 smoke test
import { screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { renderWithProviders } from '../../../../tests/utils';

// Mock feature 组件，避免 API 调用
vi.mock('@/features/evaluation', () => ({
  TestSuiteList: ({ onSelect, onCreate }: { onSelect: (id: string) => void; onCreate: () => void }) => (
    <div data-testid="test-suite-list">
      <button onClick={() => onSelect('1')}>选择</button>
      <button onClick={onCreate}>创建</button>
    </div>
  ),
  TestSuiteCreateDialog: ({ onClose }: { onClose: () => void }) => (
    <div data-testid="test-suite-create-dialog">
      <button onClick={onClose}>关闭</button>
    </div>
  ),
}));

import EvaluationListPage from './index';

describe('EvaluationListPage', () => {
  it('should render page title', () => {
    renderWithProviders(<EvaluationListPage />);
    expect(screen.getByRole('heading', { level: 1, name: '评估管理' })).toBeInTheDocument();
  });

  it('should render test suite list component', () => {
    renderWithProviders(<EvaluationListPage />);
    expect(screen.getByTestId('test-suite-list')).toBeInTheDocument();
  });
});
