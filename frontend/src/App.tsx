import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Header } from './components/layout/Header';
import { BottomNav } from './components/layout/BottomNav';
import { Sidebar } from './components/layout/Sidebar';
import { QuickCapture } from './pages/QuickCapture';
import { Inbox } from './pages/Inbox';

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-full bg-gray-50">
        {/* PC: 사이드바 */}
        <Sidebar className="hidden md:flex" />

        {/* 메인 컨텐츠 영역 */}
        <div className="flex flex-col flex-1 min-w-0">
          {/* 모바일: 헤더 */}
          <Header className="md:hidden" />

          <main className="flex-1 overflow-hidden">
            <Routes>
              <Route path="/" element={<QuickCapture />} />
              <Route path="/inbox" element={<Inbox />} />
            </Routes>
          </main>

          {/* 모바일: 하단 네비게이션 */}
          <BottomNav className="md:hidden" />
        </div>
      </div>
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
    </BrowserRouter>
  );
}

export default App;
