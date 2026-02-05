/**
 * 구조화된 로거 유틸리티
 * 개발 환경에서만 로깅, 프로덕션에서는 error만 출력
 */
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const isDev = import.meta.env.DEV;

const formatMessage = (level: LogLevel, message: string): string => {
  const timestamp = new Date().toISOString();
  return `[${timestamp}] [${level.toUpperCase()}] ${message}`;
};

export const logger = {
  debug: (message: string, data?: unknown): void => {
    if (isDev) {
      console.log(formatMessage('debug', message), data ?? '');
    }
  },

  info: (message: string, data?: unknown): void => {
    if (isDev) {
      console.info(formatMessage('info', message), data ?? '');
    }
  },

  warn: (message: string, data?: unknown): void => {
    if (isDev) {
      console.warn(formatMessage('warn', message), data ?? '');
    }
  },

  error: (message: string, data?: unknown): void => {
    // error는 항상 출력 (프로덕션 포함)
    console.error(formatMessage('error', message), data ?? '');
  },
};
