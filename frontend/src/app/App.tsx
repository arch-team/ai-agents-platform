import { BrowserRouter } from 'react-router-dom';

import { ErrorBoundary } from '@/shared/ui';

import { QueryProvider, AuthProvider } from './providers';
import { AppRoutes } from './routes';

export function App() {
  return (
    <BrowserRouter>
      <QueryProvider>
        <AuthProvider>
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
        </AuthProvider>
      </QueryProvider>
    </BrowserRouter>
  );
}
