import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  ArrowLeft,
  RefreshCw,
  ArrowRight,
  Lightbulb,
  Target,
  FileText,
  HelpCircle,
  Loader2,
  AlertCircle,
  Copy,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { usePermanentNotes } from '../hooks/usePermanentNotes';
import type { PermanentNoteDevelopResponse } from '../types/note';

interface LocationState {
  sourceMemoIds: string[];
}

export function DevelopmentPreview() {
  const navigate = useNavigate();
  const location = useLocation();
  const { developNote, developing, createNote } = usePermanentNotes();

  const [result, setResult] = useState<PermanentNoteDevelopResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [creatingOriginal, setCreatingOriginal] = useState(false);

  // location.state에서 sourceMemoIds 가져오기
  const state = location.state as LocationState | null;
  const sourceMemoIds = state?.sourceMemoIds || [];

  // 초기 분석 실행
  useEffect(() => {
    if (sourceMemoIds.length === 0) {
      toast.error('분석할 메모가 없습니다.');
      navigate('/inbox');
      return;
    }

    handleAnalyze();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAnalyze = async () => {
    if (sourceMemoIds.length === 0) return;

    setError(null);
    try {
      const data = await developNote(sourceMemoIds);
      setResult(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : '분석에 실패했습니다.';
      setError(message);
    }
  };

  const handleCreateNote = async () => {
    if (!result) return;

    setCreating(true);
    try {
      // 제안된 구조를 바탕으로 초기 내용 생성
      const initialContent = generateInitialContent(result);

      const note = await createNote({
        source_memo_ids: sourceMemoIds,
        title: result.suggested_structure.title,
        content: initialContent,
        analysis_result: result,
      });

      toast.success('영구 메모가 생성되었습니다.');
      navigate(`/notes/${note.id}`, { state: { analysisResult: result } });
    } catch {
      toast.error('영구 메모 생성에 실패했습니다.');
    } finally {
      setCreating(false);
    }
  };

  const generateInitialContent = (data: PermanentNoteDevelopResponse): string => {
    const lines: string[] = [];

    // 핵심 주장
    if (data.suggested_structure.thesis) {
      lines.push(data.suggested_structure.thesis);
      lines.push('');
    }

    // 본문 골격
    if (data.suggested_structure.body_outline.length > 0) {
      data.suggested_structure.body_outline.forEach((outline) => {
        lines.push(outline);
        lines.push('');
      });
    }

    // 추가 탐구 질문
    if (data.suggested_structure.questions_for_development.length > 0) {
      lines.push('---');
      lines.push('');
      lines.push('[추가 탐구 질문]');
      data.suggested_structure.questions_for_development.forEach((q) => {
        lines.push(`- ${q}`);
      });
    }

    return lines.join('\n');
  };

  // 원본 메모 그대로 영구 메모로 전환
  const handleCreateOriginal = async () => {
    if (!result) return;

    setCreatingOriginal(true);
    try {
      // 원본 메모 내용을 구분자로 합침
      const originalContent = result.source_memos
        .map((memo) => memo.content)
        .join('\n\n---\n\n');

      // 첫 번째 메모의 첫 줄을 제목으로
      const firstLine = result.source_memos[0]?.content.split('\n')[0].trim() || '제목 없음';
      const title = firstLine.length > 80 ? firstLine.slice(0, 80) : firstLine;

      const note = await createNote({
        source_memo_ids: sourceMemoIds,
        title,
        content: originalContent,
        analysis_result: result,
      });

      toast.success('영구 메모가 생성되었습니다.');
      navigate(`/notes/${note.id}`, { state: { analysisResult: result } });
    } catch {
      toast.error('영구 메모 생성에 실패했습니다.');
    } finally {
      setCreatingOriginal(false);
    }
  };

  const handleBack = () => {
    navigate('/inbox');
  };

  // 로딩 상태
  if (developing && !result) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gray-50 p-4">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary" />
          <div className="text-center">
            <p className="text-lg font-medium text-gray-800">
              AI가 메모를 분석하고 있습니다...
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {sourceMemoIds.length}개의 메모를 종합하여 영구 메모 구조를 제안합니다.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error && !result) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gray-50 p-4">
        <div className="flex flex-col items-center gap-4 max-w-md text-center">
          <AlertCircle className="w-12 h-12 text-red-500" />
          <div>
            <p className="text-lg font-medium text-gray-800">분석에 실패했습니다</p>
            <p className="text-sm text-gray-500 mt-1">{error}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleBack}
              className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:border-gray-300"
            >
              돌아가기
            </button>
            <button
              onClick={handleAnalyze}
              className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-600"
            >
              다시 시도
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-100">
        <div className="flex items-center gap-3">
          <button
            onClick={handleBack}
            className="p-2 -ml-2 text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft size={20} />
          </button>
          <span className="text-lg font-medium text-gray-800">메모 분석 결과</span>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={developing}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:border-gray-300 disabled:opacity-50"
        >
          {developing ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <RefreshCw size={14} />
          )}
          다시 분석
        </button>
      </div>

      {/* 컨텐츠 */}
      <div className="flex-1 overflow-auto p-4 pb-24 md:pb-6">
        <div className="w-full max-w-2xl mx-auto space-y-4">
          {/* 섹션 1: 개별 메모 분석 */}
          <section className="bg-white rounded-xl p-4 border border-gray-100">
            <div className="flex items-center gap-2 mb-3">
              <FileText size={18} className="text-blue-500" />
              <h2 className="font-medium text-gray-800">메모별 핵심 내용</h2>
            </div>
            <div className="space-y-3">
              {result.memo_analyses.map((analysis, index) => (
                <div
                  key={index}
                  className="p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center bg-blue-100 text-blue-600 text-xs font-medium rounded">
                      {analysis.memo_index}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-700">{analysis.core_content}</p>
                      {analysis.key_evidence.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {analysis.key_evidence.map((evidence, i) => (
                            <p key={i} className="text-xs text-gray-500 pl-2 border-l-2 border-gray-200">
                              {evidence}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* 섹션 2: 종합 분석 */}
          <section className="bg-white rounded-xl p-4 border border-gray-100">
            <div className="flex items-center gap-2 mb-3">
              <Target size={18} className="text-amber-500" />
              <h2 className="font-medium text-gray-800">종합 분석</h2>
            </div>
            <div className="space-y-3">
              {/* 핵심 주장 */}
              <div className="p-3 bg-amber-50 rounded-lg">
                <p className="text-xs font-medium text-amber-600 mb-1">핵심 주장</p>
                <p className="text-sm text-gray-700">{result.synthesis.main_argument}</p>
              </div>

              {/* 뒷받침 포인트 */}
              {result.synthesis.supporting_points.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-2">뒷받침 포인트</p>
                  <ul className="space-y-1.5">
                    {result.synthesis.supporting_points.map((point, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                        <span className="text-green-500 mt-0.5">+</span>
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 고려사항 */}
              {result.synthesis.counter_considerations.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-2">고려사항</p>
                  <ul className="space-y-1.5">
                    {result.synthesis.counter_considerations.map((point, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                        <span className="text-orange-500 mt-0.5">!</span>
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </section>

          {/* 섹션 3: 제안 구조 */}
          <section className="bg-white rounded-xl p-4 border border-gray-100">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb size={18} className="text-green-500" />
              <h2 className="font-medium text-gray-800">제안 구조</h2>
            </div>
            <div className="space-y-3">
              {/* 제목 */}
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-xs font-medium text-green-600 mb-1">제안 제목</p>
                <p className="text-base font-medium text-gray-800">
                  {result.suggested_structure.title}
                </p>
              </div>

              {/* 핵심 주장 */}
              {result.suggested_structure.thesis && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">핵심 문장</p>
                  <p className="text-sm text-gray-700 italic">
                    "{result.suggested_structure.thesis}"
                  </p>
                </div>
              )}

              {/* 본문 골격 */}
              {result.suggested_structure.body_outline.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-2">본문 골격</p>
                  <ol className="space-y-1.5">
                    {result.suggested_structure.body_outline.map((outline, index) => (
                      <li key={index} className="text-sm text-gray-600">
                        {outline}
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* 발전 질문 */}
              {result.suggested_structure.questions_for_development.length > 0 && (
                <div className="pt-2 border-t border-gray-100">
                  <div className="flex items-center gap-1.5 mb-2">
                    <HelpCircle size={14} className="text-purple-500" />
                    <p className="text-xs font-medium text-gray-500">추가 탐구 질문</p>
                  </div>
                  <ul className="space-y-1.5">
                    {result.suggested_structure.questions_for_development.map((q, index) => (
                      <li key={index} className="text-sm text-purple-600">
                        {q}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>

      {/* 하단 액션 바 */}
      <div className="fixed bottom-0 left-0 right-0 md:static bg-white border-t border-gray-100 p-4">
        <div className="max-w-2xl mx-auto space-y-2">
          <div className="flex gap-2">
            <button
              onClick={handleCreateOriginal}
              disabled={creatingOriginal || creating}
              className="flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium text-gray-600 border border-gray-200 rounded-xl hover:border-gray-300 disabled:opacity-50"
            >
              {creatingOriginal ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Copy size={16} />
              )}
              원본 그대로 전환
            </button>
            <button
              onClick={handleCreateNote}
              disabled={creating || creatingOriginal}
              className="flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium text-white bg-primary rounded-xl hover:bg-primary-600 disabled:opacity-50"
            >
              {creating ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <ArrowRight size={16} />
              )}
              AI 구조로 작성
            </button>
          </div>
          <button
            onClick={handleBack}
            className="w-full py-2 text-sm text-gray-400 hover:text-gray-600"
          >
            취소
          </button>
        </div>
      </div>
    </div>
  );
}
