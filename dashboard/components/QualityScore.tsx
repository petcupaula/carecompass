interface QualityScoreProps {
  label: string;
  value?: number;
  trend?: number;
}

export function QualityScore({ label, value, trend }: QualityScoreProps) {
  const getColor = (v: number) => {
    if (v >= 70) return 'text-green-600';
    if (v >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm">
      <div className="text-sm text-gray-500 mb-1">{label}</div>
      <div className="flex items-baseline gap-2">
        <span className={`text-3xl font-light ${value ? getColor(value) : 'text-gray-400'}`}>
          {value ? Math.round(value) : '--'}
        </span>
        {trend !== undefined && trend !== null && (
          <span className={`text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}
          </span>
        )}
      </div>
    </div>
  );
}
