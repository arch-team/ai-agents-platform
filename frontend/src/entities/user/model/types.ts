export interface User {
  id: number;
  email: string;
  name: string;
  role: 'admin' | 'developer' | 'viewer';
  created_at: string;
  updated_at: string;
}
