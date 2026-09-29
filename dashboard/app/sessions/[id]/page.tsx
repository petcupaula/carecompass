'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { EngagementTimeline } from '@/components/EngagementTimeline';
import { CoachingCard } from '@/components/CoachingCard';
import { QualityScore } from '@/components/QualityScore';

interface Signal {
  type: string;
  start: number;
  end: number;
  probability?: string;
  rationale?: string;
}

interface EngagementWindow {
  index: number;
  start_seconds: number;
  end_seconds: number;
  engagement_status: 'engaged' | 'neutral' | 'disengaged';
  signals: Signal[];
}

interface ConversationQuality {
  quality_index: number;
  clarity: number;
  authority: number;
  energy: number;
  rapport: number;
  learning: number;
}

interface CoachingInsight {
  title: string;
  description: string;
  specific_moment?: string;
  suggested_action: string;
}

interface TranscriptSegment {
  speaker_id?: string;
  start: number;
  end: number;
  text: string;
}

interface Session {
  id: string;
  provider_id: string;
  created_at: string;
  status: string;
  duration_seconds?: number;
  transcript?: TranscriptSegment[];
  engagement_windows?: EngagementWindow[];
  conversation_quality?: ConversationQuality;
  coaching_insights?: CoachingInsight[];
  error_message?: string;
}

export default function SessionDetail() {
  const params = useParams();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSession() {
      try {
        const res = await fetch(`/api/sessions/${params.id}`);
        if (res.ok) {
          setSession(await res.json());
        }
      } catch (e) {
        console.error('Failed to fetch session:', e);
      } finally {
        setLoading(false);
      }
    }

    fetchSession();
    // Poll while processing
    const interval = setInterval(() => {
      if (session?.status !== 'completed' && session?.status !== 'failed') {
        fetchSession();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [params.id, session?.status]);

  if (loading) {
    return (
      <main className="max-w-4xl mx-auto p-6">
        <div className="text-center text-gray-500">Loading...</div>
      </main>
    );
  }

  if (!session) {
    return (
      <main className="max-w-4xl mx-auto p-6">
        <div className="text-center text-gray-500">Session not found</div>
      </main>
    );
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <main className="max-w-4xl mx-auto p-6">
      {/* Back link */}
      <Link href="/" className="text-blue-600 hover:underline text-sm mb-4 inline-block">
        ← Back to Dashboard
      </Link>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-light text-gray-900">Session Analysis</h1>
        <p className="text-gray-500 mt-1">{formatDate(session.created_at)}</p>
        {session.status !== 'completed' && (
          <div className="mt-2 text-sm text-blue-600">
            Status: {session.status.replace('_', ' ')}...
          </div>
        )}
      </div>

      {session.error_message && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {session.error_message}
        </div>
      )}

      {/* Quality Scores */}
      {session.conversation_quality && (
        <div className="mb-8">
          <h2 className="text-lg font-medium mb-4">Conversation Quality</h2>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <QualityScore
              label="Overall"
              value={session.conversation_quality.quality_index}
            />
            <QualityScore label="Clarity" value={session.conversation_quality.clarity} />
            <QualityScore label="Authority" value={session.conversation_quality.authority} />
            <QualityScore label="Energy" value={session.conversation_quality.energy} />
            <QualityScore label="Rapport" value={session.conversation_quality.rapport} />
            <QualityScore label="Learning" value={session.conversation_quality.learning} />
          </div>
        </div>
      )}

      {/* Engagement Timeline */}
      {session.engagement_windows && session.engagement_windows.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-medium mb-4">Engagement Timeline</h2>
          <EngagementTimeline
            windows={session.engagement_windows}
            duration={session.duration_seconds || 0}
          />
        </div>
      )}

      {/* Coaching Insights */}
      {session.coaching_insights && session.coaching_insights.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-medium mb-4">Coaching Insights</h2>
          <div className="space-y-4">
            {session.coaching_insights.map((insight, i) => (
              <CoachingCard key={i} insight={insight} />
            ))}
          </div>
        </div>
      )}

      {/* Transcript */}
      {session.transcript && session.transcript.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-medium mb-4">Transcript</h2>
          <div className="bg-white rounded-xl shadow-sm p-6 space-y-4">
            {session.transcript.map((segment, i) => (
              <div key={i}>
                <div className="text-xs text-gray-400 mb-1">
                  {segment.speaker_id?.replace('SPEAKER_', 'Speaker ') || 'Speaker'} ·{' '}
                  {formatTime(segment.start)}
                </div>
                <div className="text-gray-700">{segment.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </main>
  );
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
