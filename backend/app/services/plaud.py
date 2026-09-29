"""
Plaud Transcription API Client

Uploads audio files and retrieves transcriptions with speaker diarization.

Auth flow:
- File Upload API: Bearer user_access_token
- Transcription API: X-Client-Id + X-Client-Api-Key
"""

import httpx
import asyncio
import hashlib
import base64
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
        self.secret_key = settings.plaud_secret_key
        self.base_url = "https://platform-us.plaud.ai/developer/api"
        self._user_token: Optional[str] = None
        
    async def _get_user_token(self, client: httpx.AsyncClient) -> str:
        """Get or refresh user access token."""
        if self._user_token:
            return self._user_token
        
        # Step 1: Get partner token using Basic auth
        credentials = f"{self.client_id}:{self.secret_key}"
        basic_auth = base64.b64encode(credentials.encode()).decode()
        
        print("[Plaud] Getting partner token...")
        partner_resp = await client.post(
            f"{self.base_url}/oauth/partner/access-token",
            headers={
                "Authorization": f"Basic {basic_auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        partner_resp.raise_for_status()
        partner_data = partner_resp.json()
        partner_token = partner_data["access_token"]
        
        # Step 2: Mint user access token
        print("[Plaud] Minting user access token...")
        user_resp = await client.post(
            f"{self.base_url}/open/partner/users/access-token",
            headers={
                "Authorization": f"Bearer {partner_token}",
                "Content-Type": "application/json",
            },
            json={"user_id": "carecompass-backend"},
        )
        user_resp.raise_for_status()
        user_data = user_resp.json()
        self._user_token = user_data["access_token"]
        
        return self._user_token
        
    async def transcribe_audio(self, audio_path: str) -> List[TranscriptSegment]:
        """
        Upload audio and get transcription with speaker diarization.
        """
        file_path = Path(audio_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Get user token for file upload
            user_token = await self._get_user_token(client)
            
            # Auth headers for different APIs
            upload_headers = {"Authorization": f"Bearer {user_token}"}
            transcription_headers = {
                "X-Client-Id": self.client_id,
                "X-Client-Api-Key": self.api_key,
            }
            
            # Read file
            file_data = file_path.read_bytes()
            file_size = len(file_data)
            file_type = file_path.suffix.lstrip('.').lower()
            file_md5 = hashlib.md5(file_data).hexdigest()
            
            print(f"[Plaud] Step 1: generate-presigned-urls (size={file_size}, type={file_type})")
            
            # Step 1: Get presigned upload URLs
            presign_response = await client.post(
                f"{self.base_url}/open/partner/files/upload/generate-presigned-urls",
                headers={**upload_headers, "Content-Type": "application/json"},
                json={
                    "filesize": file_size,
                    "filetype": file_type,
                },
            )
            presign_response.raise_for_status()
            presign_data = presign_response.json()
            
            print(f"[Plaud] Presign response: {presign_data}")
            
            # Response may have data wrapper or be at root level
            data = presign_data.get("data", presign_data)
            
            file_id = data["FileId"]
            upload_id = data["UploadId"]
            parts = data["Parts"]
            chunk_size = data.get("ChunkSize", 5 * 1024 * 1024)
            
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
                headers={**upload_headers, "Content-Type": "application/json"},
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
            
            # Response may have data wrapper or be at root level
            complete_result = complete_data.get("data", complete_data)
            download_url = complete_result["DownloadUrl"]
            
            print(f"[Plaud] Upload complete, got download URL")
            
            # Step 4: Submit transcription job (uses different auth)
            print(f"[Plaud] Step 4: Submit transcription task")
            
            transcribe_response = await client.post(
                f"{self.base_url}/open/partner/ai/transcriptions/",
                headers={**transcription_headers, "Content-Type": "application/json"},
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
            return await self._poll_transcription(client, transcription_id, transcription_headers)
    
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
