/**
 * 인증 상태 관리 Context
 */
import { useEffect, useState, useCallback, useContext, type ReactNode } from 'react';
import type { User, UserLogin, UserRegister } from '../types/auth';
import { authService } from '../api/auth';
import { tokenStorage } from '../utils/token';
import { AuthContext } from './AuthContextValue';

/**
 * 인증 Context 사용 훅
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  /**
   * 인증 상태 확인
   */
  const checkAuth = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch {
      // Access Token이 만료되었을 가능성 - Refresh Token으로 갱신 시도
      try {
        await authService.refreshToken();
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } catch {
        // Refresh Token도 만료되었으면 로그아웃 처리
        tokenStorage.clearTokens();
        setUser(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * 로그인
   */
  const login = useCallback(async (data: UserLogin) => {
    await authService.login(data);
    // 로그인 성공 후 사용자 정보 조회
    const currentUser = await authService.getCurrentUser();
    setUser(currentUser);
  }, []);

  /**
   * 회원가입
   */
  const register = useCallback(async (data: UserRegister) => {
    await authService.register(data);
    // 회원가입 후 자동 로그인
    await login(data);
  }, [login]);

  /**
   * 로그아웃
   */
  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  // 앱 시작 시 인증 상태 확인
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
        checkAuth,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
