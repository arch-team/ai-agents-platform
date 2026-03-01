// 评估列表页面 smoke test
import { screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { renderWithProviders } from '../../../../tests/utils';

// Mock feature 组件，避免 API 调用
vi.mock('@/features/evaluation', () => ({
  TestSuiteList: ({
    onSelect,
    onCreate,
  }: {
    onSelect: (id: string) => void;
    onCreate: () => void;
  }) => (
    <ul role="list" aria-label="测试集列表">
      <li>
        <button onClick={() => onSelect('1')}>选择</button>
        <button onClick={onCreate}>创建</button>
      </li>
    </ul>
  ),
  TestSuiteCreateDialog: ({ onClose }: { onClose: () => void }) => (
    <div role="dialog" aria-label="创建测试集">
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
    expect(screen.getByRole('list', { name: '测试集列表' })).toBeInTheDocument();
  });
});
