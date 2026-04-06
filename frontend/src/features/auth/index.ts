// features/auth 公开 API

// UI 组件
export { LoginForm } from './ui/LoginForm';
export { RegisterForm } from './ui/RegisterForm';
export { SsoLoginButton } from './ui/SsoLoginButton';

// Store hooks
export { useAuth, useAuthToken, useAuthHasHydrated, useAuthActions } from './model/store';

// API hooks
export { useLogin, useRegister, useCurrentUser, useLogout } from './api/queries';
export { useSsoInit } from './api/ssoQueries';

// 类型
export type { LoginRequest, RegisterRequest, LoginResponse } from './api/types';
export type { SsoInitRequest, SsoInitResponse } from './api/ssoTypes';
export type { AuthState } from './model/types';
