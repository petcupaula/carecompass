#!/usr/bin/env python3
"""
Test script for CareCompass backend.
Tests the analysis pipeline with a sample audio file.
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services import get_interhuman_client, get_crusoe_client
from app.models import TranscriptSegment


async def test_interhuman(audio_path: str):
    """Test Interhuman AI analysis."""
    print("\n=== Testing Interhuman AI ===")
    client = get_interhuman_client()
    
    try:
        result = await client.analyze_audio(audio_path)
        print(f"Duration: {result.get('duration_seconds')}s")
        print(f"Windows: {len(result.get('engagement_windows', []))}")
        
        if result.get('conversation_quality'):
            cq = result['conversation_quality']
            print(f"Quality Index: {cq.quality_index}")
            print(f"  Clarity: {cq.clarity}")
            print(f"  Rapport: {cq.rapport}")
        
        for w in result.get('engagement_windows', [])[:3]:
            print(f"  [{w.start_seconds:.1f}-{w.end_seconds:.1f}] {w.engagement_status.value}")
            for s in w.signals:
                print(f"    - {s.type}: {s.rationale}")
        
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None


async def test_crusoe(transcript: list, engagement_windows: list, quality):
    """Test Crusoe coaching generation."""
    print("\n=== Testing Crusoe Inference ===")
    client = get_crusoe_client()
    
    try:
        insights = await client.generate_coaching_insights(
            transcript=transcript,
            engagement_windows=engagement_windows,
            conversation_quality=quality,
        )
        
        print(f"Generated {len(insights)} coaching insights:")
        for i, insight in enumerate(insights, 1):
            print(f"\n{i}. {insight.title}")
            print(f"   Moment: {insight.specific_moment}")
            print(f"   Why: {insight.description}")
            print(f"   Action: {insight.suggested_action}")
        
        return insights
    except Exception as e:
        print(f"Error: {e}")
        return None


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_pipeline.py <audio_file>")
        print("Example: python test_pipeline.py sample.mp3")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    if not Path(audio_path).exists():
        print(f"File not found: {audio_path}")
        sys.exit(1)
    
    print(f"Testing with: {audio_path}")
    
    # Test Interhuman
    result = await test_interhuman(audio_path)
    
    if result:
        # Create mock transcript for testing
        mock_transcript = [
            TranscriptSegment(
                speaker_id="SPEAKER_0",
                start=0,
                end=30,
                text="Hello, I'm Dr. Smith. How are you feeling today?",
            ),
            TranscriptSegment(
                speaker_id="SPEAKER_1", 
                start=30,
                end=60,
                text="I've been having some headaches lately, especially in the morning.",
            ),
            TranscriptSegment(
                speaker_id="SPEAKER_0",
                start=60,
                end=120,
                text="I see. Let me explain what might be causing this. There are several factors we need to consider including your sleep patterns, stress levels, and hydration.",
            ),
        ]
        
        # Test Crusoe
        await test_crusoe(
            transcript=mock_transcript,
            engagement_windows=result.get('engagement_windows', []),
            quality=result.get('conversation_quality'),
        )
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
