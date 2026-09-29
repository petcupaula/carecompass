'use client';

import Link from 'next/link';

interface Session {
  id: string;
  provider_id: string;
  created_at: string;
  status: string;
  duration_seconds?: number;
  quality_index?: number;
  engagement_summary?: string;
}

interface SessionCardProps {
  session: Session;
}

export function SessionCard({ session }: SessionCardProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-600',
      transcribing: 'bg-blue-100 text-blue-600',
      analyzing: 'bg-purple-100 text-purple-600',
      generating_coaching: 'bg-indigo-100 text-indigo-600',
      completed: 'bg-green-100 text-green-600',
      failed: 'bg-red-100 text-red-600',
    };
    return styles[status] || styles.pending;
  };

  const getQualityColor = (score?: number) => {
    if (!score) return 'text-gray-400';
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Link href={`/sessions/${session.id}`}>
      <div className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <span className="font-medium text-gray-900">
                {formatDate(session.created_at)}
              </span>
              <span className={`text-xs px-2 py-1 rounded-full ${getStatusBadge(session.status)}`}>
                {session.status.replace('_', ' ')}
              </span>
            </div>
            <div className="text-sm text-gray-500 mt-1">
              Duration: {formatDuration(session.duration_seconds)}
              {session.engagement_summary && ` · ${session.engagement_summary}`}
            </div>
          </div>
          <div className={`text-2xl font-light ${getQualityColor(session.quality_index)}`}>
            {session.quality_index ? Math.round(session.quality_index) : '--'}
          </div>
        </div>
      </div>
    </Link>
  );
}
