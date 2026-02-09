import { screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { renderWithProviders } from '../../../tests/utils';

import NotFoundPage from './index';

describe('NotFoundPage', () => {
  it('should render 404 heading', () => {
    renderWithProviders(<NotFoundPage />);
    expect(screen.getByText('404')).toBeInTheDocument();
  });

  it('should render return home link', () => {
    renderWithProviders(<NotFoundPage />);
    expect(screen.getByRole('button', { name: '返回首页' })).toBeInTheDocument();
  });
});
