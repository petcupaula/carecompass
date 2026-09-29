from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    GENERATING_COACHING = "generating_coaching"
    COMPLETED = "completed"
    FAILED = "failed"


class EngagementLevel(str, Enum):
    ENGAGED = "engaged"
    NEUTRAL = "neutral"
    DISENGAGED = "disengaged"


class Signal(BaseModel):
    """A detected social signal from Interhuman AI."""
    type: str
    start: float
    end: float
    probability: Optional[str] = None
    rationale: Optional[str] = None
    modality: List[str] = []


class EngagementWindow(BaseModel):
    """Engagement analysis for a time window."""
    index: int
    start_seconds: float
    end_seconds: float
    engagement_status: EngagementLevel
    signals: List[Signal] = []


class ConversationQuality(BaseModel):
    """Conversation Quality Index scores."""
    quality_index: float = Field(description="Overall quality (0-100)")
    clarity: float = Field(description="Clarity/Structure (0-100)")
    authority: float = Field(description="Authority/Credibility (0-100)")
    energy: float = Field(description="Energy/Presence (0-100)")
    rapport: float = Field(description="Rapport/Relational Safety (0-100)")
    learning: float = Field(description="Learning/Exploration (0-100)")


class TranscriptSegment(BaseModel):
    """A segment of the transcript with speaker and timing."""
    speaker_id: Optional[str] = None
    start: float
    end: float
    text: str


class CoachingInsight(BaseModel):
    """AI-generated coaching recommendation."""
    title: str
    description: str
    specific_moment: Optional[str] = None
    suggested_action: str


class Session(BaseModel):
    """A recorded patient-provider session."""
    id: str
    provider_id: str
    created_at: datetime
    duration_seconds: Optional[float] = None
    status: AnalysisStatus = AnalysisStatus.PENDING
    
    # Audio file info
    audio_path: Optional[str] = None
    
    # Transcript (from Plaud)
    transcript: Optional[List[TranscriptSegment]] = None
    
    # Engagement analysis (from Interhuman AI)
    engagement_windows: Optional[List[EngagementWindow]] = None
    conversation_quality: Optional[ConversationQuality] = None
    
    # Coaching insights (from Crusoe LLM)
    coaching_insights: Optional[List[CoachingInsight]] = None
    
    # Error info
    error_message: Optional[str] = None


class SessionCreate(BaseModel):
    """Request to create a new session."""
    provider_id: str


class SessionSummary(BaseModel):
    """Summary view of a session for list display."""
    id: str
    provider_id: str
    created_at: datetime
    duration_seconds: Optional[float] = None
    status: AnalysisStatus
    quality_index: Optional[float] = None
    engagement_summary: Optional[str] = None


class ProviderMetrics(BaseModel):
    """Aggregated metrics for a provider."""
    provider_id: str
    total_sessions: int
    avg_quality_index: Optional[float] = None
    avg_clarity: Optional[float] = None
    avg_rapport: Optional[float] = None
    trend_quality_index: Optional[float] = None  # Change over last N sessions
    top_coaching_themes: List[str] = []
