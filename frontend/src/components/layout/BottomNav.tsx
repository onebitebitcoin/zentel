import { useLocation, useNavigate } from 'react-router-dom';
import { PenLine, List, BookOpen, BarChart3 } from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { path: '/', label: 'WRITE', icon: <PenLine size={20} /> },
  { path: '/inbox', label: 'PERMANENT', icon: <BookOpen size={20} /> },
  { path: '#', label: 'OUTPUT', icon: <List size={20} /> },
  { path: '#', label: 'STATS', icon: <BarChart3 size={20} /> },
];

export function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 safe-bottom">
      <div className="flex justify-around items-center h-16">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const isDisabled = item.path === '#';

          return (
            <button
              key={item.label}
              onClick={() => !isDisabled && navigate(item.path)}
              disabled={isDisabled}
              className={`flex flex-col items-center justify-center gap-1 min-w-[64px] py-2 ${
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
