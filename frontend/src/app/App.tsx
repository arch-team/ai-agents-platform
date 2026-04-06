import { useCallback } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { useBuilderActions } from '@/features/builder';
import { ErrorBoundary } from '@/shared/ui';

import { QueryProvider, AuthProvider } from './providers';
import { AppRoutes } from './routes';

function AppContent() {
  const { reset } = useBuilderActions();
  const handleErrorReset = useCallback(() => {
    reset();
  }, [reset]);

  return (
    <ErrorBoundary onReset={handleErrorReset}>
      <AppRoutes />
    </ErrorBoundary>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <QueryProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </QueryProvider>
    </BrowserRouter>
  );
}
