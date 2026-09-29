interface CoachingInsight {
  title: string;
  description: string;
  specific_moment?: string;
  suggested_action: string;
}

interface CoachingCardProps {
  insight: CoachingInsight;
}

export function CoachingCard({ insight }: CoachingCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="font-medium text-gray-900 mb-2">{insight.title}</h3>
      
      {insight.specific_moment && (
        <div className="text-sm text-gray-500 mb-3">
          <span className="font-medium">Moment:</span> {insight.specific_moment}
        </div>
      )}
      
      {insight.description && (
        <p className="text-gray-600 mb-4">{insight.description}</p>
      )}
      
      <div className="bg-blue-50 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <span className="text-xl">💡</span>
          <div>
            <div className="text-sm font-medium text-blue-900 mb-1">Suggested Action</div>
            <div className="text-sm text-blue-800">{insight.suggested_action}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
