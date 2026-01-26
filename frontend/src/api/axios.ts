/**
 * 공통 Axios 인스턴스 설정
 *
 * - Base URL 설정
 * - Authorization 헤더 자동 추가
 * - Trailing slash 제거
 * - 401 에러 시 토큰 자동 갱신
 * - 동시 요청 시 토큰 갱신 중복 방지
 */
import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { tokenStorage } from '../utils/token';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// 토큰 갱신 상태 관리
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

// 토큰 갱신 완료 시 대기 중인 요청들에게 새 토큰 전달
const onRefreshed = (token: string) => {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
};

// 토큰 갱신 대기 큐에 추가
const addRefreshSubscriber = (callback: (token: string) => void) => {
  refreshSubscribers.push(callback);
};

/**
 * 공통 Axios 인스턴스 생성
 */
export const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true,
  });

  // Request 인터셉터
  instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    // Trailing slash 제거
    if (config.url && config.url.endsWith('/')) {
      config.url = config.url.slice(0, -1);
    }

    // Authorization 헤더 추가
    const token = tokenStorage.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  });

  // Response 인터셉터
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      // 401 에러이고, refresh/login 요청이 아니고, 재시도하지 않은 경우
      if (
        error.response?.status === 401 &&
        !originalRequest._retry &&
        !originalRequest.url?.includes('/auth/refresh') &&
        !originalRequest.url?.includes('/auth/login')
      ) {
        if (isRefreshing) {
          // 이미 토큰 갱신 중이면 대기
          return new Promise((resolve) => {
            addRefreshSubscriber((token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(instance(originalRequest));
            });
          });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          // Refresh Token으로 새 Access Token 발급
          const response = await axios.post(
            `${API_BASE_URL}/auth/refresh`,
            {},
            { withCredentials: true }
          );
          const { access_token } = response.data;

          // 새 토큰 저장
          tokenStorage.setAccessToken(access_token);

          // 대기 중인 요청들에게 새 토큰 전달
          onRefreshed(access_token);

          // 실패한 요청 재시도
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return instance(originalRequest);
        } catch {
          // Refresh Token도 만료되었으면 로그아웃 처리
          tokenStorage.clearTokens();
          window.location.href = '/login';
          return Promise.reject(error);
        } finally {
          isRefreshing = false;
        }
      }

      return Promise.reject(error);
    }
  );

  return instance;
};

// 공통 인스턴스 export
export const api = createApiInstance();
export { API_BASE_URL };
