// 知识库列表页面 smoke test
import { screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { renderWithProviders } from '../../../../tests/utils';

// Mock feature 组件，避免 API 调用
vi.mock('@/features/knowledge', () => ({
  KnowledgeList: ({ onSelect, onCreate }: { onSelect: (id: string) => void; onCreate: () => void }) => (
    <div data-testid="knowledge-list">
      <button onClick={() => onSelect('1')}>选择</button>
      <button onClick={onCreate}>创建</button>
    </div>
  ),
  KnowledgeCreateDialog: ({ open }: { open: boolean }) =>
    open ? <div data-testid="knowledge-create-dialog">创建对话框</div> : null,
}));

import KnowledgeListPage from './index';

describe('KnowledgeListPage', () => {
  it('should render page title', () => {
    renderWithProviders(<KnowledgeListPage />);
    expect(screen.getByRole('heading', { level: 1, name: '知识库管理' })).toBeInTheDocument();
  });

  it('should render knowledge list component', () => {
    renderWithProviders(<KnowledgeListPage />);
    expect(screen.getByTestId('knowledge-list')).toBeInTheDocument();
  });
});
