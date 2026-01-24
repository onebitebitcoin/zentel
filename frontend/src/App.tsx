import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { GuestRoute } from './components/auth/GuestRoute';
import { Header } from './components/layout/Header';
import { BottomNav } from './components/layout/BottomNav';
import { Sidebar } from './components/layout/Sidebar';
import { QuickCapture } from './pages/QuickCapture';
import { Inbox } from './pages/Inbox';
import { MemoEdit } from './pages/MemoEdit';
import { Settings } from './pages/Settings';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-full bg-gray-50 overflow-x-hidden">
      {/* PC: 사이드바 */}
      <Sidebar className="hidden md:flex" />

      {/* 메인 컨텐츠 영역 */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* 모바일: 헤더 */}
        <Header className="md:hidden" />

        <main className="flex-1 overflow-hidden">{children}</main>

        {/* 모바일: 하단 네비게이션 */}
        <BottomNav className="md:hidden" />
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* 게스트 전용 라우트 (로그인 시 홈으로 리다이렉트) */}
          <Route
            path="/login"
            element={
              <GuestRoute>
                <Login />
              </GuestRoute>
            }
          />
          <Route
            path="/register"
            element={
              <GuestRoute>
                <Register />
              </GuestRoute>
            }
          />

          {/* 보호된 라우트 */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <QuickCapture />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/inbox"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Inbox />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/memo/:id"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <MemoEdit />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Settings />
                </AppLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
        <Toaster
          position="top-center"
          toastOptions={{
            duration: 2000,
            style: {
              background: '#333',
              color: '#fff',
              borderRadius: '12px',
            },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
