// 应用侧边导航栏 — 分组导航，覆盖全部页面入口
import { Link, useLocation } from 'react-router-dom';

import { cn } from '@/shared/lib/cn';
import {
  HomeIcon,
  AgentIcon,
  ChatIcon,
  TeamIcon,
  BookOpenIcon,
  LayoutIcon,
  WrenchIcon,
  BarChartIcon,
  ClipboardCheckIcon,
  BuilderIcon,
  SettingsIcon,
  DollarIcon,
  type IconProps,
} from '@/shared/ui';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

interface NavItem {
  label: string;
  path: string;
  // 存储组件引用而非 JSX 实例，避免每次渲染创建新对象
  Icon: React.ComponentType<IconProps>;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

// 导航分组配置 — Icon 字段存储组件引用，渲染时再实例化
const navGroups: NavGroup[] = [
  {
    title: '概览',
    items: [
      {
        label: '仪表盘',
        path: '/',
        Icon: HomeIcon,
      },
    ],
  },
  {
    title: 'Agent 管理',
    items: [
      {
        label: 'Agent 列表',
        path: '/agents',
        Icon: AgentIcon,
      },
      {
        label: 'Agent 构建器',
        path: '/builder',
        Icon: BuilderIcon,
      },
      {
        label: '对话',
        path: '/chat',
        Icon: ChatIcon,
      },
      {
        label: '团队执行',
        path: '/team-executions',
        Icon: TeamIcon,
      },
    ],
  },
  {
    title: '工具与知识',
    items: [
      {
        label: '知识库',
        path: '/knowledge',
        Icon: BookOpenIcon,
      },
      {
        label: '模板',
        path: '/templates',
        Icon: LayoutIcon,
      },
      {
        label: '工具目录',
        path: '/tools',
        Icon: WrenchIcon,
      },
    ],
  },
  {
    title: '分析',
    items: [
      {
        label: '使用洞察',
        path: '/insights',
        Icon: BarChartIcon,
      },
      {
        label: '评估',
        path: '/evaluation',
        Icon: ClipboardCheckIcon,
      },
    ],
  },
  {
    title: '系统管理',
    items: [
      {
        label: '费用管理',
        path: '/billing',
        Icon: DollarIcon,
      },
      {
        label: '系统设置',
        path: '/admin',
        Icon: SettingsIcon,
      },
    ],
  },
];

export function Sidebar({ isOpen = true, onClose }: SidebarProps) {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <>
      {/* 移动端遮罩 */}
      {isOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* 侧边栏 */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-20 mt-14 w-56 border-r border-gray-200 bg-white transition-transform lg:static lg:mt-0 lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        )}
        aria-label="主导航"
      >
        <nav className="flex flex-col gap-1 p-3">
          {navGroups.map((group) => (
            <div key={group.title} className="mb-2">
              {/* 分组标题 */}
              <h3 className="mb-1 px-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
                {group.title}
              </h3>
              {/* 分组导航项 */}
              {group.items.map((item) => {
                const active = isActive(item.path);
                const Icon = item.Icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={onClose}
                    aria-current={active ? 'page' : undefined}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      'hover:bg-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
                      active ? 'bg-blue-50 text-blue-700' : 'text-gray-700',
                    )}
                  >
                    <Icon />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
      </aside>
    </>
  );
}
