/**
 * 하이라이트된 텍스트 렌더링 컴포넌트
 */
import { Fragment } from 'react';
import type { HighlightItem } from '../../types/memo';

interface HighlightedTextProps {
  text: string;
  highlights: HighlightItem[] | null;
}

export function HighlightedText({ text, highlights }: HighlightedTextProps) {
  // 하이라이트가 없으면 텍스트만 반환
  if (!highlights || highlights.length === 0) {
    return <span>{text}</span>;
  }

  // 유효한 위치가 있는 하이라이트만 필터링
  const validHighlights = highlights.filter((h) => h.start >= 0 && h.end >= 0);

  // 유효한 하이라이트가 없으면 텍스트만 반환
  if (validHighlights.length === 0) {
    return <span>{text}</span>;
  }

  // 하이라이트 위치 정렬
  const sortedHighlights = [...validHighlights].sort((a, b) => a.start - b.start);
  const elements: React.ReactNode[] = [];
  let lastEnd = 0;

  sortedHighlights.forEach((highlight, idx) => {
    // 하이라이트 이전 텍스트
    if (highlight.start > lastEnd) {
      elements.push(
        <span key={`text-${idx}`}>{text.slice(lastEnd, highlight.start)}</span>
      );
    }

    // 하이라이트된 텍스트
    elements.push(
      <span
        key={`highlight-${idx}`}
        className="bg-yellow-200"
      >
        {text.slice(highlight.start, highlight.end)}
      </span>
    );

    lastEnd = highlight.end;
  });

  // 마지막 하이라이트 이후 텍스트
  if (lastEnd < text.length) {
    elements.push(
      <span key="text-last">{text.slice(lastEnd)}</span>
    );
  }

  return <Fragment>{elements}</Fragment>;
}
