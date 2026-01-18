import { useLocation, useNavigate } from 'react-router-dom';
import {
  Sprout,
  FileEdit,
  BookOpen,
  Settings,
  Trash2,
  Plus,
  Hash,
} from 'lucide-react';
import { MEMO_TYPES } from '../../types/memo';

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
      path: '#',
      label: 'Fertilizer (External)',
      icon: <Sprout size={18} />,
      disabled: true,
    },
    {
      path: '/inbox',
      label: 'Temporary Note',
      icon: <FileEdit size={18} />,
    },
    {
      path: '#',
      label: 'Permanent Note',
      icon: <BookOpen size={18} />,
      disabled: true,
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
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
            <div className="w-5 h-5 text-primary">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
              </svg>
            </div>
          </div>
          <div>
            <div className="font-semibold text-gray-800">Zentel</div>
            <div className="text-xs text-gray-400 tracking-wider">
              ZETTELKASTEN
            </div>
          </div>
        </div>
      </div>

      {/* LIFECYCLE Section */}
      <div className="px-4 py-3">
        <div className="text-xs font-medium text-gray-400 tracking-wider px-2 mb-2">
          LIFECYCLE
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

      {/* TAGS Section */}
      <div className="px-4 py-3">
        <div className="flex items-center justify-between px-2 mb-2">
          <span className="text-xs font-medium text-gray-400 tracking-wider">
            TAGS
          </span>
          <button className="text-gray-300 hover:text-gray-400">
            <Plus size={14} />
          </button>
        </div>
        <div className="flex flex-wrap gap-2 px-2">
          {MEMO_TYPES.slice(0, 3).map((type) => (
            <span
              key={type.type}
              className="inline-flex items-center gap-1 px-2 py-1 bg-gray-50 text-gray-500 rounded-md text-xs"
            >
              <Hash size={12} />
              {type.label.toLowerCase().replace(/\s+/g, '-')}
            </span>
          ))}
        </div>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Settings & Trash */}
      <div className="px-4 py-3 space-y-1">
        <button
          disabled
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-300 cursor-not-allowed"
        >
          <Settings size={18} />
          Settings
        </button>
        <button
          disabled
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-300 cursor-not-allowed"
        >
          <Trash2 size={18} />
          Trash
        </button>
      </div>

      {/* CTA Button */}
      <div className="px-4 py-4">
        <button
          onClick={() => navigate('/')}
          className="w-full flex items-center justify-center gap-2 py-3 bg-primary hover:bg-primary-600 text-white rounded-lg font-medium transition-colors"
        >
          <Plus size={18} />
          New Temporary Note
        </button>
      </div>
    </aside>
  );
}
