"""
Dashboard API Router

Provides aggregated metrics and analytics for providers.
"""

from typing import Optional, List
from collections import defaultdict

from fastapi import APIRouter

from ..models import ProviderMetrics, AnalysisStatus
from ..services import get_neo4j_client
from .sessions import sessions


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics/{provider_id}", response_model=ProviderMetrics)
async def get_provider_metrics(provider_id: str) -> ProviderMetrics:
    """Get aggregated metrics for a provider."""
    provider_sessions = [
        s for s in sessions.values()
        if s.provider_id == provider_id and s.status == AnalysisStatus.COMPLETED
    ]
    
    total_sessions = len(provider_sessions)
    
    if total_sessions == 0:
        return ProviderMetrics(
            provider_id=provider_id,
            total_sessions=0,
        )
    
    # Calculate averages
    quality_scores = []
    clarity_scores = []
    rapport_scores = []
    
    for s in provider_sessions:
        if s.conversation_quality:
            quality_scores.append(s.conversation_quality.quality_index)
            clarity_scores.append(s.conversation_quality.clarity)
            rapport_scores.append(s.conversation_quality.rapport)
    
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None
    avg_clarity = sum(clarity_scores) / len(clarity_scores) if clarity_scores else None
    avg_rapport = sum(rapport_scores) / len(rapport_scores) if rapport_scores else None
    
    # Calculate trend (last 5 vs previous 5)
    trend = None
    if len(quality_scores) >= 10:
        recent = quality_scores[-5:]
        previous = quality_scores[-10:-5]
        trend = sum(recent) / 5 - sum(previous) / 5
    
    # Extract top coaching themes
    theme_counts = defaultdict(int)
    for s in provider_sessions:
        if s.coaching_insights:
            for insight in s.coaching_insights:
                # Simple theme extraction from title
                theme_counts[insight.title] += 1
    
    top_themes = sorted(theme_counts.keys(), key=lambda t: theme_counts[t], reverse=True)[:3]
    
    return ProviderMetrics(
        provider_id=provider_id,
        total_sessions=total_sessions,
        avg_quality_index=avg_quality,
        avg_clarity=avg_clarity,
        avg_rapport=avg_rapport,
        trend_quality_index=trend,
        top_coaching_themes=top_themes,
    )


@router.get("/metrics", response_model=List[ProviderMetrics])
async def get_all_provider_metrics() -> List[ProviderMetrics]:
    """Get metrics for all providers."""
    # Get unique provider IDs
    provider_ids = set(s.provider_id for s in sessions.values())
    
    metrics = []
    for provider_id in provider_ids:
        m = await get_provider_metrics(provider_id)
        metrics.append(m)
    
    # Sort by total sessions descending
    metrics.sort(key=lambda m: m.total_sessions, reverse=True)
    
    return metrics


# Neo4j Knowledge Graph Endpoints

@router.get("/graph/trends/{provider_id}")
async def get_provider_trends(provider_id: str):
    """
    Get quality score trends from Neo4j knowledge graph.
    
    Shows how a provider's scores have changed over time.
    """
    neo4j = get_neo4j_client()
    if not neo4j.is_configured:
        return {"error": "Neo4j not configured", "configured": False}
    
    return await neo4j.get_provider_trends(provider_id)


@router.get("/graph/themes/{provider_id}")
async def get_coaching_themes(provider_id: str):
    """
    Get recurring coaching themes from Neo4j knowledge graph.
    
    Identifies patterns in coaching recommendations across sessions.
    """
    neo4j = get_neo4j_client()
    if not neo4j.is_configured:
        return {"error": "Neo4j not configured", "configured": False}
    
    themes = await neo4j.get_common_coaching_themes(provider_id)
    return {"provider_id": provider_id, "themes": themes}


@router.get("/graph/signals/{provider_id}")
async def get_signal_patterns(provider_id: str):
    """
    Get social signal patterns from Neo4j knowledge graph.
    
    Shows which signals appear most frequently in conversations.
    """
    neo4j = get_neo4j_client()
    if not neo4j.is_configured:
        return {"error": "Neo4j not configured", "configured": False}
    
    signals = await neo4j.get_signal_patterns(provider_id)
    return {"provider_id": provider_id, "signals": signals}
