// 404 页面
import { Link } from 'react-router-dom';

import { Button } from '@/shared/ui';

export default function NotFoundPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <h1 className="text-6xl font-bold text-gray-300">404</h1>
      <p className="mt-4 text-lg text-gray-600">页面未找到</p>
      <p className="mt-2 text-sm text-gray-400">你访问的页面不存在或已被移除</p>
      <Link to="/" className="mt-6">
        <Button>返回首页</Button>
      </Link>
    </main>
  );
}
