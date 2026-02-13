// 模板列表页面 smoke test
import { screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { renderWithProviders } from '../../../../tests/utils';

// Mock feature 组件，避免 API 调用
vi.mock('@/features/templates', () => ({
  TemplateList: ({ onSelect, onCreate }: { onSelect: (id: string) => void; onCreate: () => void }) => (
    <div data-testid="template-list">
      <button onClick={() => onSelect('1')}>选择</button>
      <button onClick={onCreate}>创建</button>
    </div>
  ),
  TemplateCreateDialog: ({ open }: { open: boolean }) =>
    open ? <div data-testid="template-create-dialog">创建对话框</div> : null,
}));

import TemplateListPage from './index';

describe('TemplateListPage', () => {
  it('should render page title', () => {
    renderWithProviders(<TemplateListPage />);
    expect(screen.getByRole('heading', { level: 1, name: '模板管理' })).toBeInTheDocument();
  });

  it('should render template list component', () => {
    renderWithProviders(<TemplateListPage />);
    expect(screen.getByTestId('template-list')).toBeInTheDocument();
  });
});
