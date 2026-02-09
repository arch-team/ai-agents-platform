// 认证后的应用主布局: Header + Sidebar + 内容区
import { useState } from 'react';
import { Outlet } from 'react-router-dom';

import { Header } from '@/widgets/header';
import { Sidebar } from '@/widgets/sidebar';

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleToggleSidebar = () => {
    setSidebarOpen((prev) => !prev);
  };

  const handleCloseSidebar = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="flex h-screen flex-col">
      <Header onToggleSidebar={handleToggleSidebar} />
      <div className="flex min-h-0 flex-1">
        <Sidebar isOpen={sidebarOpen} onClose={handleCloseSidebar} />
        <main id="main-content" className="flex-1 overflow-y-auto bg-gray-50" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
