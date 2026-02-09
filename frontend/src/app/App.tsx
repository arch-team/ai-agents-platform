import { QueryProvider, AuthProvider } from './providers';
import { AppRoutes } from './routes';

export function App() {
  return (
    <QueryProvider>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </QueryProvider>
  );
}
