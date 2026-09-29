"""
Plaud Transcription API Client

Uploads audio files and retrieves transcriptions with speaker diarization.
"""

import httpx
import asyncio
from typing import Optional, List
from pathlib import Path

from ..config import get_settings
from ..models import TranscriptSegment


class PlaudClient:
    """Client for Plaud Transcription API."""
    
    def __init__(self):
        settings = get_settings()
        self.client_id = settings.plaud_client_id
        self.api_key = settings.plaud_api_key
        self.base_url = settings.plaud_base_url
        
    async def transcribe_audio(self, audio_path: str) -> List[TranscriptSegment]:
        """
        Upload audio and get transcription with speaker diarization.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of transcript segments with speaker IDs and timestamps
        """
        file_path = Path(audio_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Step 1: Get presigned upload URL
            file_size = file_path.stat().st_size
            presign_response = await client.post(
                f"{self.base_url}/open/partner/files/upload/generate-presigned-urls",
                headers={
                    "X-Client-Id": self.client_id,
                    "X-Client-Api-Key": self.api_key,
                },
                json={
                    "file_name": file_path.name,
                    "file_size": file_size,
                    "content_type": self._get_content_type(file_path),
                },
            )
            presign_response.raise_for_status()
            presign_data = presign_response.json()
            
            # Step 2: Upload file to presigned URL
            upload_url = presign_data.get("upload_url")
            file_id = presign_data.get("file_id")
            
            with open(file_path, "rb") as f:
                upload_response = await client.put(
                    upload_url,
                    content=f.read(),
                    headers={"Content-Type": self._get_content_type(file_path)},
                )
                upload_response.raise_for_status()
            
            # Step 3: Complete upload
            complete_response = await client.post(
                f"{self.base_url}/open/partner/files/upload/complete-upload",
                headers={
                    "X-Client-Id": self.client_id,
                    "X-Client-Api-Key": self.api_key,
                },
                json={"file_id": file_id},
            )
            complete_response.raise_for_status()
            complete_data = complete_response.json()
            file_url = complete_data.get("file_url")
            
            # Step 4: Submit transcription job
            transcribe_response = await client.post(
                f"{self.base_url}/open/partner/ai/transcriptions/",
                headers={
                    "X-Client-Id": self.client_id,
                    "X-Client-Api-Key": self.api_key,
                },
                json={
                    "file_url": file_url,
                    "language": "auto",  # Auto-detect language
                    "speaker_diarization": True,
                },
            )
            transcribe_response.raise_for_status()
            job_data = transcribe_response.json()
            task_id = job_data.get("task_id")
            
            # Step 5: Poll for completion
            return await self._poll_transcription(client, task_id)
    
    async def _poll_transcription(
        self, 
        client: httpx.AsyncClient, 
        task_id: str,
    ) -> List[TranscriptSegment]:
        """Poll for transcription job completion."""
        max_attempts = 120  # 4 minutes max
        
        for _ in range(max_attempts):
            await asyncio.sleep(2)
            
            response = await client.get(
                f"{self.base_url}/open/partner/ai/transcriptions/{task_id}",
                headers={
                    "X-Client-Id": self.client_id,
                    "X-Client-Api-Key": self.api_key,
                },
            )
            response.raise_for_status()
            
            data = response.json()
            status = data.get("status")
            
            if status == "completed":
                return self._parse_transcript(data)
            elif status == "failed":
                error = data.get("error", "Unknown error")
                raise Exception(f"Transcription failed: {error}")
        
        raise TimeoutError("Transcription job timed out")
    
    def _parse_transcript(self, data: dict) -> List[TranscriptSegment]:
        """Parse transcription response into segments."""
        segments = []
        
        result = data.get("result", {})
        utterances = result.get("utterances", [])
        
        for u in utterances:
            segments.append(TranscriptSegment(
                speaker_id=u.get("speaker"),
                start=u.get("start", 0),
                end=u.get("end", 0),
                text=u.get("text", ""),
            ))
        
        return segments
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get content type for audio file."""
        suffix = file_path.suffix.lower()
        content_types = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
            ".flac": "audio/flac",
            ".webm": "audio/webm",
        }
        return content_types.get(suffix, "application/octet-stream")


# Singleton instance
_client: Optional[PlaudClient] = None


def get_plaud_client() -> PlaudClient:
    global _client
    if _client is None:
        _client = PlaudClient()
    return _client
