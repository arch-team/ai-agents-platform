import { Link } from 'react-router-dom';

import { Card } from '@/shared/ui';
import { LoginForm } from '@/features/auth';

// 登录页面
export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <h1 className="mb-6 text-center text-2xl font-bold text-gray-900">登录</h1>
        <LoginForm />
        <p className="mt-4 text-center text-sm text-gray-500">
          还没有账号？{' '}
          <Link to="/register" className="text-blue-600 hover:text-blue-700">
            立即注册
          </Link>
        </p>
      </Card>
    </main>
  );
}
