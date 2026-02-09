import { screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { renderWithProviders } from '../../../../tests/utils';

import AgentListPage from './index';

describe('AgentListPage', () => {
  it('should render page title', () => {
    renderWithProviders(<AgentListPage />);
    expect(screen.getByRole('heading', { level: 1, name: 'Agent 管理' })).toBeInTheDocument();
  });
});
