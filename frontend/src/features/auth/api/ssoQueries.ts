// SSO 认证相关 mutations

import { useMutation } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';
import { isValidRedirectUrl } from '@/shared/lib/isValidRedirectUrl';

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
      // 白名单验证 — 防止开放重定向攻击
      if (!isValidRedirectUrl(data.redirect_url)) {
        throw new Error('SSO 返回了不可信的重定向地址');
      }
      window.location.href = data.redirect_url;
    },
  });
}
