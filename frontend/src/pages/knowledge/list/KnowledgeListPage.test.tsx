// 知识库列表页面 smoke test
import { screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { renderWithProviders } from '../../../../tests/utils';

// Mock feature 组件，避免 API 调用
vi.mock('@/features/knowledge', () => ({
  KnowledgeList: ({
    onSelect,
    onCreate,
  }: {
    onSelect: (id: string) => void;
    onCreate: () => void;
  }) => (
    <ul role="list" aria-label="知识库列表">
      <li>
        <button onClick={() => onSelect('1')}>选择</button>
        <button onClick={onCreate}>创建</button>
      </li>
    </ul>
  ),
  KnowledgeCreateDialog: ({ open }: { open: boolean }) =>
    open ? (
      <div role="dialog" aria-label="创建知识库">
        创建对话框
      </div>
    ) : null,
}));

import KnowledgeListPage from './index';

describe('KnowledgeListPage', () => {
  it('should render page title', () => {
    renderWithProviders(<KnowledgeListPage />);
    expect(screen.getByRole('heading', { level: 1, name: '知识库管理' })).toBeInTheDocument();
  });

  it('should render knowledge list component', () => {
    renderWithProviders(<KnowledgeListPage />);
    expect(screen.getByRole('list', { name: '知识库列表' })).toBeInTheDocument();
  });
});
