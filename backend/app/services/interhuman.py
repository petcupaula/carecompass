"""
Interhuman AI API Client

Analyzes audio/video for engagement signals and conversation quality.
Uses the v2 upload/analyze endpoint with inter-2-audio model.
"""

import httpx
import asyncio
from typing import Optional, List
from pathlib import Path

from ..config import get_settings
from ..models import (
    EngagementWindow,
    EngagementLevel,
    Signal,
    ConversationQuality,
)


class InterhumanClient:
    """Client for Interhuman AI audio analysis API."""
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.interhuman_api_key
        self.base_url = settings.interhuman_base_url
        
    async def analyze_audio(
        self,
        audio_path: str,
        wait_seconds: int = 120,
    ) -> dict:
        """
        Submit audio for analysis and wait for results.
        
        Args:
            audio_path: Path to audio file (wav, mp3, m4a, etc.)
            wait_seconds: How long to wait for job completion
            
        Returns:
            Dict with engagement_windows and conversation_quality
        """
        file_path = Path(audio_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Determine content type
        suffix = file_path.suffix.lower()
        content_types = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
            ".flac": "audio/flac",
            ".webm": "audio/webm",
        }
        content_type = content_types.get(suffix, "application/octet-stream")
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            # Submit the job
            with open(file_path, "rb") as f:
                files = {
                    "file": (file_path.name, f, content_type),
                }
                data = {
                    "model": "inter-2-audio",
                    "wait_seconds": str(wait_seconds),
                    "include[]": [
                        "conversation_quality_overall",
                        "conversation_quality_timeline",
                    ],
                }
                
                response = await client.post(
                    f"{self.base_url}/v2/upload/analyze",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                    data=data,
                )
                
            if response.status_code == 200:
                # Job completed within wait_seconds
                return self._parse_response(response.json())
            elif response.status_code == 202:
                # Job queued, need to poll
                job_data = response.json()
                return await self._poll_job(client, job_data)
            else:
                response.raise_for_status()
    
    async def _poll_job(self, client: httpx.AsyncClient, job_data: dict) -> dict:
        """Poll for job completion."""
        job_id = job_data["job_id"]
        status_url = f"{self.base_url}/v2/upload/jobs/{job_id}"
        
        max_attempts = 60
        for _ in range(max_attempts):
            await asyncio.sleep(2)
            
            response = await client.get(
                status_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            
            data = response.json()
            status = data.get("status")
            
            if status == "completed":
                return self._parse_response(data)
            elif status == "failed":
                error = data.get("error", {})
                raise Exception(f"Analysis failed: {error.get('message', 'Unknown error')}")
        
        raise TimeoutError("Analysis job timed out")
    
    def _parse_response(self, data: dict) -> dict:
        """Parse the API response into our models."""
        result = data.get("result", {})
        
        # Parse engagement windows
        windows = []
        for w in result.get("windows", []):
            signals = [
                Signal(
                    type=s["type"],
                    start=s["start"],
                    end=s["end"],
                    probability=s.get("probability"),
                    rationale=s.get("rationale"),
                    modality=s.get("modality", []),
                )
                for s in w.get("signals", [])
            ]
            
            windows.append(EngagementWindow(
                index=w["index"],
                start_seconds=w["start_seconds"],
                end_seconds=w["end_seconds"],
                engagement_status=EngagementLevel(w["engagement_status"]),
                signals=signals,
            ))
        
        # Parse conversation quality
        cq_data = result.get("conversation_quality", {})
        overall = cq_data.get("overall")
        conversation_quality = None
        if overall:
            conversation_quality = ConversationQuality(
                quality_index=overall["quality_index"],
                clarity=overall["clarity"],
                authority=overall["authority"],
                energy=overall["energy"],
                rapport=overall["rapport"],
                learning=overall["learning"],
            )
        
        return {
            "duration_seconds": result.get("duration_seconds"),
            "engagement_windows": windows,
            "conversation_quality": conversation_quality,
        }


# Singleton instance
_client: Optional[InterhumanClient] = None


def get_interhuman_client() -> InterhumanClient:
    global _client
    if _client is None:
        _client = InterhumanClient()
    return _client
