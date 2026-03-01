// 环境变量类型安全封装

function getEnvVar(key: string, fallback: string): string {
  const value = import.meta.env[key];
  return typeof value === 'string' && value.length > 0 ? value : fallback;
}

export const env = {
  // 默认空字符串 = 相对路径（CloudFront 同源代理 /api/*）
  // 本地开发时通过 .env 设置 VITE_API_BASE_URL=http://localhost:8000
  VITE_API_BASE_URL: getEnvVar('VITE_API_BASE_URL', ''),
} as const;
