// 工具目录列表页面 smoke test
import { screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { renderWithProviders } from '../../../../tests/utils';

// Mock feature 组件，避免 API 调用
vi.mock('@/features/tool-catalog', () => ({
  ToolList: ({ onSelect }: { onSelect: (id: string) => void }) => (
    <div data-testid="tool-list">
      <button onClick={() => onSelect('1')}>选择</button>
    </div>
  ),
}));

import ToolListPage from './index';

describe('ToolListPage', () => {
  it('should render page title', () => {
    renderWithProviders(<ToolListPage />);
    expect(screen.getByRole('heading', { level: 1, name: '工具目录' })).toBeInTheDocument();
  });

  it('should render tool list component', () => {
    renderWithProviders(<ToolListPage />);
    expect(screen.getByTestId('tool-list')).toBeInTheDocument();
  });
});
