import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';

// mock Header 和 Sidebar 以隔离 AppLayout 测试
vi.mock('@/widgets/header', () => ({
  Header: ({ onToggleSidebar }: { onToggleSidebar?: () => void }) => (
    <header data-testid="mock-header">
      <button onClick={onToggleSidebar}>切换菜单</button>
    </header>
  ),
}));

vi.mock('@/widgets/sidebar', () => ({
  Sidebar: ({ isOpen, onClose }: { isOpen?: boolean; onClose?: () => void }) => (
    <aside data-testid="mock-sidebar" data-is-open={isOpen}>
      <button onClick={onClose}>关闭</button>
    </aside>
  ),
}));

import { AppLayout } from './AppLayout';

function renderAppLayout() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<div>页面内容</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe('AppLayout', () => {
  it('应该渲染 Header', () => {
    renderAppLayout();
    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
  });

  it('应该渲染 Sidebar', () => {
    renderAppLayout();
    expect(screen.getByTestId('mock-sidebar')).toBeInTheDocument();
  });

  it('应该渲染 Outlet 内容', () => {
    renderAppLayout();
    expect(screen.getByText('页面内容')).toBeInTheDocument();
  });

  it('应该渲染 main 内容区域', () => {
    renderAppLayout();
    const main = screen.getByRole('main');
    expect(main).toHaveAttribute('id', 'main-content');
  });

  it('应该在点击切换菜单后更新 sidebar 状态', async () => {
    const user = userEvent.setup();
    renderAppLayout();

    // 初始状态: sidebar 关闭 (isOpen = false)
    expect(screen.getByTestId('mock-sidebar')).toHaveAttribute('data-is-open', 'false');

    // 点击切换
    await user.click(screen.getByText('切换菜单'));
    expect(screen.getByTestId('mock-sidebar')).toHaveAttribute('data-is-open', 'true');
  });

  it('应该在 sidebar 关闭后恢复状态', async () => {
    const user = userEvent.setup();
    renderAppLayout();

    // 打开 sidebar
    await user.click(screen.getByText('切换菜单'));
    expect(screen.getByTestId('mock-sidebar')).toHaveAttribute('data-is-open', 'true');

    // 关闭 sidebar
    await user.click(screen.getByText('关闭'));
    expect(screen.getByTestId('mock-sidebar')).toHaveAttribute('data-is-open', 'false');
  });
});
