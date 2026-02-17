import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';

import { Sidebar } from './Sidebar';

function renderSidebar(props: { isOpen?: boolean; onClose?: () => void } = {}, initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Sidebar {...props} />
    </MemoryRouter>,
  );
}

describe('Sidebar', () => {
  it('应该渲染侧边栏导航', () => {
    renderSidebar();
    expect(screen.getByLabelText('主导航')).toBeInTheDocument();
  });

  it('应该渲染所有导航分组标题', () => {
    renderSidebar();
    expect(screen.getByText('概览')).toBeInTheDocument();
    expect(screen.getByText('Agent 管理')).toBeInTheDocument();
    expect(screen.getByText('工具与知识')).toBeInTheDocument();
    expect(screen.getByText('分析')).toBeInTheDocument();
  });

  it('应该渲染所有导航链接', () => {
    renderSidebar();
    expect(screen.getByText('仪表盘')).toBeInTheDocument();
    expect(screen.getByText('Agent 列表')).toBeInTheDocument();
    expect(screen.getByText('对话')).toBeInTheDocument();
    expect(screen.getByText('团队执行')).toBeInTheDocument();
    expect(screen.getByText('知识库')).toBeInTheDocument();
    expect(screen.getByText('模板')).toBeInTheDocument();
    expect(screen.getByText('工具目录')).toBeInTheDocument();
    expect(screen.getByText('使用洞察')).toBeInTheDocument();
    expect(screen.getByText('评估')).toBeInTheDocument();
  });

  it('应该高亮当前活跃的导航项', () => {
    renderSidebar({}, '/agents');
    const agentLink = screen.getByText('Agent 列表').closest('a');
    expect(agentLink).toHaveAttribute('aria-current', 'page');
  });

  it('应该不高亮非活跃的导航项', () => {
    renderSidebar({}, '/agents');
    const dashboardLink = screen.getByText('仪表盘').closest('a');
    expect(dashboardLink).not.toHaveAttribute('aria-current');
  });

  it('应该在点击导航项时调用 onClose', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderSidebar({ onClose });
    await user.click(screen.getByText('Agent 列表'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('应该在 isOpen 为 false 时应用隐藏样式', () => {
    renderSidebar({ isOpen: false });
    const aside = screen.getByLabelText('主导航');
    expect(aside).toHaveClass('-translate-x-full');
  });

  it('应该在 isOpen 为 true 时应用显示样式', () => {
    renderSidebar({ isOpen: true });
    const aside = screen.getByLabelText('主导航');
    expect(aside).toHaveClass('translate-x-0');
  });
});
