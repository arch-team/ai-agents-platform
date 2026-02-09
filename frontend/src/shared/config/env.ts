export const env = {
  VITE_API_BASE_URL: (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000',
} as const;
