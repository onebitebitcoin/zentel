/**
 * 인증 API 클라이언트
 */
import axios from 'axios';
import type {
  User,
  UserRegister,
  UserLogin,
  TokenResponse,
  UsernameCheckResponse,
  PasswordChange,
  UserUpdate,
} from '../types/auth';
import { tokenStorage } from '../utils/token';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const authApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 쿠키 포함
});

// Trailing slash 제거 인터셉터
authApi.interceptors.request.use((config) => {
  if (config.url && config.url.endsWith('/')) {
    config.url = config.url.slice(0, -1);
  }
  return config;
});

// 토큰 갱신 중인지 추적하는 플래그
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

// 401 에러 시 자동 토큰 갱신 인터셉터
authApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 401 에러이고, refresh 요청이 아니고, 재시도하지 않은 요청인 경우
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
            resolve(authApi(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Refresh Token으로 새 Access Token 발급
        const response = await authApi.post<TokenResponse>('/auth/refresh', {});
        const { access_token } = response.data;

        // 새 토큰 저장
        tokenStorage.setAccessToken(access_token);

        // 대기 중인 요청들에게 새 토큰 전달
        onRefreshed(access_token);

        // 실패한 요청 재시도
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return authApi(originalRequest);
      } catch (refreshError) {
        // Refresh Token도 만료되었으면 로그아웃 처리
        tokenStorage.clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export const authService = {
  /**
   * 회원가입
   */
  register: async (data: UserRegister): Promise<User> => {
    const response = await authApi.post<User>('/auth/register', data);
    return response.data;
  },

  /**
   * 로그인
   */
  login: async (data: UserLogin): Promise<TokenResponse> => {
    const response = await authApi.post<TokenResponse>('/auth/login', data);
    const tokenData = response.data;

    // Access Token 저장
    tokenStorage.setAccessToken(tokenData.access_token);

    return tokenData;
  },

  /**
   * 로그아웃
   */
  logout: async (): Promise<void> => {
    const token = tokenStorage.getAccessToken();
    if (token) {
      try {
        await authApi.post('/auth/logout', null, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        // 로그아웃 API 실패해도 로컬 토큰은 삭제
      }
    }
    tokenStorage.clearTokens();
  },

  /**
   * 현재 사용자 정보 조회
   */
  getCurrentUser: async (): Promise<User> => {
    const token = tokenStorage.getAccessToken();
    const response = await authApi.get<User>('/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  /**
   * 토큰 갱신 (httpOnly 쿠키의 refresh_token 사용)
   */
  refreshToken: async (): Promise<TokenResponse> => {
    // body 없음 - refresh_token은 httpOnly 쿠키로 자동 전송
    const response = await authApi.post<TokenResponse>('/auth/refresh', {});
    const tokenData = response.data;

    // 새 Access Token 저장
    tokenStorage.setAccessToken(tokenData.access_token);

    return tokenData;
  },

  /**
   * 사용자 이름 중복 체크
   */
  checkUsername: async (username: string): Promise<UsernameCheckResponse> => {
    const response = await authApi.get<UsernameCheckResponse>(
      `/auth/check-username?username=${encodeURIComponent(username)}`
    );
    return response.data;
  },

  /**
   * 비밀번호 변경
   */
  changePassword: async (data: PasswordChange): Promise<{ message: string }> => {
    const token = tokenStorage.getAccessToken();
    const response = await authApi.put<{ message: string }>('/auth/password', data, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  /**
   * 프로필 업데이트
   */
  updateProfile: async (data: UserUpdate): Promise<User> => {
    const token = tokenStorage.getAccessToken();
    const response = await authApi.put<User>('/auth/profile', data, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },
};
