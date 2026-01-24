import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Plus, LogOut, Edit2, Check } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../hooks/useAuth';
import { authService } from '../api/auth';
import { formatDate } from '../utils/date';
import type { AIPersona } from '../types/auth';

export function Settings() {
  const navigate = useNavigate();
  const { user, logout, setUser } = useAuth();

  // 비밀번호 변경 상태
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);

  // 관심사 상태
  const [interests, setInterests] = useState<string[]>(user?.interests || []);
  const [newInterest, setNewInterest] = useState('');
  const [savingInterest, setSavingInterest] = useState(false);

  // AI 페르소나 상태
  const [personas, setPersonas] = useState<AIPersona[]>(user?.ai_personas || []);
  const [newPersonaName, setNewPersonaName] = useState('');
  const [newPersonaDesc, setNewPersonaDesc] = useState('');
  const [savingPersona, setSavingPersona] = useState(false);
  const [editingPersonaIndex, setEditingPersonaIndex] = useState<number | null>(null);
  const [editPersonaName, setEditPersonaName] = useState('');
  const [editPersonaDesc, setEditPersonaDesc] = useState('');

  const handlePasswordChange = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('모든 필드를 입력해주세요.');
      return;
    }

    if (newPassword.length < 8) {
      toast.error('새 비밀번호는 8자 이상이어야 합니다.');
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error('새 비밀번호가 일치하지 않습니다.');
      return;
    }

    setChangingPassword(true);
    try {
      await authService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      toast.success('비밀번호가 변경되었습니다.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: unknown) {
      if (error instanceof Error && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        toast.error(axiosError.response?.data?.detail || '비밀번호 변경에 실패했습니다.');
      } else {
        toast.error('비밀번호 변경에 실패했습니다.');
      }
    } finally {
      setChangingPassword(false);
    }
  };

  const handleAddInterest = async () => {
    const trimmed = newInterest.trim();
    if (!trimmed) return;
    if (interests.includes(trimmed)) {
      toast.error('이미 추가된 관심사입니다.');
      return;
    }
    const newInterests = [...interests, trimmed];
    setInterests(newInterests);
    setNewInterest('');
    setSavingInterest(true);
    try {
      const updatedUser = await authService.updateProfile({ interests: newInterests });
      setUser(updatedUser);
      toast.success('관심사가 추가되었습니다.');
    } catch {
      setInterests(interests);
      toast.error('관심사 추가에 실패했습니다.');
    } finally {
      setSavingInterest(false);
    }
  };

  const handleRemoveInterest = async (interest: string) => {
    const newInterests = interests.filter((i) => i !== interest);
    setInterests(newInterests);
    setSavingInterest(true);
    try {
      const updatedUser = await authService.updateProfile({ interests: newInterests });
      setUser(updatedUser);
      toast.success('관심사가 삭제되었습니다.');
    } catch {
      setInterests(interests);
      toast.error('관심사 삭제에 실패했습니다.');
    } finally {
      setSavingInterest(false);
    }
  };

  const handleAddPersona = async () => {
    const trimmedName = newPersonaName.trim();
    if (!trimmedName) {
      toast.error('페르소나 이름을 입력해주세요.');
      return;
    }
    if (personas.some((p) => p.name === trimmedName)) {
      toast.error('이미 존재하는 페르소나 이름입니다.');
      return;
    }
    const newPersona: AIPersona = {
      name: trimmedName,
      description: newPersonaDesc.trim() || undefined,
    };
    const newPersonas = [...personas, newPersona];
    setPersonas(newPersonas);
    setNewPersonaName('');
    setNewPersonaDesc('');
    setSavingPersona(true);
    try {
      const updatedUser = await authService.updateProfile({ ai_personas: newPersonas });
      setUser(updatedUser);
      toast.success('페르소나가 추가되었습니다.');
    } catch {
      setPersonas(personas);
      toast.error('페르소나 추가에 실패했습니다.');
    } finally {
      setSavingPersona(false);
    }
  };

  const handleRemovePersona = async (index: number) => {
    const newPersonas = personas.filter((_, i) => i !== index);
    setPersonas(newPersonas);
    setSavingPersona(true);
    try {
      const updatedUser = await authService.updateProfile({ ai_personas: newPersonas });
      setUser(updatedUser);
      toast.success('페르소나가 삭제되었습니다.');
    } catch {
      setPersonas(personas);
      toast.error('페르소나 삭제에 실패했습니다.');
    } finally {
      setSavingPersona(false);
    }
  };

  const startEditPersona = (index: number) => {
    setEditingPersonaIndex(index);
    setEditPersonaName(personas[index].name);
    setEditPersonaDesc(personas[index].description || '');
  };

  const handleSavePersonaEdit = async () => {
    if (editingPersonaIndex === null) return;
    const trimmedName = editPersonaName.trim();
    if (!trimmedName) {
      toast.error('페르소나 이름을 입력해주세요.');
      return;
    }
    // 다른 페르소나와 이름 중복 체크 (자기 자신 제외)
    if (personas.some((p, i) => i !== editingPersonaIndex && p.name === trimmedName)) {
      toast.error('이미 존재하는 페르소나 이름입니다.');
      return;
    }
    const newPersonas = personas.map((p, i) =>
      i === editingPersonaIndex
        ? { name: trimmedName, description: editPersonaDesc.trim() || undefined }
        : p
    );
    setPersonas(newPersonas);
    setEditingPersonaIndex(null);
    setSavingPersona(true);
    try {
      const updatedUser = await authService.updateProfile({ ai_personas: newPersonas });
      setUser(updatedUser);
      toast.success('페르소나가 수정되었습니다.');
    } catch {
      setPersonas(personas);
      toast.error('페르소나 수정에 실패했습니다.');
    } finally {
      setSavingPersona(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="flex flex-col h-full">
      {/* PC: 상단 헤더 */}
      <div className="hidden md:flex items-center px-6 py-5 bg-white border-b border-gray-100">
        <h1 className="text-xl font-semibold text-gray-800">설정</h1>
      </div>

      <div className="flex-1 overflow-auto px-4 md:px-6 py-4 pb-24 md:pb-6 space-y-6">
        {/* 계정 정보 섹션 */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            계정 정보
          </h2>
          <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">사용자명</span>
              <span className="text-sm font-medium text-gray-800">
                {user?.username}
              </span>
            </div>
            <div className="border-t border-gray-100" />
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">가입일</span>
              <span className="text-sm text-gray-800">
                {user?.created_at ? formatDate(user.created_at) : '-'}
              </span>
            </div>
          </div>
        </section>

        {/* 관심사 섹션 */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            관심사
          </h2>
          <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
            {/* 관심사 태그 */}
            <div className="flex flex-wrap gap-2">
              {interests.map((interest) => (
                <span
                  key={interest}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-full"
                >
                  {interest}
                  <button
                    onClick={() => handleRemoveInterest(interest)}
                    disabled={savingInterest}
                    className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
                  >
                    <X size={14} />
                  </button>
                </span>
              ))}
              {interests.length === 0 && (
                <span className="text-sm text-gray-400">
                  관심사를 추가해보세요
                </span>
              )}
            </div>

            {/* 관심사 입력 */}
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="새 관심사 입력"
                value={newInterest}
                onChange={(e) => setNewInterest(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddInterest();
                  }
                }}
                disabled={savingInterest}
                className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary disabled:opacity-50"
              />
              <button
                onClick={handleAddInterest}
                disabled={savingInterest || !newInterest.trim()}
                className="px-3 py-2 text-primary border border-primary rounded-lg hover:bg-primary/5 disabled:opacity-50"
              >
                <Plus size={18} />
              </button>
            </div>
          </div>
        </section>

        {/* AI 페르소나 섹션 */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            AI 페르소나
          </h2>
          <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
            <p className="text-xs text-gray-400 mb-2">
              댓글에서 @이름으로 특정 페르소나를 호출하거나, 자동으로 랜덤 선택됩니다.
            </p>

            {/* 페르소나 목록 */}
            <div className="space-y-2">
              {personas.map((persona, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 p-2 bg-gray-50 rounded-lg"
                >
                  {editingPersonaIndex === index ? (
                    <div className="flex-1 space-y-2">
                      <input
                        type="text"
                        value={editPersonaName}
                        onChange={(e) => setEditPersonaName(e.target.value)}
                        placeholder="이름"
                        className="w-full px-2 py-1.5 text-sm border border-gray-200 rounded focus:outline-none focus:border-primary"
                      />
                      <input
                        type="text"
                        value={editPersonaDesc}
                        onChange={(e) => setEditPersonaDesc(e.target.value)}
                        placeholder="설명 (선택)"
                        className="w-full px-2 py-1.5 text-sm border border-gray-200 rounded focus:outline-none focus:border-primary"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={handleSavePersonaEdit}
                          disabled={savingPersona}
                          className="px-2 py-1 text-xs text-white bg-primary rounded hover:bg-primary-600 disabled:opacity-50"
                        >
                          <Check size={14} />
                        </button>
                        <button
                          onClick={() => setEditingPersonaIndex(null)}
                          className="px-2 py-1 text-xs text-gray-500 border border-gray-200 rounded hover:bg-gray-100"
                        >
                          취소
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex-1">
                        <span className="text-sm font-medium text-primary">
                          @{persona.name}
                        </span>
                        {persona.description && (
                          <p className="text-xs text-gray-500 mt-0.5">
                            {persona.description}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => startEditPersona(index)}
                        disabled={savingPersona}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                      >
                        <Edit2 size={14} />
                      </button>
                      <button
                        onClick={() => handleRemovePersona(index)}
                        disabled={savingPersona}
                        className="p-1 text-gray-400 hover:text-red-500 disabled:opacity-50"
                      >
                        <X size={14} />
                      </button>
                    </>
                  )}
                </div>
              ))}
              {personas.length === 0 && (
                <span className="text-sm text-gray-400">
                  AI 페르소나를 추가해보세요
                </span>
              )}
            </div>

            {/* 페르소나 추가 폼 */}
            <div className="space-y-2 pt-2 border-t border-gray-100">
              <input
                type="text"
                placeholder="페르소나 이름 (필수)"
                value={newPersonaName}
                onChange={(e) => setNewPersonaName(e.target.value)}
                disabled={savingPersona}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary disabled:opacity-50"
              />
              <input
                type="text"
                placeholder="설명 (선택, 예: 비판적 사고를 하는 분석가)"
                value={newPersonaDesc}
                onChange={(e) => setNewPersonaDesc(e.target.value)}
                disabled={savingPersona}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary disabled:opacity-50"
              />
              <button
                onClick={handleAddPersona}
                disabled={savingPersona || !newPersonaName.trim()}
                className="w-full flex items-center justify-center gap-1 py-2 text-sm text-primary border border-primary rounded-lg hover:bg-primary/5 disabled:opacity-50"
              >
                <Plus size={16} />
                페르소나 추가
              </button>
            </div>
          </div>
        </section>

        {/* 비밀번호 변경 섹션 */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            비밀번호 변경
          </h2>
          <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
            <input
              type="password"
              placeholder="현재 비밀번호"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary"
            />
            <input
              type="password"
              placeholder="새 비밀번호 (8자 이상)"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary"
            />
            <input
              type="password"
              placeholder="새 비밀번호 확인"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary"
            />
            <button
              onClick={handlePasswordChange}
              disabled={changingPassword}
              className="w-full py-2.5 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-600 disabled:opacity-50"
            >
              {changingPassword ? '변경 중...' : '비밀번호 변경'}
            </button>
          </div>
        </section>

        {/* 로그아웃 */}
        <section>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 py-3 text-sm font-medium text-red-500 bg-white border border-gray-100 rounded-xl hover:bg-red-50"
          >
            <LogOut size={18} />
            로그아웃
          </button>
        </section>
      </div>
    </div>
  );
}
