import { Package } from 'lucide-react';
import goldenIcon from '../assets/images/golden.png';

export function Outputs() {
  return (
    <div className="flex flex-col h-full">
      {/* PC Header */}
      <div className="hidden md:flex items-center gap-3 px-6 py-4 border-b border-gray-100">
        <img src={goldenIcon} alt="결과물" className="w-8 h-8" />
        <h1 className="text-xl font-bold text-gray-800">결과물</h1>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col items-center justify-center p-4 pb-20 md:pb-4">
        <div className="text-gray-300 mb-4">
          <Package size={64} strokeWidth={1} />
        </div>
        <p className="text-gray-500 text-center">
          아직 결과물이 없습니다
        </p>
        <p className="text-gray-400 text-sm text-center mt-1">
          영구 메모를 발전시켜 결과물을 만들어보세요
        </p>
      </div>
    </div>
  );
}
