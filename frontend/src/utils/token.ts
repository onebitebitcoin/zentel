/**
 * 토큰 저장/조회/삭제 유틸리티
 */

const ACCESS_TOKEN_KEY = 'myrottenapple_access_token';
const REFRESH_TOKEN_KEY = 'myrottenapple_refresh_token';

export const tokenStorage = {
  /**
   * Access Token 저장
   */
  setAccessToken: (token: string): void => {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  },

  /**
   * Access Token 조회
   */
  getAccessToken: (): string | null => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  /**
   * Access Token 삭제
   */
  removeAccessToken: (): void => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  },

  /**
   * Refresh Token 저장 (백업용 - 주로 쿠키 사용)
   */
  setRefreshToken: (token: string): void => {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  },

  /**
   * Refresh Token 조회
   */
  getRefreshToken: (): string | null => {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  /**
   * Refresh Token 삭제
   */
  removeRefreshToken: (): void => {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  /**
   * 모든 토큰 삭제
   */
  clearTokens: (): void => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  /**
   * 토큰 존재 여부 확인
   */
  hasToken: (): boolean => {
    return !!localStorage.getItem(ACCESS_TOKEN_KEY);
  },
};
