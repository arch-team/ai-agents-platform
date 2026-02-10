// 环境变量类型安全封装

function getEnvVar(key: string, fallback: string): string {
  const value = import.meta.env[key];
  return typeof value === 'string' && value.length > 0 ? value : fallback;
}

export const env = {
  VITE_API_BASE_URL: getEnvVar('VITE_API_BASE_URL', 'http://localhost:8000'),
} as const;
