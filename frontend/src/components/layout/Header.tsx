import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import rottenIcon from '../../assets/images/rotten.png';

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
          <div className="flex items-center gap-2">
            <img src={rottenIcon} alt="Rotten Apple 로고" className="w-8 h-8" />
            <div className="text-lg font-bold leading-none">
              <span className="text-green-900">Rotten</span>{' '}
              <span className="text-red-900">Apple</span>
            </div>
          </div>
        )}

        {isInbox && (
          <h1 className="absolute left-1/2 transform -translate-x-1/2 text-base font-medium text-gray-700">
            <span className="inline-flex items-center gap-2">
              <img src={rottenIcon} alt="임시 메모 목록" className="w-6 h-6" />
              임시 메모 목록
            </span>
          </h1>
        )}

        <div className="w-8" />
      </div>
    </header>
  );
}
