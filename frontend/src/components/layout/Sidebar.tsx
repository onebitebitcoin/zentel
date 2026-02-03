import { useLocation, useNavigate } from 'react-router-dom';
import {
  FileEdit,
  BookOpen,
  Settings,
  Trash2,
  Plus,
} from 'lucide-react';
import rottenIcon from '../../assets/images/rotten.png';

interface SidebarProps {
  className?: string;
}

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  count?: number;
  disabled?: boolean;
}

export function Sidebar({ className = '' }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();

  const lifecycleItems: NavItem[] = [
    {
      path: '/inbox',
      label: '임시 메모',
      icon: <FileEdit size={18} />,
    },
    {
      path: '/notes',
      label: '영구 메모',
      icon: <BookOpen size={18} />,
    },
  ];

  const handleNavClick = (item: NavItem) => {
    if (!item.disabled) {
      navigate(item.path);
    }
  };

  return (
    <aside
      className={`w-[280px] h-full bg-white border-r border-gray-100 flex flex-col ${className}`}
    >
      {/* Logo */}
      <div className="px-6 py-5">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-3 hover:opacity-80 transition-opacity"
        >
          <img src={rottenIcon} alt="Rotten Apple 로고" className="w-10 h-10" />
          <div className="text-left">
            <div className="font-bold">
              <span className="text-green-900">Rotten</span>{' '}
              <span className="text-red-900">Apple</span>
            </div>
            <div className="text-xs text-gray-400 tracking-wider">
              메모 시스템
            </div>
          </div>
        </button>
      </div>

      {/* 단계 섹션 */}
      <div className="px-4 py-3">
        <div className="text-xs font-medium text-gray-400 tracking-wider px-2 mb-2">
          단계
        </div>
        <nav className="space-y-1">
          {lifecycleItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.label}
                onClick={() => handleNavClick(item)}
                disabled={item.disabled}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-primary/10 text-primary font-medium'
                    : item.disabled
                      ? 'text-gray-300 cursor-not-allowed'
                      : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <span className="flex items-center gap-3">
                  {item.icon}
                  {item.label}
                </span>
                {item.count !== undefined && (
                  <span className="text-xs text-gray-400">{item.count}</span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* 설정 & 휴지통 */}
      <div className="px-4 py-3 space-y-1">
        <button
          onClick={() => navigate('/settings')}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
            location.pathname === '/settings'
              ? 'bg-primary/10 text-primary font-medium'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Settings size={18} />
          설정
        </button>
        <button
          disabled
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-300 cursor-not-allowed"
        >
          <Trash2 size={18} />
          휴지통
        </button>
      </div>

      {/* 새 메모 버튼 */}
      <div className="px-4 py-4">
        <button
          onClick={() => navigate('/')}
          className="w-full flex items-center justify-center gap-2 py-3 bg-primary hover:bg-primary-600 text-white rounded-lg font-medium transition-colors"
        >
          <Plus size={18} />
          새 메모 작성
        </button>
      </div>
    </aside>
  );
}
