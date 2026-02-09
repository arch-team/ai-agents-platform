// 注册表单 — React Hook Form + Zod + 完整无障碍

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';

import { Button, Input, ErrorMessage } from '@/shared/ui';

import { useRegister } from '../api/queries';
import { registerSchema } from '../lib/validation';

import type { RegisterFormData } from '../lib/validation';

export function RegisterForm() {
  const navigate = useNavigate();
  const registerMutation = useRegister();
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const handleFormSubmit = (data: RegisterFormData) => {
    setApiError(null);
    registerMutation.mutate(
      { name: data.name, email: data.email, password: data.password },
      {
        onSuccess: () => {
          navigate('/login');
        },
        onError: (error) => {
          if (error && typeof error === 'object' && 'response' in error) {
            const axiosError = error as { response?: { data?: { message?: string } } };
            setApiError(axiosError.response?.data?.message || '注册失败，请重试');
          } else {
            setApiError('注册失败，请重试');
          }
        },
      },
    );
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} noValidate className="space-y-4">
      {apiError && <ErrorMessage error={apiError} />}

      <Input
        label="姓名"
        type="text"
        autoComplete="name"
        placeholder="请输入姓名"
        error={errors.name?.message}
        {...register('name')}
      />

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
        autoComplete="new-password"
        placeholder="请输入密码"
        error={errors.password?.message}
        {...register('password')}
      />

      <Input
        label="确认密码"
        type="password"
        autoComplete="new-password"
        placeholder="请再次输入密码"
        error={errors.confirmPassword?.message}
        {...register('confirmPassword')}
      />

      <Button type="submit" loading={registerMutation.isPending} className="w-full">
        注册
      </Button>
    </form>
  );
}
