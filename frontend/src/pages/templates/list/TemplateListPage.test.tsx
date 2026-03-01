// 模板列表页面 smoke test
import { screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { renderWithProviders } from '../../../../tests/utils';

// Mock feature 组件，避免 API 调用
vi.mock('@/features/templates', () => ({
  TemplateList: ({
    onSelect,
    onCreate,
  }: {
    onSelect: (id: string) => void;
    onCreate: () => void;
  }) => (
    <ul role="list" aria-label="模板列表">
      <li>
        <button onClick={() => onSelect('1')}>选择</button>
        <button onClick={onCreate}>创建</button>
      </li>
    </ul>
  ),
  TemplateCreateDialog: ({ open }: { open: boolean }) =>
    open ? (
      <div role="dialog" aria-label="创建模板">
        创建对话框
      </div>
    ) : null,
}));

import TemplateListPage from './index';

describe('TemplateListPage', () => {
  it('should render page title', () => {
    renderWithProviders(<TemplateListPage />);
    expect(screen.getByRole('heading', { level: 1, name: '模板管理' })).toBeInTheDocument();
  });

  it('should render template list component', () => {
    renderWithProviders(<TemplateListPage />);
    expect(screen.getByRole('list', { name: '模板列表' })).toBeInTheDocument();
  });
});
