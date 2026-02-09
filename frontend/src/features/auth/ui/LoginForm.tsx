// 登录表单 — React Hook Form + Zod + 完整无障碍

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';

import { Button, Input, ErrorMessage } from '@/shared/ui';

import { useLogin } from '../api/queries';
import { loginSchema } from '../lib/validation';

import type { LoginFormData } from '../lib/validation';

export function LoginForm() {
  const navigate = useNavigate();
  const loginMutation = useLogin();
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const handleFormSubmit = (data: LoginFormData) => {
    setApiError(null);
    loginMutation.mutate(data, {
      onSuccess: () => {
        navigate('/');
      },
      onError: (error) => {
        if (error && typeof error === 'object' && 'response' in error) {
          const axiosError = error as { response?: { data?: { message?: string } } };
          setApiError(axiosError.response?.data?.message || '登录失败，请重试');
        } else {
          setApiError('登录失败，请重试');
        }
      },
    });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} noValidate className="space-y-4">
      {apiError && <ErrorMessage error={apiError} />}

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
