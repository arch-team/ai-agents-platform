import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';

// mock features/auth 模块
vi.mock('@/features/auth', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 1, name: '测试用户', role: 'admin' as const },
  })),
  useLogout: vi.fn(() => vi.fn()),
}));

import { useAuth, useLogout } from '@/features/auth';

import { Header } from './Header';

function renderHeader(props: { onToggleSidebar?: () => void } = {}) {
  return render(
    <MemoryRouter>
      <Header {...props} />
    </MemoryRouter>,
  );
}

describe('Header', () => {
  it('应该渲染 header 元素', () => {
    renderHeader();
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });

  it('应该渲染平台名称链接', () => {
    renderHeader();
    expect(screen.getByText('AI Agents Platform')).toBeInTheDocument();
  });

  it('应该在有用户时显示用户信息', () => {
    renderHeader();
    expect(screen.getByText('测试用户')).toBeInTheDocument();
    expect(screen.getByText('admin')).toBeInTheDocument();
  });

  it('应该在无用户时不显示用户信息和登出按钮', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      isAuthenticated: false,
    } as unknown as ReturnType<typeof useAuth>);

    renderHeader();
    expect(screen.queryByText('登出')).not.toBeInTheDocument();
  });

  it('应该渲染登出按钮', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 1, name: '测试用户', role: 'admin' as const },
      isAuthenticated: true,
    } as unknown as ReturnType<typeof useAuth>);

    renderHeader();
    expect(screen.getByRole('button', { name: '登出' })).toBeInTheDocument();
  });

  it('应该在点击登出时调用 logout', async () => {
    const mockLogout = vi.fn();
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 1, name: '测试用户', role: 'admin' as const },
      isAuthenticated: true,
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(useLogout).mockReturnValue(mockLogout);

    const user = userEvent.setup();
    renderHeader();
    await user.click(screen.getByRole('button', { name: '登出' }));
    expect(mockLogout).toHaveBeenCalled();
  });

  it('应该渲染切换菜单按钮', () => {
    renderHeader();
    expect(screen.getByLabelText('切换菜单')).toBeInTheDocument();
  });

  it('应该在点击汉堡菜单时调用 onToggleSidebar', async () => {
    const onToggleSidebar = vi.fn();
    const user = userEvent.setup();
    renderHeader({ onToggleSidebar });
    await user.click(screen.getByLabelText('切换菜单'));
    expect(onToggleSidebar).toHaveBeenCalledTimes(1);
  });
});
