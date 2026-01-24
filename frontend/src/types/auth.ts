/**
 * 인증 관련 타입 정의
 */

export interface AIPersona {
  name: string;
  description?: string;
}

export interface User {
  id: string;
  username: string;
  is_active: boolean;
  interests: string[] | null;
  ai_personas: AIPersona[] | null;
  created_at: string;
  updated_at: string | null;
}

export interface UserRegister {
  username: string;
  password: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UsernameCheckResponse {
  available: boolean;
  message: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}

export interface UserUpdate {
  interests?: string[];
  ai_personas?: AIPersona[];
}
