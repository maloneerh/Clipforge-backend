# routers/analyze.py
# Endpoint: POST /analyze
# Takes a video URL, downloads it, transcribes it,
# and returns AI-scored clip suggestions.
# This is the "find the best moments" step.

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from services.downloader  import download_video,  DownloadError
from services.transcriber import transcribe,       TranscribeError
from services.ai_scorer   import score_clips,      ScoringError
from utils.file_manager   import cleanup_old_files, delete_file

router = APIRouter()

# ── Request model ────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    url:        str
    clip_count: int   = 5
    clip_style: str   = "viral"
    min_length: int   = 30
    max_length: int   = 90

# ── Response model ───────────────────────────────────────
class AnalyzeResponse(BaseModel):
    job_id:    str
    title:     str
    duration:  float
    platform:  str
    clips:     list[dict]

@router.post("", response_model=AnalyzeResponse)
async def analyze_video(req: AnalyzeRequest, background: BackgroundTasks):
    """
    Full pipeline: URL → download → transcribe → AI score → return clip list.
    The clips are suggestions at this point — no video cutting yet.
    """

    # ── 1. Download the video ────────────────────────────
    try:
        video_info = download_video(req.url)
    except DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))

    video_path = video_info["filepath"]
    job_id     = video_info["job_id"]

    # ── 2. Transcribe ────────────────────────────────────
    try:
        segments = transcribe(video_path, job_id)
    except TranscribeError as e:
        delete_file(video_path)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    # ── 3. AI scoring ────────────────────────────────────
    try:
        clips = score_clips(
            segments   = segments,
            title      = video_info["title"],
            platform   = video_info["platform"],
            clip_count = req.clip_count,
            clip_style = req.clip_style,
            min_length = req.min_length,
            max_length = req.max_length,
        )
    except ScoringError as e:
        delete_file(video_path)
        raise HTTPException(status_code=500, detail=f"AI scoring failed: {e}")

    # ── Clean up old files in background ─────────────────
    # We keep the downloaded video so /render can use it.
    # Old files get cleaned up automatically.
    background.add_task(cleanup_old_files)

    return AnalyzeResponse(
        job_id   = job_id,
        title    = video_info["title"],
        duration = video_info["duration"],
        platform = video_info["platform"],
        clips    = clips,
    )
