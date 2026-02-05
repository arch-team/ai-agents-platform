> **职责**: 状态管理规范 - React Query (服务端)、Zustand (客户端)、表单状态

# 状态管理规范 (State Management Standards)

---

## 0. 速查卡片

### 状态类型决策

| 数据类型 | 推荐方案 | 示例 |
|---------|---------|------|
| 服务端数据 | React Query | 用户列表、Agent 详情 |
| 全局 UI 状态 | Zustand | 主题、侧边栏展开状态 |
| 用户会话 | Zustand + persist | 登录状态、Token |
| 表单状态 | React Hook Form | 登录表单、配置表单 |
| 组件局部状态 | useState | 下拉菜单开关 |
| 复杂组件状态 | useReducer | 多步骤向导 |

### 决策流程图

```
数据来自 API？ ──是──► React Query (TanStack Query)
      │
     否
      ↓
需要跨组件共享？ ──是──► Zustand Store
      │                    ↓
     否              需要持久化？ ──是──► Zustand + persist
      ↓
组件状态复杂？ ──是──► useReducer
      │
     否
      ↓
useState
```

### 文件位置速查

| 状态类型 | 位置 |
|---------|------|
| Feature 相关 API | `features/{feature}/api/queries.ts` |
| Feature Store | `features/{feature}/model/store.ts` |
| 全局 Store | `shared/store/{store}.ts` |
| 实体类型 | `entities/{entity}/model/types.ts` |

### PR Review 检查清单

- [ ] 服务端数据使用 React Query
- [ ] 全局状态使用 Zustand
- [ ] Store 有 selector hooks 导出
- [ ] Query Keys 遵循命名规范
- [ ] 敏感数据不存入持久化 Store

---

## 1. React Query (服务端状态)

### 1.1 基本配置

```typescript
// app/providers/QueryProvider.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 分钟
      gcTime: 1000 * 60 * 30,   // 30 分钟 (原 cacheTime)
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export function QueryProvider({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### 1.2 Query Keys 规范

```typescript
// features/agents/api/queries.ts

// 定义 key factory
export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (filters: AgentFilters) => [...agentKeys.lists(), filters] as const,
  details: () => [...agentKeys.all, 'detail'] as const,
  detail: (id: string) => [...agentKeys.details(), id] as const,
};

// 使用示例
useQuery({ queryKey: agentKeys.detail(agentId) });
```

### 1.3 Query Hooks 模板

```typescript
// features/agents/api/queries.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/shared/api';
import type { Agent, CreateAgentDTO, UpdateAgentDTO } from '../model/types';

// 列表查询
export function useAgents(filters?: AgentFilters) {
  return useQuery({
    queryKey: agentKeys.list(filters ?? {}),
    queryFn: async () => {
      const { data } = await apiClient.get<Agent[]>('/api/v1/agents', {
        params: filters,
      });
      return data;
    },
  });
}

// 详情查询
export function useAgent(id: string) {
  return useQuery({
    queryKey: agentKeys.detail(id),
    queryFn: async () => {
      const { data } = await apiClient.get<Agent>(`/api/v1/agents/${id}`);
      return data;
    },
    enabled: !!id, // 仅当 id 存在时查询
  });
}

// 创建 mutation
export function useCreateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (dto: CreateAgentDTO) => {
      const { data } = await apiClient.post<Agent>('/api/v1/agents', dto);
      return data;
    },
    onSuccess: () => {
      // 使列表缓存失效
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
  });
}

// 更新 mutation
export function useUpdateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, dto }: { id: string; dto: UpdateAgentDTO }) => {
      const { data } = await apiClient.put<Agent>(`/api/v1/agents/${id}`, dto);
      return data;
    },
    onSuccess: (data) => {
      // 更新详情缓存
      queryClient.setQueryData(agentKeys.detail(data.id), data);
      // 使列表缓存失效
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
  });
}

// 删除 mutation
export function useDeleteAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/api/v1/agents/${id}`);
      return id;
    },
    onSuccess: (id) => {
      queryClient.removeQueries({ queryKey: agentKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
  });
}
```

### 1.4 乐观更新

