// 认证 API 请求/响应类型

import type { UserSummary } from '@/entities/user';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserSummary;
}
