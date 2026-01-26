/**
 * 인증 API 클라이언트
 */
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
import { api } from './axios';

export const authService = {
  /**
   * 회원가입
   */
  register: async (data: UserRegister): Promise<User> => {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  /**
   * 로그인
   */
  login: async (data: UserLogin): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', data);
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
        await api.post('/auth/logout', null, {
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
    const response = await api.get<User>('/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  /**
   * 토큰 갱신 (httpOnly 쿠키의 refresh_token 사용)
   */
  refreshToken: async (): Promise<TokenResponse> => {
    // body 없음 - refresh_token은 httpOnly 쿠키로 자동 전송
    const response = await api.post<TokenResponse>('/auth/refresh', {});
    const tokenData = response.data;

    // 새 Access Token 저장
    tokenStorage.setAccessToken(tokenData.access_token);

    return tokenData;
  },

  /**
   * 사용자 이름 중복 체크
   */
  checkUsername: async (username: string): Promise<UsernameCheckResponse> => {
    const response = await api.get<UsernameCheckResponse>(
      `/auth/check-username?username=${encodeURIComponent(username)}`
    );
    return response.data;
  },

  /**
   * 비밀번호 변경
   */
  changePassword: async (data: PasswordChange): Promise<{ message: string }> => {
    const token = tokenStorage.getAccessToken();
    const response = await api.put<{ message: string }>('/auth/password', data, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  /**
   * 프로필 업데이트
   */
  updateProfile: async (data: UserUpdate): Promise<User> => {
    const token = tokenStorage.getAccessToken();
    const response = await api.put<User>('/auth/profile', data, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },
};
