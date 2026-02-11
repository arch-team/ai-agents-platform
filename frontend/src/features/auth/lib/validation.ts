// 认证表单 Zod 校验规则

import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('请输入有效的邮箱'),
  password: z.string().min(8, '密码至少 8 位'),
});

export const registerSchema = z
  .object({
    name: z.string().min(2, '姓名至少 2 个字符').max(50, '姓名最多 50 个字符'),
    email: z.string().email('请输入有效的邮箱'),
    password: z
      .string()
      .min(8, '密码至少 8 位')
      .regex(/[A-Z]/, '密码需要包含大写字母')
      .regex(/[a-z]/, '密码需要包含小写字母')
      .regex(/[0-9]/, '密码需要包含数字'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: '两次密码不一致',
    path: ['confirmPassword'],
  });

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
