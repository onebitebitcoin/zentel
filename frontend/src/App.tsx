import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Header } from './components/layout/Header';
import { BottomNav } from './components/layout/BottomNav';
import { QuickCapture } from './pages/QuickCapture';
import { Inbox } from './pages/Inbox';

function App() {
  return (
    <BrowserRouter>
      <div className="flex flex-col h-full bg-gray-50">
        <Header />
        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<QuickCapture />} />
            <Route path="/inbox" element={<Inbox />} />
          </Routes>
        </main>
        <BottomNav />
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
