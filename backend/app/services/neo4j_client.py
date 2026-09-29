"""
Neo4j Knowledge Graph Service

Stores sessions, quality scores, and coaching insights as a graph
to track provider improvement over time.

Graph Model:
  (:Provider)-[:CONDUCTED]->(:Session)-[:HAS_QUALITY]->(:QualityScore)
                                      -[:GENERATED]->(:CoachingInsight)
                                      -[:HAS_SIGNAL]->(:SocialSignal)
"""

from typing import Optional, List
from datetime import datetime

from ..config import get_settings
from ..models import (
    Session,
    ConversationQuality,
    CoachingInsight,
    EngagementWindow,
)


class Neo4jClient:
    """Client for Neo4j knowledge graph operations."""
    
    def __init__(self):
        settings = get_settings()
        self.uri = settings.neo4j_uri
        self.username = settings.neo4j_username
        self.password = settings.neo4j_password
        self._driver = None
        
    @property
    def driver(self):
        """Lazy-load the Neo4j driver."""
        if self._driver is None:
            if not self.uri:
                return None
            try:
                from neo4j import GraphDatabase
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password)
                )
            except Exception as e:
                print(f"[Neo4j] Failed to connect: {e}")
                return None
        return self._driver
    
    @property
    def is_configured(self) -> bool:
        """Check if Neo4j is configured."""
        return bool(self.uri and self.username and self.password)
    
    async def store_session(self, session: Session) -> bool:
        """
        Store a completed session in the knowledge graph.
        
        Creates nodes for:
        - Provider (if not exists)
        - Session
        - QualityScore
        - CoachingInsights
        - SocialSignals (aggregated from engagement windows)
        """
        if not self.driver:
            print("[Neo4j] Not configured, skipping store")
            return False
        
        try:
            with self.driver.session() as db_session:
                # Create/merge Provider and Session
                db_session.run("""
                    MERGE (p:Provider {id: $provider_id})
                    CREATE (s:Session {
                        id: $session_id,
                        created_at: datetime($created_at),
                        duration_seconds: $duration
                    })
                    CREATE (p)-[:CONDUCTED]->(s)
                """, {
                    "provider_id": session.provider_id,
                    "session_id": session.id,
                    "created_at": session.created_at.isoformat(),
                    "duration": session.duration_seconds or 0,
                })
                
                # Store quality scores
                if session.conversation_quality:
                    q = session.conversation_quality
                    db_session.run("""
                        MATCH (s:Session {id: $session_id})
                        CREATE (q:QualityScore {
                            quality_index: $quality_index,
                            clarity: $clarity,
                            authority: $authority,
                            energy: $energy,
                            rapport: $rapport,
                            learning: $learning
                        })
                        CREATE (s)-[:HAS_QUALITY]->(q)
                    """, {
                        "session_id": session.id,
                        "quality_index": q.quality_index,
                        "clarity": q.clarity,
                        "authority": q.authority,
                        "energy": q.energy,
                        "rapport": q.rapport,
                        "learning": q.learning,
                    })
                
                # Store coaching insights
                if session.coaching_insights:
                    for insight in session.coaching_insights:
                        db_session.run("""
                            MATCH (s:Session {id: $session_id})
                            CREATE (c:CoachingInsight {
                                title: $title,
                                description: $description,
                                suggested_action: $action
                            })
                            CREATE (s)-[:GENERATED]->(c)
                        """, {
                            "session_id": session.id,
                            "title": insight.title,
                            "description": insight.description,
                            "action": insight.suggested_action,
                        })
                
                # Store aggregated social signals
                if session.engagement_windows:
                    signal_counts = {}
                    for window in session.engagement_windows:
                        for signal in window.signals:
                            signal_type = signal.type
                            if signal_type not in signal_counts:
                                signal_counts[signal_type] = 0
                            signal_counts[signal_type] += 1
                    
                    for signal_type, count in signal_counts.items():
                        db_session.run("""
                            MATCH (s:Session {id: $session_id})
                            CREATE (sig:SocialSignal {
                                type: $type,
                                count: $count
                            })
                            CREATE (s)-[:HAS_SIGNAL]->(sig)
                        """, {
                            "session_id": session.id,
                            "type": signal_type,
                            "count": count,
                        })
                
                print(f"[Neo4j] Stored session {session.id}")
                return True
                
        except Exception as e:
            print(f"[Neo4j] Failed to store session: {e}")
            return False
    
    async def get_provider_trends(self, provider_id: str, limit: int = 10) -> dict:
        """
        Get quality score trends for a provider.
        
        Returns recent sessions with quality scores to show improvement over time.
        """
        if not self.driver:
            return {"error": "Neo4j not configured"}
        
        try:
            with self.driver.session() as db_session:
                result = db_session.run("""
                    MATCH (p:Provider {id: $provider_id})-[:CONDUCTED]->(s:Session)-[:HAS_QUALITY]->(q:QualityScore)
                    RETURN s.id as session_id, 
                           s.created_at as created_at,
                           q.quality_index as quality_index,
                           q.clarity as clarity,
                           q.rapport as rapport
                    ORDER BY s.created_at DESC
                    LIMIT $limit
                """, {"provider_id": provider_id, "limit": limit})
                
                sessions = []
                for record in result:
                    sessions.append({
                        "session_id": record["session_id"],
                        "created_at": str(record["created_at"]),
                        "quality_index": record["quality_index"],
                        "clarity": record["clarity"],
                        "rapport": record["rapport"],
                    })
                
                # Calculate trend (simple: compare first and last)
                trend = None
                if len(sessions) >= 2:
                    oldest = sessions[-1]["quality_index"]
                    newest = sessions[0]["quality_index"]
                    trend = newest - oldest
                
                return {
                    "provider_id": provider_id,
                    "sessions": sessions,
                    "trend": trend,
                    "session_count": len(sessions),
                }
                
        except Exception as e:
            print(f"[Neo4j] Failed to get trends: {e}")
            return {"error": str(e)}
    
    async def get_common_coaching_themes(self, provider_id: str) -> List[dict]:
        """
        Find recurring coaching themes for a provider.
        
        Groups coaching insights by similar titles to identify patterns.
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as db_session:
                result = db_session.run("""
                    MATCH (p:Provider {id: $provider_id})-[:CONDUCTED]->(s:Session)-[:GENERATED]->(c:CoachingInsight)
                    RETURN c.title as title, count(*) as occurrences
                    ORDER BY occurrences DESC
                    LIMIT 5
                """, {"provider_id": provider_id})
                
                themes = []
                for record in result:
                    themes.append({
                        "title": record["title"],
                        "occurrences": record["occurrences"],
                    })
                
                return themes
                
        except Exception as e:
            print(f"[Neo4j] Failed to get themes: {e}")
            return []
    
    async def get_signal_patterns(self, provider_id: str) -> dict:
        """
        Analyze social signal patterns across sessions.
        
        Shows which signals appear most frequently in the provider's conversations.
        """
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as db_session:
                result = db_session.run("""
                    MATCH (p:Provider {id: $provider_id})-[:CONDUCTED]->(s:Session)-[:HAS_SIGNAL]->(sig:SocialSignal)
                    RETURN sig.type as signal_type, sum(sig.count) as total_count
                    ORDER BY total_count DESC
                """, {"provider_id": provider_id})
                
                signals = {}
                for record in result:
                    signals[record["signal_type"]] = record["total_count"]
                
                return signals
                
        except Exception as e:
            print(f"[Neo4j] Failed to get signal patterns: {e}")
            return {}
    
    def close(self):
        """Close the driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None


# Singleton instance
_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    global _client
    if _client is None:
        _client = Neo4jClient()
    return _client
