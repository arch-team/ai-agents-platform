// SSO 认证 API 类型定义

export interface SsoInitRequest {
  /** 认证完成后的回跳 URL（可选） */
  return_url?: string;
}

export interface SsoInitResponse {
  /** 后端返回的 IdP 登录跳转 URL */
  redirect_url: string;
}
