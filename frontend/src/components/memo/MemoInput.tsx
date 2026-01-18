import { useRef, useEffect } from 'react';

interface MemoInputProps {
  value: string;
  onChange: (value: string) => void;
  maxLength?: number;
}

export function MemoInput({ value, onChange, maxLength = 10000 }: MemoInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    // 자동 포커스
    textareaRef.current?.focus();
  }, []);

  return (
    <div className="relative">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="떠오른 생각을 바로 기록하세요..."
        maxLength={maxLength}
        className="w-full h-40 p-4 text-base text-gray-800 placeholder-gray-400 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
      />
      <div className="absolute bottom-3 right-3 text-xs text-gray-400">
        {value.length} / {maxLength}
      </div>
    </div>
  );
}
