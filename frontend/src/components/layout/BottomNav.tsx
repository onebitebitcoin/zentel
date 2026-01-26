import { useLocation, useNavigate } from 'react-router-dom';
import { PenLine, BookOpen, Package, Settings } from 'lucide-react';
import rottenIcon from '../../assets/images/rotten.png';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { path: '/', label: '작성', icon: <PenLine size={20} /> },
  {
    path: '/inbox',
    label: '임시 메모',
    icon: <img src={rottenIcon} alt="임시 메모" className="w-5 h-5" />,
  },
  { path: '#', label: '영구 메모', icon: <BookOpen size={20} /> },
  { path: '#', label: '결과물', icon: <Package size={20} /> },
  { path: '/settings', label: '설정', icon: <Settings size={20} /> },
];

interface BottomNavProps {
  className?: string;
}

export function BottomNav({ className = '' }: BottomNavProps) {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav className={`fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 safe-bottom ${className}`}>
      <div className="flex justify-around items-center h-16">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const isDisabled = item.path === '#';

          return (
            <button
              key={item.label}
              onClick={() => !isDisabled && navigate(item.path)}
              disabled={isDisabled}
              className={`flex flex-col items-center justify-center gap-1 min-w-[56px] py-2 ${
                isActive
                  ? 'text-primary'
                  : isDisabled
                    ? 'text-gray-300'
                    : 'text-gray-500'
              }`}
            >
              {item.icon}
              <span className="text-xs">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
