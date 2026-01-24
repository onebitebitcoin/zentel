import { useEffect, useRef, useCallback, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

interface AnalysisCompleteEvent {
  memo_id: string;
  status: string;
  error?: string;
}

export interface CommentAIResponseEvent {
  memo_id: string;
  comment_id: string;
  parent_comment_id: string;
  status: 'completed' | 'failed';
  error?: string;
}

export interface AnalysisProgressEvent {
  memo_id: string;
  step: string;
  message: string;
  detail?: string;
  timestamp?: string;
}

export interface AnalysisLogs {
  [memoId: string]: AnalysisProgressEvent[];
}

/**
 * AI 분석 완료 SSE 이벤트를 수신하는 훅
 */
export function useAnalysisSSE(
  onAnalysisComplete: (memoId: string, status: string) => void,
  onCommentAIResponse?: (event: CommentAIResponseEvent) => void
) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const onAnalysisCompleteRef = useRef(onAnalysisComplete);
  const onCommentAIResponseRef = useRef(onCommentAIResponse);
  const [analysisLogs, setAnalysisLogs] = useState<AnalysisLogs>({});

  // 콜백 참조 업데이트
  useEffect(() => {
    onAnalysisCompleteRef.current = onAnalysisComplete;
  }, [onAnalysisComplete]);

  useEffect(() => {
    onCommentAIResponseRef.current = onCommentAIResponse;
  }, [onCommentAIResponse]);

  // 특정 메모의 로그 초기화
  const clearLogs = useCallback((memoId: string) => {
    setAnalysisLogs((prev) => {
      const newLogs = { ...prev };
      delete newLogs[memoId];
      return newLogs;
    });
  }, []);

  // 모든 로그 초기화
  const clearAllLogs = useCallback(() => {
    setAnalysisLogs({});
  }, []);

  const connect = useCallback(() => {
    // 이미 연결되어 있으면 무시
    if (eventSourceRef.current) {
      return;
    }

    const eventSource = new EventSource(`${API_BASE_URL}/temp-memos/analysis-events`);
    eventSourceRef.current = eventSource;

    // 분석 진행 상황 이벤트
    eventSource.addEventListener('analysis_progress', (event) => {
      try {
        const data: AnalysisProgressEvent = JSON.parse(event.data);
        data.timestamp = new Date().toLocaleTimeString('ko-KR');
        console.log('[SSE] Analysis progress:', data);

        setAnalysisLogs((prev) => ({
          ...prev,
          [data.memo_id]: [...(prev[data.memo_id] || []), data],
        }));
      } catch (error) {
        console.error('[SSE] Failed to parse progress event:', error);
      }
    });

    // 분석 완료 이벤트
    eventSource.addEventListener('analysis_complete', (event) => {
      try {
        const data: AnalysisCompleteEvent = JSON.parse(event.data);
        console.log('[SSE] Analysis complete:', data);
        onAnalysisCompleteRef.current(data.memo_id, data.status);
      } catch (error) {
        console.error('[SSE] Failed to parse event:', error);
      }
    });

    // AI 댓글 응답 이벤트
    eventSource.addEventListener('comment_ai_response', (event) => {
      try {
        const data: CommentAIResponseEvent = JSON.parse(event.data);
        console.log('[SSE] Comment AI response:', data);
        onCommentAIResponseRef.current?.(data);
      } catch (error) {
        console.error('[SSE] Failed to parse comment AI response:', error);
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

  return { connect, disconnect, analysisLogs, clearLogs, clearAllLogs };
}
