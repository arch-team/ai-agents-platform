export interface User {
  id: number;
  email: string;
  name: string;
  role: 'admin' | 'developer' | 'viewer';
  created_at: string;
  updated_at: string;
}

/** API 响应中的用户摘要（不含时间戳字段） */
export type UserSummary = Pick<User, 'id' | 'email' | 'name' | 'role'>;
