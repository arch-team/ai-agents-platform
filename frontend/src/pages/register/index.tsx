import { Link } from 'react-router-dom';

import { Card } from '@/shared/ui';
import { RegisterForm } from '@/features/auth';

// 注册页面
export default function RegisterPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <h1 className="mb-6 text-center text-2xl font-bold text-gray-900">注册</h1>
        <RegisterForm />
        <p className="mt-4 text-center text-sm text-gray-500">
          已有账号？{' '}
          <Link to="/login" className="text-blue-600 hover:text-blue-700">
            立即登录
          </Link>
        </p>
      </Card>
    </main>
  );
}
