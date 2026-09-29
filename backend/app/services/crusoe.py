"""
Crusoe Inference API Client

Uses Crusoe's OpenAI-compatible API to generate coaching insights
from transcript and engagement analysis.
"""

from typing import Optional, List
from openai import AsyncOpenAI

from ..config import get_settings
from ..models import (
    CoachingInsight,
    TranscriptSegment,
    EngagementWindow,
    ConversationQuality,
)


COACHING_SYSTEM_PROMPT = """You are an expert healthcare communication coach. Your role is to help healthcare providers improve their patient communication skills by connecting WHAT they say with HOW they say it.

You will receive:
1. A transcript of a patient-provider conversation (what was said)
2. Engagement analysis with social signals showing HOW the conversation felt (engagement levels, detected signals like hesitation, confusion, agreement, etc.)
3. Conversation quality scores (clarity, authority, energy, rapport, learning)

Your task is to provide 2-3 specific, actionable coaching insights. Each insight MUST:
- Reference a specific moment with timestamp
- Connect the WORDS spoken (from transcript) with the SIGNALS detected (from engagement analysis)
- Explain the gap between intent and impact
- Provide a concrete alternative phrasing or technique

Example insight format:
"At 2:15, you explained the medication dosage ('Take two pills twice daily with food'). However, the engagement analysis detected CONFUSION and HESITATION signals immediately after. The patient likely needed a simpler explanation or a chance to ask questions. Try: 'Let me make sure this is clear - you'll take two pills in the morning with breakfast, and two more with dinner. Does that make sense?'"

Focus on moments where:
- Engagement dropped right after the provider spoke (words didn't land)
- Confusion or hesitation signals appeared (patient didn't understand)
- The provider missed opportunities to check understanding
- Medical jargon caused disengagement

Be specific about both the words AND the signals. Don't give generic advice."""


class CrusoeClient:
    """Client for Crusoe Inference API (OpenAI-compatible)."""
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.crusoe_api_key,
            base_url=settings.crusoe_base_url,
        )
        self.model = settings.crusoe_model
        
    async def generate_coaching_insights(
        self,
        transcript: List[TranscriptSegment],
        engagement_windows: List[EngagementWindow],
        conversation_quality: Optional[ConversationQuality],
    ) -> List[CoachingInsight]:
        """
        Generate coaching insights from analysis results.
        
        Args:
            transcript: Conversation transcript with speaker IDs
            engagement_windows: Engagement analysis per time window
            conversation_quality: Overall quality scores
            
        Returns:
            List of coaching insights
        """
        # Format transcript for the prompt
        transcript_text = self._format_transcript(transcript)
        engagement_text = self._format_engagement(engagement_windows)
        quality_text = self._format_quality(conversation_quality)
        
        user_prompt = f"""## Transcript
{transcript_text}

## Engagement Analysis
{engagement_text}

## Conversation Quality Scores
{quality_text}

Based on this analysis, provide 2-3 specific coaching insights to help this provider improve their patient communication. Format each insight as:

**Insight Title**
- Specific moment: [timestamp and what happened]
- Why it matters: [explanation]
- Suggested action: [concrete improvement]"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": COACHING_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        
        content = response.choices[0].message.content
        return self._parse_insights(content)
    
    def _format_transcript(self, transcript: List[TranscriptSegment]) -> str:
        """Format transcript for the prompt."""
        lines = []
        for seg in transcript:
            speaker = seg.speaker_id or "Unknown"
            timestamp = self._format_time(seg.start)
            lines.append(f"[{timestamp}] {speaker}: {seg.text}")
        return "\n".join(lines)
    
    def _format_engagement(self, windows: List[EngagementWindow]) -> str:
        """Format engagement analysis for the prompt, including social signals."""
        lines = []
        for w in windows:
            start = self._format_time(w.start_seconds)
            end = self._format_time(w.end_seconds)
            status = w.engagement_status.value
            
            # Include detailed signal information
            signal_details = []
            if w.signals:
                for s in w.signals:
                    signal_time = self._format_time(s.start)
                    detail = f"{s.type} at {signal_time}"
                    if s.probability:
                        detail += f" ({s.probability})"
                    if s.rationale:
                        detail += f" - {s.rationale}"
                    signal_details.append(detail)
            
            line = f"[{start}-{end}] {status.upper()}"
            if signal_details:
                line += f"\n  Signals: {'; '.join(signal_details)}"
            lines.append(line)
        return "\n".join(lines)
    
    def _format_quality(self, quality: Optional[ConversationQuality]) -> str:
        """Format quality scores for the prompt."""
        if not quality:
            return "Not available"
        
        return f"""- Overall Quality Index: {quality.quality_index:.1f}/100
- Clarity: {quality.clarity:.1f}/100
- Authority: {quality.authority:.1f}/100
- Energy: {quality.energy:.1f}/100
- Rapport: {quality.rapport:.1f}/100
- Learning: {quality.learning:.1f}/100"""
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def _parse_insights(self, content: str) -> List[CoachingInsight]:
        """Parse LLM response into structured insights."""
        insights = []
        
        if not content:
            return insights
        
        # Split by insight headers (marked with **)
        sections = content.split("**")
        
        i = 1
        while i < len(sections):
            title = sections[i].strip()
            if not title or title.startswith("-") or title.startswith("\n"):
                i += 1
                continue
                
            if i + 1 < len(sections):
                body = sections[i + 1]
                
                # Extract components from body
                specific_moment = None
                description = ""
                suggested_action = ""
                
                lines = body.strip().split("\n")
                
                for line in lines:
                    line = line.strip()
                    line_lower = line.lower()
                    
                    if line_lower.startswith("- moment:") or line_lower.startswith("- specific moment:"):
                        specific_moment = line.split(":", 1)[1].strip() if ":" in line else ""
                    elif line_lower.startswith("- why") or line_lower.startswith("- explanation"):
                        description = line.split(":", 1)[1].strip() if ":" in line else ""
                    elif line_lower.startswith("- action:") or line_lower.startswith("- suggested action:"):
                        suggested_action = line.split(":", 1)[1].strip() if ":" in line else ""
                    elif not specific_moment and not description and not suggested_action:
                        # First non-empty line might be description
                        if line and not line.startswith("-"):
                            description = line
                
                if title:
                    insights.append(CoachingInsight(
                        title=title,
                        description=description or "See suggested action.",
                        specific_moment=specific_moment,
                        suggested_action=suggested_action or "Review this moment in the recording.",
                    ))
            
            i += 2
        
        return insights


# Singleton instance
_client: Optional[CrusoeClient] = None


def get_crusoe_client() -> CrusoeClient:
    global _client
    if _client is None:
        _client = CrusoeClient()
    return _client
