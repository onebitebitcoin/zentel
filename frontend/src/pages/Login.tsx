/**
 * 로그인 페이지
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, LogIn } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../hooks/useAuth';
import type { UserLogin } from '../types/auth';

export function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState<UserLogin>({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;

    setIsLoading(true);
    try {
      await login(formData);
      toast.success('로그인되었습니다.');
      navigate('/');
    } catch (error: unknown) {
      const errorMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || '로그인에 실패했습니다.';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const canSubmit = formData.username.length >= 3 && formData.password.length >= 8;

  return (
    <div className="flex flex-col min-h-full bg-gray-50">
      {/* 헤더 */}
      <div className="flex items-center justify-center px-4 py-8 md:py-12">
        <h1 className="text-2xl font-bold text-gray-800">Zentel</h1>
      </div>

      {/* 폼 */}
      <div className="flex-1 px-4 md:px-6">
        <div className="max-w-sm mx-auto space-y-6">
          <div className="text-center mb-8">
            <h2 className="text-xl font-semibold text-gray-800">로그인</h2>
            <p className="text-gray-500 mt-2">계정에 로그인하세요</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 사용자 이름 */}
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                사용자 이름
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="사용자 이름을 입력하세요"
                autoComplete="username"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              />
            </div>

            {/* 비밀번호 */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                비밀번호
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="비밀번호를 입력하세요"
                  autoComplete="current-password"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            {/* 회원가입 링크 */}
            <div className="text-center pt-4">
              <span className="text-gray-500">계정이 없으신가요? </span>
              <Link to="/register" className="text-primary font-medium hover:underline">
                회원가입
              </Link>
            </div>
          </form>
        </div>
      </div>

      {/* 로그인 버튼 (하단 고정) */}
      <div className="sticky bottom-0 left-0 right-0 px-4 pb-4 pt-4 bg-gradient-to-t from-gray-50 to-transparent safe-bottom">
        <div className="max-w-sm mx-auto">
          <button
            onClick={handleSubmit}
            disabled={!canSubmit || isLoading}
            className={`w-full flex items-center justify-center gap-2 py-4 rounded-xl font-semibold text-white transition-all ${
              canSubmit && !isLoading
                ? 'bg-primary hover:bg-primary-600 active:scale-[0.98]'
                : 'bg-gray-300'
            }`}
          >
            <LogIn size={20} />
            <span>{isLoading ? '로그인 중...' : '로그인'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
