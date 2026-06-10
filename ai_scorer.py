# services/ai_scorer.py
# Sends the video transcript to Claude and asks it to
# identify the best moments to clip, scored for virality.

import json
import anthropic
from config import ANTHROPIC_API_KEY, MAX_CLIPS_PER_REQUEST

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class ScoringError(Exception):
    pass

STYLE_DESCRIPTIONS = {
    "viral":       "moments most likely to go viral — surprising, funny, shocking, or highly shareable",
    "hooks":       "moments with the strongest opening hooks that grab attention in the first 3 seconds",
    "emotional":   "emotionally powerful moments — inspiring, moving, or deeply relatable",
    "debate":      "controversial or debate-triggering statements that spark comments and arguments",
    "educational": "key insights, tips, or 'aha' moments that deliver clear value",
}

def score_clips(
    segments:    list[dict],
    title:       str,
    platform:    str,
    clip_count:  int,
    clip_style:  str,
    min_length:  int,
    max_length:  int,
) -> list[dict]:
    """
    Send transcript segments to Claude.
    Returns a list of clip suggestions with timestamps and scores.
    """
    if not segments:
        raise ScoringError("No transcript segments to analyze.")

    clip_count  = min(clip_count, MAX_CLIPS_PER_REQUEST)
    style_desc  = STYLE_DESCRIPTIONS.get(clip_style, STYLE_DESCRIPTIONS["viral"])

    # Build the transcript text with timestamps
    transcript_text = "\n".join(
        f"[{seg['start']}s - {seg['end']}s] {seg['text']}"
        for seg in segments
    )

    prompt = f"""You are ClipForge's AI engine. Analyze this video transcript and identify the {clip_count} best moments to clip.

Video Title: "{title}"
Platform: {platform}
Clip Style: {style_desc}
Clip Length: {min_length}–{max_length} seconds each

TRANSCRIPT (with timestamps in seconds):
{transcript_text}

Instructions:
- Find exactly {clip_count} non-overlapping clips
- Each clip must be {min_length}–{max_length} seconds long
- Use the actual timestamps from the transcript
- Expand start/end slightly to include natural sentence boundaries

For each clip return:
- title: punchy clip title max 8 words
- start: start time in seconds (float)
- end: end time in seconds (float)
- hook: one sentence — what happens in this clip
- reason: why this fits the "{clip_style}" style
- viral_potential: 0–100
- hook_strength: 0–100
- emotional_impact: 0–100
- tags: array of 2–3 tags from [hook, viral, emotional, debate, insight, funny, shocking, relatable, inspiring]

Respond ONLY with a valid JSON array. No markdown, no backticks, no explanation."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()

        clips = json.loads(raw)

        if not isinstance(clips, list):
            raise ScoringError("Claude returned unexpected format.")

        # Sort by viral_potential descending
        clips.sort(key=lambda c: c.get("viral_potential", 0), reverse=True)

        return clips

    except json.JSONDecodeError as e:
        raise ScoringError(f"Could not parse Claude's response: {e}")
    except anthropic.APIError as e:
        raise ScoringError(f"Claude API error: {e}")
    except Exception as e:
        raise ScoringError(f"Scoring failed: {e}")
