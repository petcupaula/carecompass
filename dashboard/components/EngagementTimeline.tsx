interface EngagementWindow {
  index: number;
  start_seconds: number;
  end_seconds: number;
  engagement_status: 'engaged' | 'neutral' | 'disengaged';
  signals: Array<{
    type: string;
    rationale?: string;
  }>;
}

interface EngagementTimelineProps {
  windows: EngagementWindow[];
  duration: number;
}

export function EngagementTimeline({ windows, duration }: EngagementTimelineProps) {
  const getColor = (status: string) => {
    switch (status) {
      case 'engaged':
        return 'bg-green-500';
      case 'neutral':
        return 'bg-yellow-500';
      case 'disengaged':
        return 'bg-red-500';
      default:
        return 'bg-gray-300';
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate engagement stats
  const stats = windows.reduce(
    (acc, w) => {
      acc[w.engagement_status] = (acc[w.engagement_status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const total = windows.length;

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      {/* Timeline bars */}
      <div className="flex gap-1 h-12 mb-4">
        {windows.map((window, i) => (
          <div
            key={i}
            className={`flex-1 rounded ${getColor(window.engagement_status)} relative group cursor-pointer`}
            title={`${formatTime(window.start_seconds)} - ${formatTime(window.end_seconds)}: ${window.engagement_status}`}
          >
            {/* Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
              <div className="bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                {formatTime(window.start_seconds)} - {window.engagement_status}
                {window.signals.length > 0 && (
                  <div className="text-gray-300">
                    {window.signals.map((s) => s.type).join(', ')}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Time labels */}
      <div className="flex justify-between text-xs text-gray-400 mb-4">
        <span>0:00</span>
        <span>{formatTime(duration)}</span>
      </div>

      {/* Legend */}
      <div className="flex gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-500"></div>
          <span>Engaged ({stats.engaged || 0}/{total})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-yellow-500"></div>
          <span>Neutral ({stats.neutral || 0}/{total})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-500"></div>
          <span>Disengaged ({stats.disengaged || 0}/{total})</span>
        </div>
      </div>
    </div>
  );
}
