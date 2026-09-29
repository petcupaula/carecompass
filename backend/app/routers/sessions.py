"""
Sessions API Router

Handles session creation, audio upload, and analysis pipeline.
"""

import os
import uuid
import aiofiles
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ..config import get_settings
from ..models import (
    Session,
    SessionCreate,
    SessionSummary,
    AnalysisStatus,
)
from ..services import (
    get_interhuman_client,
    get_plaud_client,
    get_crusoe_client,
)


router = APIRouter(prefix="/sessions", tags=["sessions"])

# In-memory session store (replace with database in production)
sessions: Dict[str, Session] = {}


@router.post("/", response_model=Session)
async def create_session(session_create: SessionCreate) -> Session:
    """Create a new session for a provider."""
    session_id = str(uuid.uuid4())
    session = Session(
        id=session_id,
        provider_id=session_create.provider_id,
        created_at=datetime.utcnow(),
        status=AnalysisStatus.PENDING,
    )
    sessions[session_id] = session
    return session


@router.post("/{session_id}/upload")
async def upload_audio(
    session_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> JSONResponse:
    """
    Upload audio file for a session and start analysis pipeline.
    
    Accepts: wav, mp3, m4a, ogg, flac, webm
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Validate file type
    allowed_extensions = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
        )
    
    # Save file
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{session_id}{file_ext}"
    
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)
    
    session.audio_path = str(file_path)
    session.status = AnalysisStatus.TRANSCRIBING
    
    # Start analysis pipeline in background
    background_tasks.add_task(run_analysis_pipeline, session_id)
    
    return JSONResponse(
        content={
            "message": "Audio uploaded successfully. Analysis started.",
            "session_id": session_id,
        },
        status_code=202,
    )


@router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str) -> Session:
    """Get session details including analysis results."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


@router.get("/", response_model=list[SessionSummary])
async def list_sessions(
    provider_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[SessionSummary]:
    """List sessions with optional provider filter."""
    filtered = list(sessions.values())
    
    if provider_id:
        filtered = [s for s in filtered if s.provider_id == provider_id]
    
    # Sort by created_at descending
    filtered.sort(key=lambda s: s.created_at, reverse=True)
    
    # Paginate
    paginated = filtered[offset:offset + limit]
    
    # Convert to summaries
    summaries = []
    for s in paginated:
        quality_index = None
        if s.conversation_quality:
            quality_index = s.conversation_quality.quality_index
        
        engagement_summary = None
        if s.engagement_windows:
            engaged = sum(1 for w in s.engagement_windows if w.engagement_status.value == "engaged")
            total = len(s.engagement_windows)
            engagement_summary = f"{engaged}/{total} windows engaged"
        
        summaries.append(SessionSummary(
            id=s.id,
            provider_id=s.provider_id,
            created_at=s.created_at,
            duration_seconds=s.duration_seconds,
            status=s.status,
            quality_index=quality_index,
            engagement_summary=engagement_summary,
        ))
    
    return summaries


async def run_analysis_pipeline(session_id: str):
    """
    Run the full analysis pipeline:
    1. Transcribe with Plaud
    2. Analyze engagement with Interhuman AI
    3. Generate coaching with Crusoe
    """
    session = sessions.get(session_id)
    if not session or not session.audio_path:
        return
    
    try:
        # Step 1: Transcribe with Plaud
        session.status = AnalysisStatus.TRANSCRIBING
        plaud_client = get_plaud_client()
        
        try:
            transcript = await plaud_client.transcribe_audio(session.audio_path)
            session.transcript = transcript
        except Exception as e:
            print(f"Plaud transcription failed: {e}")
            # Continue without transcript - Interhuman can still analyze
        
        # Step 2: Analyze with Interhuman AI
        session.status = AnalysisStatus.ANALYZING
        interhuman_client = get_interhuman_client()
        
        analysis = await interhuman_client.analyze_audio(session.audio_path)
        session.duration_seconds = analysis.get("duration_seconds")
        session.engagement_windows = analysis.get("engagement_windows", [])
        session.conversation_quality = analysis.get("conversation_quality")
        
        # Step 3: Generate coaching with Crusoe
        session.status = AnalysisStatus.GENERATING_COACHING
        crusoe_client = get_crusoe_client()
        
        insights = await crusoe_client.generate_coaching_insights(
            transcript=session.transcript or [],
            engagement_windows=session.engagement_windows or [],
            conversation_quality=session.conversation_quality,
        )
        session.coaching_insights = insights
        
        session.status = AnalysisStatus.COMPLETED
        
    except Exception as e:
        session.status = AnalysisStatus.FAILED
        session.error_message = str(e)
        print(f"Analysis pipeline failed for session {session_id}: {e}")
