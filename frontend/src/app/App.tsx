import { BrowserRouter } from 'react-router-dom';

import { QueryProvider, AuthProvider } from './providers';
import { AppRoutes } from './routes';

export function App() {
  return (
    <BrowserRouter>
      <QueryProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </QueryProvider>
    </BrowserRouter>
  );
}