```typescript
export function useUpdateAgentStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: AgentStatus }) => {
      const { data } = await apiClient.patch<Agent>(
        `/api/v1/agents/${id}/status`,
        { status }
      );
      return data;
    },
    onMutate: async ({ id, status }) => {
      // 取消正在进行的查询
      await queryClient.cancelQueries({ queryKey: agentKeys.detail(id) });

      // 保存旧数据
      const previousAgent = queryClient.getQueryData<Agent>(agentKeys.detail(id));

      // 乐观更新
      if (previousAgent) {
        queryClient.setQueryData(agentKeys.detail(id), {
          ...previousAgent,
          status,
        });
      }

      return { previousAgent };
    },
    onError: (err, { id }, context) => {
      // 回滚
      if (context?.previousAgent) {
        queryClient.setQueryData(agentKeys.detail(id), context.previousAgent);
      }
    },
    onSettled: (data, error, { id }) => {
      // 重新获取最新数据
      queryClient.invalidateQueries({ queryKey: agentKeys.detail(id) });
    },
  });
}
```

---

## 2. Zustand (客户端状态)

### 2.1 Store 模板

```typescript
// features/auth/model/store.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User } from '@/entities/user';

interface AuthState {
  // 状态
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;

  // 操作
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // 初始状态
      user: null,
      token: null,
      isAuthenticated: false,

      // 操作实现
      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
        }),

      setToken: (token) => set({ token }),

      logout: () =>
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        token: state.token,
        // 注意：不持久化敏感用户信息
      }),
    }
  )
);
```

### 2.2 Selector Hooks

```typescript
// features/auth/model/store.ts (续)

// 细粒度 selector - 避免不必要的重渲染
export const useAuth = () =>
  useAuthStore((state) => ({
    user: state.user,
    isAuthenticated: state.isAuthenticated,
  }));

export const useAuthToken = () => useAuthStore((state) => state.token);

export const useAuthActions = () =>
  useAuthStore((state) => ({
    setUser: state.setUser,
    setToken: state.setToken,
    logout: state.logout,
  }));
```

### 2.3 不带持久化的 Store

```typescript
// shared/store/ui.ts
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
}));

// Selector hooks
export const useSidebar = () => useUIStore((state) => ({
  isOpen: state.sidebarOpen,
  toggle: state.toggleSidebar,
}));

export const useTheme = () => useUIStore((state) => ({
  theme: state.theme,
  setTheme: state.setTheme,
}));
```

### 2.4 异步操作

```typescript
// features/auth/model/store.ts
import { apiClient } from '@/shared/api';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: false,
  error: null,

  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await apiClient.post('/api/v1/auth/login', credentials);
      set({
        user: data.user,
        token: data.token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '登录失败',
        isLoading: false,
      });
      throw error;
    }
  },

  fetchCurrentUser: async () => {
    const token = get().token;
    if (!token) return;

    set({ isLoading: true });
    try {
      const { data } = await apiClient.get('/api/v1/auth/me');
      set({ user: data, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
}));
```

---

## 3. React Hook Form (表单状态)

### 3.1 基本用法

```typescript
// features/auth/ui/LoginForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button, Input } from '@/shared/ui';
import { useLogin } from '../api/queries';

const loginSchema = z.object({
  email: z.string().email('请输入有效的邮箱'),
  password: z.string().min(8, '密码至少 8 位'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const login = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    await login.mutateAsync(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input
        label="邮箱"
        type="email"
        error={errors.email?.message}
        {...register('email')}
      />
      <Input
        label="密码"
        type="password"
        error={errors.password?.message}
        {...register('password')}
      />
      <Button type="submit" loading={isSubmitting}>
        登录
      </Button>
    </form>
  );
}
```

---

## 4. 状态管理最佳实践

### 4.1 避免过度使用全局状态

```typescript
// ❌ 错误 - 把所有东西都放全局
const useStore = create((set) => ({
  modalOpen: false,        // 应该是组件状态
  formData: {},            // 应该用 React Hook Form
  users: [],               // 应该用 React Query
}));

// ✅ 正确 - 只把真正需要全局共享的放 Zustand
const useUIStore = create((set) => ({
  sidebarOpen: true,       // 确实需要跨组件共享
  theme: 'light',          // 确实需要跨组件共享
}));
```

### 4.2 状态提升 vs 全局状态

```
需要跨组件共享？
    │
   否 ──────► useState (组件内)
    │
   是
    ↓
只在父子组件间？ ──是──► Props 传递 / Context
    │
   否
    ↓
Zustand Store
```

### 4.3 避免 Prop Drilling

```typescript
// ❌ 错误 - 层层传递 props
function App() {
  const [user, setUser] = useState(null);
  return <Layout user={user} setUser={setUser} />;
}

// ✅ 正确 - 使用 Zustand
function App() {
  return <Layout />;
}

function DeepChild() {
  const user = useAuthStore((s) => s.user);
  // 直接获取
}
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [architecture.md](architecture.md) | FSD 分层，Store 放置位置 |
| [component-design.md](component-design.md) | 组件中使用状态 |
| [testing.md](testing.md) | 状态相关测试 |
