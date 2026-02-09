import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { renderWithProviders } from '../../../tests/utils';

import ChatPage from './index';

describe('ChatPage', () => {
  it('should render empty state when no conversation selected', () => {
    renderWithProviders(<ChatPage />);
    expect(screen.getByText('请选择一个对话')).toBeInTheDocument();
  });

  it('should render conversation list', async () => {
    renderWithProviders(<ChatPage />);
    // 对话列表 aside 应该存在
    await waitFor(() => {
      expect(screen.getByRole('complementary', { name: '对话列表' })).toBeInTheDocument();
    });
  });
});
