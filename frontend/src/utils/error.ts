/**
 * 에러 처리 유틸리티
 */

interface ApiError {
  response?: {
    data?: {
      detail?: string;
      message?: string;
    };
    status?: number;
  };
  message?: string;
}

/**
 * API 에러에서 사용자 친화적인 메시지 추출
 */
export function getErrorMessage(error: unknown, defaultMessage = '오류가 발생했습니다.'): string {
  if (!error) {
    return defaultMessage;
  }

  // Axios 에러 형태
  if (typeof error === 'object' && 'response' in error) {
    const apiError = error as ApiError;

    // detail 메시지 우선
    if (apiError.response?.data?.detail) {
      return apiError.response.data.detail;
    }

    // message 메시지
    if (apiError.response?.data?.message) {
      return apiError.response.data.message;
    }

    // HTTP 상태 코드별 기본 메시지
    switch (apiError.response?.status) {
      case 400:
        return '잘못된 요청입니다.';
      case 401:
        return '인증이 필요합니다.';
      case 403:
        return '권한이 없습니다.';
      case 404:
        return '요청한 항목을 찾을 수 없습니다.';
      case 500:
        return '서버 오류가 발생했습니다.';
    }
  }

  // 일반 Error 객체
  if (error instanceof Error) {
    return error.message || defaultMessage;
  }

  // 문자열 에러
  if (typeof error === 'string') {
    return error;
  }

  return defaultMessage;
}

/**
 * 네트워크 에러인지 확인
 */
export function isNetworkError(error: unknown): boolean {
  if (!error || typeof error !== 'object') {
    return false;
  }

  // Axios network error
  if ('code' in error && error.code === 'ERR_NETWORK') {
    return true;
  }

  // No response received
  if ('response' in error && !(error as ApiError).response) {
    return true;
  }

  return false;
}
