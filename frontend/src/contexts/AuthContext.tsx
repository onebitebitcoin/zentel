/**
 * 인증 상태 관리 Context
 */
import { useEffect, useState, useCallback, type ReactNode } from 'react';
import type { User, UserLogin, UserRegister } from '../types/auth';
import { authService } from '../api/auth';
import { tokenStorage } from '../utils/token';
import { AuthContext } from './AuthContextValue';

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
      // 토큰이 유효하지 않으면 로그아웃 처리
      tokenStorage.clearTokens();
      setUser(null);
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
