import { useEffect, useRef, useCallback } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

interface AnalysisEvent {
  memo_id: string;
  status: string;
}

/**
 * AI 분석 완료 SSE 이벤트를 수신하는 훅
 */
export function useAnalysisSSE(
  onAnalysisComplete: (memoId: string, status: string) => void
) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const onAnalysisCompleteRef = useRef(onAnalysisComplete);

  // 콜백 참조 업데이트
  useEffect(() => {
    onAnalysisCompleteRef.current = onAnalysisComplete;
  }, [onAnalysisComplete]);

  const connect = useCallback(() => {
    // 이미 연결되어 있으면 무시
    if (eventSourceRef.current) {
      return;
    }

    const eventSource = new EventSource(`${API_BASE_URL}/temp-memos/analysis-events`);
    eventSourceRef.current = eventSource;

    eventSource.addEventListener('analysis_complete', (event) => {
      try {
        const data: AnalysisEvent = JSON.parse(event.data);
        console.log('[SSE] Analysis complete:', data);
        onAnalysisCompleteRef.current(data.memo_id, data.status);
      } catch (error) {
        console.error('[SSE] Failed to parse event:', error);
      }
    });

    eventSource.addEventListener('ping', () => {
      // keepalive ping - 무시
    });

    eventSource.onerror = (error) => {
      console.error('[SSE] Connection error:', error);
      eventSource.close();
      eventSourceRef.current = null;

      // 3초 후 재연결 시도
      setTimeout(() => {
        console.log('[SSE] Attempting to reconnect...');
        connect();
      }, 3000);
    };

    eventSource.onopen = () => {
      console.log('[SSE] Connected to analysis events');
    };
  }, []);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      console.log('[SSE] Disconnected');
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return { connect, disconnect };
}
