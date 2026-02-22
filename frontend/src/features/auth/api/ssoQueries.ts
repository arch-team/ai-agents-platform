// SSO 认证相关 mutations

import { useMutation } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import type { SsoInitRequest, SsoInitResponse } from './ssoTypes';

/**
 * 发起 SSO 登录 mutation
 * 调用成功后，将页面重定向至 IdP 登录页
 */
export function useSsoInit() {
  return useMutation({
    mutationFn: async (payload: SsoInitRequest = {}) => {
      const { data } = await apiClient.post<SsoInitResponse>('/api/v1/auth/sso/init', payload);
      return data;
    },
    onSuccess: (data) => {
      // 跳转到 IdP 认证页
      window.location.href = data.redirect_url;
    },
  });
}
