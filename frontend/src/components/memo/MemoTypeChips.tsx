import {
  Lightbulb,
  Target,
  TrendingUp,
  HelpCircle,
  AlertTriangle,
  Heart,
} from 'lucide-react';
import type { MemoType, MemoTypeInfo } from '../../types/memo';
import { MEMO_TYPES } from '../../types/memo';

interface MemoTypeChipsProps {
  selectedType: MemoType;
  onSelect: (type: MemoType) => void;
}

const iconMap: Record<string, React.ReactNode> = {
  Lightbulb: <Lightbulb size={18} />,
  Target: <Target size={18} />,
  TrendingUp: <TrendingUp size={18} />,
  HelpCircle: <HelpCircle size={18} />,
  AlertTriangle: <AlertTriangle size={18} />,
  Heart: <Heart size={18} />,
};

function MemoTypeChip({
  info,
  isSelected,
  onSelect,
}: {
  info: MemoTypeInfo;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition-all ${
        isSelected
          ? `${info.bgColor} ${info.color} border-current`
          : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
      }`}
    >
      <span className={isSelected ? info.color : 'text-gray-400'}>
        {iconMap[info.icon]}
      </span>
      <span className="text-sm font-medium whitespace-nowrap">{info.label}</span>
    </button>
  );
}

export function MemoTypeChips({ selectedType, onSelect }: MemoTypeChipsProps) {
  return (
    <div className="space-y-2">
      <p className="text-sm text-gray-500 px-1">SELECT NOTE TYPE</p>
      <div className="grid grid-cols-2 gap-2">
        {MEMO_TYPES.map((info) => (
          <MemoTypeChip
            key={info.type}
            info={info}
            isSelected={selectedType === info.type}
            onSelect={() => onSelect(info.type)}
          />
        ))}
      </div>
    </div>
  );
}
