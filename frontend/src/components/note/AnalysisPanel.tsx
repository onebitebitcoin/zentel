import { Lightbulb, Target, ChevronDown, ChevronUp, RefreshCw, Loader2 } from 'lucide-react';
import type { PermanentNoteDevelopResponse } from '../../types/note';

interface AnalysisPanelProps {
  analysisResult: PermanentNoteDevelopResponse;
  expanded: boolean;
  reanalyzing: boolean;
  hasSourceMemos: boolean;
  onToggle: () => void;
  onReanalyze: () => void;
}

export function AnalysisPanel({
  analysisResult,
  expanded,
  reanalyzing,
  hasSourceMemos,
  onToggle,
  onReanalyze,
}: AnalysisPanelProps) {
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100"
      >
        <div className="flex items-center gap-2">
          <Lightbulb size={16} className="text-amber-500" />
          <span className="text-sm font-medium text-gray-700">AI 분석 결과</span>
        </div>
        <div className="flex items-center gap-2">
          {hasSourceMemos && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onReanalyze();
              }}
              disabled={reanalyzing}
              className="flex items-center gap-1 px-2 py-1 text-xs text-primary hover:bg-primary/10 rounded-lg transition-colors disabled:opacity-50"
              title="출처 메모를 다시 분석합니다"
            >
              {reanalyzing ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <RefreshCw size={12} />
              )}
              다시 분석
            </button>
          )}
          {expanded ? (
            <ChevronUp size={16} className="text-gray-400" />
          ) : (
            <ChevronDown size={16} className="text-gray-400" />
          )}
        </div>
      </button>
      {expanded && (
        <div className="p-4 space-y-4 bg-white">
          {/* 종합 분석 */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Target size={14} className="text-amber-500" />
              <span className="text-xs font-medium text-gray-500">핵심 주장</span>
            </div>
            <p className="text-sm text-gray-700 bg-amber-50 p-3 rounded-lg">
              {analysisResult.synthesis.main_argument}
            </p>
          </div>

          {/* 뒷받침 포인트 */}
          {analysisResult.synthesis.supporting_points.length > 0 && (
            <div>
              <span className="text-xs font-medium text-gray-500">뒷받침 포인트</span>
              <ul className="mt-1.5 space-y-1">
                {analysisResult.synthesis.supporting_points.map((point, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="text-green-500 mt-0.5">+</span>
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 고려사항 */}
          {analysisResult.synthesis.counter_considerations.length > 0 && (
            <div>
              <span className="text-xs font-medium text-gray-500">고려사항</span>
              <ul className="mt-1.5 space-y-1">
                {analysisResult.synthesis.counter_considerations.map((point, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="text-orange-500 mt-0.5">!</span>
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 추가 탐구 질문 */}
          {analysisResult.suggested_structure.questions_for_development.length > 0 && (
            <div className="pt-2 border-t border-gray-100">
              <span className="text-xs font-medium text-gray-500">추가 탐구 질문</span>
              <ul className="mt-1.5 space-y-1">
                {analysisResult.suggested_structure.questions_for_development.map((q, i) => (
                  <li key={i} className="text-sm text-purple-600">
                    {q}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
