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

完整检查清单见 [checklist.md](checklist.md) §状态管理

---

## 1. React Query (服务端状态)

### 1.1 基本配置

```typescript
// app/providers/QueryProvider.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,  // 5 分钟
      gcTime: 1000 * 60 * 30,    // 30 分钟
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export function QueryProvider({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

### 1.2 Query Keys 规范

```typescript
// features/agents/api/queries.ts - Key Factory 模式
export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (filters: AgentFilters) => [...agentKeys.lists(), filters] as const,
  details: () => [...agentKeys.all, 'detail'] as const,
  detail: (id: string) => [...agentKeys.details(), id] as const,
};
```

### 1.3 Query/Mutation 模板

```typescript
// 列表查询
export function useAgents(filters?: AgentFilters) {
  return useQuery({
    queryKey: agentKeys.list(filters ?? {}),
    queryFn: async () => {
      const { data } = await apiClient.get<Agent[]>('/api/v1/agents', { params: filters });
      return data;
    },
  });
}

// Mutation + 缓存失效
export function useCreateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (dto: CreateAgentDTO) => apiClient.post<Agent>('/api/v1/agents', dto).then(r => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: agentKeys.lists() }),
  });
}

// 详情查询同理，关键点: enabled: !!id 防止空请求
// 更新/删除 mutation 关键点:
// - onSuccess: invalidateQueries 使列表失效
// - onSuccess: setQueryData 更新详情缓存
// - onSuccess: removeQueries 删除缓存
```

### 1.4 乐观更新模式

```
onMutate: cancelQueries → 保存旧数据 → setQueryData 乐观写入 → return { previous }
onError: 用 context.previous 回滚
onSettled: invalidateQueries 确保数据一致
```

---

## 2. Zustand (客户端状态)

### 2.1 Store 模板（带持久化）

```typescript
// features/auth/model/store.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ token: state.token }), // 只持久化 token
    }
  )
);
```

**不需要持久化时**: 去掉 `persist` 包装，直接 `create<State>()((set) => ({...}))`

### 2.2 Selector Hooks（性能关键）

```typescript
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

---

## 3. React Hook Form (表单状态)

```typescript
// features/auth/ui/LoginForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email('请输入有效的邮箱'),
  password: z.string().min(8, '密码至少 8 位'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => { /* 调用 mutation */ };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <span>{errors.email.message}</span>}
      <input type="password" {...register('password')} />
      {errors.password && <span>{errors.password.message}</span>}
      <button type="submit" disabled={isSubmitting}>登录</button>
    </form>
  );
}
```

---

## 4. 最佳实践

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
