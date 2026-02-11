// 登录表单 — React Hook Form + Zod + 完整无障碍

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';

import { Button, Input, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useLogin } from '../api/queries';
import { loginSchema } from '../lib/validation';

import type { LoginFormData } from '../lib/validation';

export function LoginForm() {
  const navigate = useNavigate();
  const loginMutation = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const handleFormSubmit = async (data: LoginFormData) => {
    try {
      await loginMutation.mutateAsync(data);
      navigate('/');
    } catch {
      // 错误由 loginMutation.isError 处理，UI 中展示
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} noValidate className="space-y-4">
      {loginMutation.isError && (
        <ErrorMessage error={extractApiError(loginMutation.error, '登录失败，请重试')} />
      )}

      <Input
        label="邮箱"
        type="email"
        autoComplete="email"
        placeholder="请输入邮箱"
        error={errors.email?.message}
        {...register('email')}
      />

      <Input
        label="密码"
        type="password"
        autoComplete="current-password"
        placeholder="请输入密码"
        error={errors.password?.message}
        {...register('password')}
      />

      <Button type="submit" loading={loginMutation.isPending} className="w-full">
        登录
      </Button>
    </form>
  );
}
