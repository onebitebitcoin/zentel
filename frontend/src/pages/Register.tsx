/**
 * 회원가입 페이지
 */
import { useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, UserPlus, Check, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../hooks/useAuth';
import { authService } from '../api/auth';
import rottenIcon from '../assets/images/rotten.png';
import type { UserRegister } from '../types/auth';

export function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [formData, setFormData] = useState<UserRegister & { confirmPassword: string }>({
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [usernameStatus, setUsernameStatus] = useState<{
    checking: boolean;
    available: boolean | null;
    message: string;
  }>({ checking: false, available: null, message: '' });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // 사용자 이름 변경 시 상태 초기화
    if (name === 'username') {
      setUsernameStatus({ checking: false, available: null, message: '' });
    }
  };

  const checkUsername = useCallback(async () => {
    const username = formData.username.trim();
    if (username.length < 3) {
      setUsernameStatus({
        checking: false,
        available: false,
        message: '사용자 이름은 3자 이상이어야 합니다',
      });
      return;
    }

    setUsernameStatus({ checking: true, available: null, message: '' });
    try {
      const result = await authService.checkUsername(username);
      setUsernameStatus({
        checking: false,
        available: result.available,
        message: result.message,
      });
    } catch {
      setUsernameStatus({
        checking: false,
        available: null,
        message: '중복 확인에 실패했습니다',
      });
    }
  }, [formData.username]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;

    // 비밀번호 확인
    if (formData.password !== formData.confirmPassword) {
      toast.error('비밀번호가 일치하지 않습니다.');
      return;
    }

    setIsLoading(true);
    try {
      await register({ username: formData.username, password: formData.password });
      toast.success('회원가입이 완료되었습니다.');
      navigate('/');
    } catch (error: unknown) {
      const errorMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || '회원가입에 실패했습니다.';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const passwordMatch = formData.password === formData.confirmPassword;
  const passwordValid = formData.password.length >= 8;
  const canSubmit =
    formData.username.length >= 3 &&
    passwordValid &&
    passwordMatch &&
    usernameStatus.available === true;

  return (
    <div className="flex flex-col min-h-full bg-gray-50">
      {/* 헤더 */}
      <div className="flex items-center justify-center px-4 py-8 md:py-12">
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <img src={rottenIcon} alt="Rotten Apple" className="w-10 h-10" />
          <span className="text-green-900">Rotten</span>{' '}
          <span className="text-red-900">Apple</span>
        </h1>
      </div>

      {/* 폼 */}
      <div className="flex-1 px-4 md:px-6">
        <div className="max-w-sm mx-auto space-y-6">
          <div className="text-center mb-8">
            <h2 className="text-xl font-semibold text-gray-800">회원가입</h2>
            <p className="text-gray-500 mt-2">새 계정을 만드세요</p>
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
              <div className="relative">
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  onBlur={checkUsername}
                  placeholder="영문, 숫자, 언더스코어 (3자 이상)"
                  autoComplete="username"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all pr-12"
                />
                {usernameStatus.checking ? (
                  <div className="absolute right-4 top-1/2 -translate-y-1/2">
                    <div className="w-5 h-5 border-2 border-gray-300 border-t-primary rounded-full animate-spin" />
                  </div>
                ) : usernameStatus.available !== null ? (
                  <div className="absolute right-4 top-1/2 -translate-y-1/2">
                    {usernameStatus.available ? (
                      <Check size={20} className="text-green-500" />
                    ) : (
                      <X size={20} className="text-red-500" />
                    )}
                  </div>
                ) : null}
              </div>
              {usernameStatus.message && (
                <p
                  className={`text-xs mt-1 ${
                    usernameStatus.available ? 'text-green-500' : 'text-red-500'
                  }`}
                >
                  {usernameStatus.message}
                </p>
              )}
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
                  placeholder="8자 이상"
                  autoComplete="new-password"
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
              {formData.password && !passwordValid && (
                <p className="text-xs text-red-500 mt-1">
                  비밀번호는 8자 이상이어야 합니다
                </p>
              )}
            </div>

            {/* 비밀번호 확인 */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                비밀번호 확인
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="비밀번호를 다시 입력하세요"
                  autoComplete="new-password"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
              {formData.confirmPassword && !passwordMatch && (
                <p className="text-xs text-red-500 mt-1">비밀번호가 일치하지 않습니다</p>
              )}
            </div>

            {/* 로그인 링크 */}
            <div className="text-center pt-4">
              <span className="text-gray-500">이미 계정이 있으신가요? </span>
              <Link to="/login" className="text-primary font-medium hover:underline">
                로그인
              </Link>
            </div>
          </form>
        </div>
      </div>

      {/* 회원가입 버튼 (하단 고정) */}
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
            <UserPlus size={20} />
            <span>{isLoading ? '가입 중...' : '회원가입'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
