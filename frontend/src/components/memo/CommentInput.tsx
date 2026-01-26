/**
 * 댓글 입력 컴포넌트 (페르소나 자동완성 포함)
 */
import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import type { AIPersona } from '../../types/auth';

interface CommentInputProps {
  personas: AIPersona[];
  submitting: boolean;
  onSubmit: (content: string) => Promise<void>;
}

export function CommentInput({ personas, submitting, onSubmit }: CommentInputProps) {
  const [content, setContent] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [filter, setFilter] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredPersonas = personas.filter((p) =>
    p.name.toLowerCase().includes(filter.toLowerCase())
  );

  const handleChange = (value: string) => {
    setContent(value);

    // @ 입력 감지
    const lastAtIndex = value.lastIndexOf('@');
    if (lastAtIndex !== -1 && personas.length > 0) {
      const afterAt = value.slice(lastAtIndex + 1);
      if (!afterAt.includes(' ')) {
        setFilter(afterAt);
        setShowDropdown(true);
        setSelectedIndex(0);
        return;
      }
    }
    setShowDropdown(false);
  };

  const handleSelectPersona = (personaName: string) => {
    const lastAtIndex = content.lastIndexOf('@');
    if (lastAtIndex !== -1) {
      const before = content.slice(0, lastAtIndex);
      setContent(`${before}@${personaName} `);
    }
    setShowDropdown(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (showDropdown && filteredPersonas.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredPersonas.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : filteredPersonas.length - 1
        );
      } else if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        handleSelectPersona(filteredPersonas[selectedIndex].name);
      } else if (e.key === 'Escape') {
        setShowDropdown(false);
      }
    } else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = async () => {
    if (!content.trim() || submitting) return;
    await onSubmit(content.trim());
    setContent('');
  };

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative flex gap-2">
      <div className="relative flex-1">
        <input
          ref={inputRef}
          type="text"
          value={content}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={personas.length > 0 ? "@페르소나로 AI 호출..." : "의견을 남겨보세요..."}
          className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary"
        />

        {/* 페르소나 자동완성 드롭다운 */}
        {showDropdown && filteredPersonas.length > 0 && (
          <div
            ref={dropdownRef}
            className="absolute left-0 right-0 bottom-full mb-1 bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden z-10"
          >
            {filteredPersonas.map((persona, index) => (
              <button
                key={persona.name}
                onClick={() => handleSelectPersona(persona.name)}
                className={`w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-gray-50 ${
                  index === selectedIndex ? 'bg-gray-100' : ''
                }`}
              >
                <div
                  className="w-5 h-5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: persona.color || '#6366F1' }}
                />
                <div className="flex-1 min-w-0">
                  <span
                    className="text-sm font-medium"
                    style={{ color: persona.color || '#6366F1' }}
                  >
                    @{persona.name}
                  </span>
                  {persona.description && (
                    <p className="text-xs text-gray-400 truncate">
                      {persona.description}
                    </p>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
      <button
        onClick={handleSubmit}
        disabled={!content.trim() || submitting}
        className="px-3 py-2 text-white bg-primary rounded-lg hover:bg-primary-600 disabled:opacity-50"
      >
        <Send size={16} />
      </button>
    </div>
  );
}
