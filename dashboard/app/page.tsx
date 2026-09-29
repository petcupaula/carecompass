'use client';

import { useEffect, useState } from 'react';
import { SessionCard } from '@/components/SessionCard';
import { QualityScore } from '@/components/QualityScore';

interface Session {
  id: string;
  provider_id: string;
  created_at: string;
  status: string;
  duration_seconds?: number;
  quality_index?: number;
  engagement_summary?: string;
}

interface Metrics {
  provider_id: string;
  total_sessions: number;
  avg_quality_index?: number;
  avg_clarity?: number;
  avg_rapport?: number;
  trend_quality_index?: number;
}

export default function Dashboard() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const providerId = 'dr-chen-test'; // Demo provider

  useEffect(() => {
    async function fetchData() {
      try {
        const [sessionsRes, metricsRes] = await Promise.all([
          fetch(`/api/sessions/?provider_id=${providerId}`),
          fetch(`/api/dashboard/metrics/${providerId}`),
        ]);

        if (sessionsRes.ok) {
          setSessions(await sessionsRes.json());
        }
        if (metricsRes.ok) {
          setMetrics(await metricsRes.json());
        }
      } catch (e) {
        setError('Failed to connect to backend. Make sure it\'s running on localhost:8000');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
    // Poll every 5 seconds for updates
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-light text-gray-900">CareCompass</h1>
        <p className="text-gray-500 mt-1">AI Shadow Coach for Healthcare Providers</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <QualityScore
            label="Quality Index"
            value={metrics.avg_quality_index}
            trend={metrics.trend_quality_index}
          />
          <QualityScore label="Clarity" value={metrics.avg_clarity} />
          <QualityScore label="Rapport" value={metrics.avg_rapport} />
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Total Sessions</div>
            <div className="text-3xl font-light">{metrics.total_sessions}</div>
          </div>
        </div>
      )}

      {/* Sessions List */}
      <div className="bg-white rounded-xl shadow-sm">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-medium">Recent Sessions</h2>
        </div>

        {loading ? (
          <div className="p-6 text-center text-gray-500">Loading...</div>
        ) : sessions.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <p>No sessions yet.</p>
            <p className="text-sm mt-2">
              Record a conversation with your Plaud device to get started.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {sessions.map((session) => (
              <SessionCard key={session.id} session={session} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
