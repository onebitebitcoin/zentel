/**
 * 게스트 전용 라우트 컴포넌트
 * - 이미 인증된 사용자는 홈으로 리다이렉트
 */
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface GuestRouteProps {
  children: React.ReactNode;
}

export function GuestRoute({ children }: GuestRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();

  // 로딩 중일 때는 로딩 UI 표시
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-4 border-gray-200 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  // 이미 인증된 경우 홈으로 리다이렉트
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
