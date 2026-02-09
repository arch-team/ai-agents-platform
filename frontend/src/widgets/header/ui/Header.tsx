// 应用顶部导航栏
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useAuth, useLogout } from '@/features/auth';
import { cn } from '@/shared/lib/cn';
import { Button } from '@/shared/ui';

interface HeaderProps {
  onToggleSidebar?: () => void;
}

export function Header({ onToggleSidebar }: HeaderProps) {
  const { user } = useAuth();
  const logout = useLogout();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    setIsMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-30 border-b border-gray-200 bg-white">
      <div className="flex h-14 items-center justify-between px-4">
        {/* 左侧: 汉堡菜单 + Logo */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 lg:hidden"
            aria-label="切换菜单"
            onClick={() => {
              onToggleSidebar?.();
              setIsMobileMenuOpen(!isMobileMenuOpen);
            }}
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white">
              AI
            </div>
            <span className="hidden text-lg font-semibold text-gray-900 sm:inline">
              AI Agents Platform
            </span>
          </Link>
        </div>

        {/* 右侧: 用户信息 + 登出 */}
        <div className="flex items-center gap-3">
          {user && (
            <>
              <div className="hidden items-center gap-2 sm:flex">
                <span className="text-sm font-medium text-gray-700">{user.name}</span>
                <span
                  className={cn(
                    'rounded-full px-2 py-0.5 text-xs font-medium',
                    user.role === 'admin'
                      ? 'bg-purple-100 text-purple-700'
                      : user.role === 'developer'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-100 text-gray-700',
                  )}
                >
                  {user.role}
                </span>
              </div>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                登出
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
