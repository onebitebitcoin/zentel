import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

interface HeaderProps {
  className?: string;
}

export function Header({ className = '' }: HeaderProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const isInbox = location.pathname === '/inbox';

  return (
    <header className={`sticky top-0 z-10 bg-white border-b border-gray-100 ${className}`}>
      <div className="flex items-center justify-between px-4 h-14">
        {isInbox ? (
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-gray-600"
          >
            <ArrowLeft size={20} />
          </button>
        ) : (
          <div className="text-lg font-semibold text-gray-800">Zentel</div>
        )}

        <h1 className="absolute left-1/2 transform -translate-x-1/2 text-base font-medium text-gray-700">
          {isInbox ? '임시 메모 목록' : '새 메모 작성'}
        </h1>

        <div className="w-8" />
      </div>
    </header>
  );
}
