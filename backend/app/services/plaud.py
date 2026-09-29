"""
Plaud Transcription API Client

Uploads audio files and retrieves transcriptions with speaker diarization.
"""

import httpx
import asyncio
import hashlib
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
        # Transcription API uses platform-us.plaud.ai (not /developer/api)
        self.base_url = "https://platform-us.plaud.ai"
        
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
        
        # Auth headers for transcription API
        auth_headers = {
            "X-Client-Id": self.client_id,
            "X-Client-Api-Key": self.api_key,
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Step 1: Get presigned upload URLs
            file_data = file_path.read_bytes()
            file_size = len(file_data)
            file_type = file_path.suffix.lstrip('.').lower()
            file_md5 = hashlib.md5(file_data).hexdigest()
            
            print(f"[Plaud] Step 1: generate-presigned-urls (size={file_size}, type={file_type})")
            
            presign_response = await client.post(
                f"{self.base_url}/open/partner/files/upload/generate-presigned-urls",
                headers=auth_headers,
                json={
                    "filesize": file_size,
                    "filetype": file_type,
                },
            )
            presign_response.raise_for_status()
            presign_data = presign_response.json()
            
            file_id = presign_data["data"]["FileId"]
            upload_id = presign_data["data"]["UploadId"]
            parts = presign_data["data"]["Parts"]
            chunk_size = presign_data["data"].get("ChunkSize", 5 * 1024 * 1024)
            
            print(f"[Plaud] Got {len(parts)} part URLs, fileId={file_id}")
            
            # Step 2: Upload parts to S3
            part_results = []
            for i, part in enumerate(parts):
                start = i * chunk_size
                end = min(start + chunk_size, file_size)
                chunk = file_data[start:end]
                
                print(f"[Plaud] Step 2: PUT part {part['PartNumber']}/{len(parts)} ({len(chunk)} bytes)")
                
                upload_response = await client.put(
                    part["PresignedUrl"],
                    content=chunk,
                )
                upload_response.raise_for_status()
                etag = upload_response.headers.get("ETag", "").strip('"')
                part_results.append({
                    "PartNumber": part["PartNumber"],
                    "ETag": etag,
                })
            
            # Step 3: Complete upload
            print(f"[Plaud] Step 3: complete-upload ({len(part_results)} parts)")
            
            complete_response = await client.post(
                f"{self.base_url}/open/partner/files/upload/complete-upload",
                headers=auth_headers,
                json={
                    "file_id": file_id,
                    "upload_id": upload_id,
                    "part_list": part_results,
                    "filetype": file_type,
                    "file_md5": file_md5,
                },
            )
            complete_response.raise_for_status()
            complete_data = complete_response.json()
            download_url = complete_data["data"]["DownloadUrl"]
            
            print(f"[Plaud] Upload complete, got download URL")
            
            # Step 4: Submit transcription job
            print(f"[Plaud] Step 4: Submit transcription task")
            
            transcribe_response = await client.post(
                f"{self.base_url}/open/partner/ai/transcriptions/",
                headers=auth_headers,
                json={
                    "file_url": download_url,
                    "params": {
                        "transcribe": {"language": "auto"},
                        "diarization": {"enabled": True},
                    },
                },
            )
            transcribe_response.raise_for_status()
            job_data = transcribe_response.json()
            transcription_id = job_data.get("transcription_id") or job_data.get("data", {}).get("task_id", "")
            
            print(f"[Plaud] Transcription submitted: id={transcription_id}")
            
            # Step 5: Poll for completion
            return await self._poll_transcription(client, transcription_id, auth_headers)
    
    async def _poll_transcription(
        self, 
        client: httpx.AsyncClient, 
        transcription_id: str,
        auth_headers: dict,
    ) -> List[TranscriptSegment]:
        """Poll for transcription job completion."""
        max_attempts = 120  # 4 minutes max
        
        for attempt in range(max_attempts):
            await asyncio.sleep(2)
            
            response = await client.get(
                f"{self.base_url}/open/partner/ai/transcriptions/{transcription_id}",
                headers=auth_headers,
            )
            response.raise_for_status()
            
            data = response.json()
            status = data.get("status", "").upper()
            
            print(f"[Plaud] Poll {attempt+1}/{max_attempts}: status={status}")
            
            if status == "SUCCESS":
                return self._parse_transcript(data)
            elif status in ("FAILURE", "REVOKED"):
                error = data.get("message", "Unknown error")
                raise Exception(f"Transcription failed: {error}")
            # PENDING, RECEIVED, STARTED, PROGRESS - keep polling
        
        raise TimeoutError("Transcription job timed out")
    
    def _parse_transcript(self, data: dict) -> List[TranscriptSegment]:
        """Parse transcription response into segments."""
        segments = []
        
        results = data.get("data", {}).get("results", [])
        
        for r in results:
            segments.append(TranscriptSegment(
                speaker_id=r.get("speaker_id"),
                start=r.get("start", 0),
                end=r.get("end", 0),
                text=r.get("text", ""),
            ))
        
        return segments


# Singleton instance
_client: Optional[PlaudClient] = None


def get_plaud_client() -> PlaudClient:
    global _client
    if _client is None:
        _client = PlaudClient()
    return _client
