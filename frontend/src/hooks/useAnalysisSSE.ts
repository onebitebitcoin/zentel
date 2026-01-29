import { useEffect, useRef, useCallback, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
const ANALYSIS_LOGS_STORAGE_KEY = 'zentel_analysis_logs';

// 재연결 설정
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

export type SSEConnectionStatus = 'connected' | 'disconnected' | 'reconnecting';

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
 *
 * @param onAnalysisComplete 분석 완료 시 호출되는 콜백
 * @param onCommentAIResponse AI 댓글 응답 시 호출되는 콜백
 * @param onReconnect 재연결 시 호출되는 콜백 (분석 중인 메모들 상태 새로고침용)
 */
export function useAnalysisSSE(
  onAnalysisComplete: (memoId: string, status: string) => void,
  onCommentAIResponse?: (event: CommentAIResponseEvent) => void,
  onReconnect?: () => void
) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const onAnalysisCompleteRef = useRef(onAnalysisComplete);
  const onCommentAIResponseRef = useRef(onCommentAIResponse);
  const onReconnectRef = useRef(onReconnect);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 연결 상태
  const [connectionStatus, setConnectionStatus] = useState<SSEConnectionStatus>('disconnected');
  const [lastConnectedAt, setLastConnectedAt] = useState<Date | null>(null);

  // localStorage에서 로그 복원
  const [analysisLogs, setAnalysisLogs] = useState<AnalysisLogs>(() => {
    try {
      const stored = localStorage.getItem(ANALYSIS_LOGS_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.error('[useAnalysisSSE] Failed to load logs from localStorage:', error);
    }
    return {};
  });

  // 로그 변경 시 localStorage에 저장
  useEffect(() => {
    try {
      localStorage.setItem(ANALYSIS_LOGS_STORAGE_KEY, JSON.stringify(analysisLogs));
    } catch (error) {
      console.error('[useAnalysisSSE] Failed to save logs to localStorage:', error);
    }
  }, [analysisLogs]);

  // 콜백 참조 업데이트
  useEffect(() => {
    onAnalysisCompleteRef.current = onAnalysisComplete;
  }, [onAnalysisComplete]);

  useEffect(() => {
    onCommentAIResponseRef.current = onCommentAIResponse;
  }, [onCommentAIResponse]);

  useEffect(() => {
    onReconnectRef.current = onReconnect;
  }, [onReconnect]);

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

  // 재연결 타이머 정리
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      console.log('[SSE] Disconnected');
    }
    setConnectionStatus('disconnected');
  }, [clearReconnectTimeout]);

  const connect = useCallback((isReconnect: boolean = false) => {
    // 이미 연결되어 있으면 무시
    if (eventSourceRef.current?.readyState === EventSource.OPEN) {
      return;
    }

    // 기존 연결 정리
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    if (isReconnect) {
      setConnectionStatus('reconnecting');
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

        // 분석 완료 시 해당 메모의 로그 정리
        if (data.status === 'completed' || data.status === 'failed') {
          setAnalysisLogs((prev) => {
            const newLogs = { ...prev };
            delete newLogs[data.memo_id];
            return newLogs;
          });
        }
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

    eventSource.onerror = () => {
      console.error('[SSE] Connection error');
      eventSource.close();
      eventSourceRef.current = null;
      setConnectionStatus('disconnected');

      // 재연결 시도 (최대 횟수 제한)
      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttemptsRef.current += 1;
        const delay = RECONNECT_DELAY_MS * reconnectAttemptsRef.current; // 점진적 백오프
        console.log(`[SSE] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})...`);

        setConnectionStatus('reconnecting');
        reconnectTimeoutRef.current = setTimeout(() => {
          connect(true);
        }, delay);
      } else {
        console.error('[SSE] Max reconnect attempts reached');
        setConnectionStatus('disconnected');
      }
    };

    eventSource.onopen = () => {
      console.log('[SSE] Connected to analysis events');
      setConnectionStatus('connected');
      setLastConnectedAt(new Date());

      // 재연결 성공 시 카운터 리셋 및 상태 새로고침
      if (isReconnect || reconnectAttemptsRef.current > 0) {
        reconnectAttemptsRef.current = 0;
        console.log('[SSE] Reconnected - refreshing analyzing memos status');
        // 재연결 시 분석 중인 메모들 상태 새로고침
        onReconnectRef.current?.();
      }
    };
  }, []);

  // 수동 재연결 (사용자가 버튼 클릭)
  const manualReconnect = useCallback(() => {
    console.log('[SSE] Manual reconnect requested');
    reconnectAttemptsRef.current = 0; // 수동 재연결 시 카운터 리셋
    disconnect();
    connect(true);
  }, [disconnect, connect]);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connect,
    disconnect,
    manualReconnect,
    analysisLogs,
    clearLogs,
    clearAllLogs,
    connectionStatus,
    lastConnectedAt,
  };
}
