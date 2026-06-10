# routers/render.py
# Endpoint: POST /render
# Takes a job_id + selected clip timestamps,
# cuts the actual MP4 files using FFmpeg,
# and returns download URLs.

import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.clipper   import cut_multiple_clips, ClipError
from utils.file_manager import downloads_path, clip_url

router = APIRouter()

# ── Request model ────────────────────────────────────────
class ClipRequest(BaseModel):
    start: float
    end:   float
    title: str = "clip"

class RenderRequest(BaseModel):
    job_id:      str
    clips:       list[ClipRequest]
    reframe:     bool = False
    captions:    bool = False
    originality: bool = False

@router.post("")
async def render_clips(req: RenderRequest, request: Request):
    """
    Cut real MP4 clips from the downloaded video.
    Returns download URLs for each clip.
    """

    # Find the downloaded video file for this job
    video_path = _find_video(req.job_id)
    if not video_path:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Video for job '{req.job_id}' not found. "
                "It may have expired (videos are kept for 1 hour). "
                "Please re-analyze the URL."
            )
        )

    if not req.clips:
        raise HTTPException(status_code=400, detail="No clips provided.")

    # Cut all the clips
    clip_dicts = [c.model_dump() for c in req.clips]

    try:
        results = cut_multiple_clips(
            video_path  = video_path,
            clips       = clip_dicts,
            reframe     = req.reframe,
            captions    = req.captions,
            originality = req.originality,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Render failed: {e}")

    # Build response — add download URL to each successful clip
    base_url = str(request.base_url).rstrip("/")
    for clip in results:
        if clip.get("status") == "ready" and clip.get("filename"):
            clip["download_url"] = f"{base_url}/clips/{clip['filename']}"

    return {
        "job_id": req.job_id,
        "clips":  results,
    }


def _find_video(job_id: str) -> str | None:
    """Find the downloaded video file for a given job ID."""
    for ext in ["mp4", "mkv", "webm", "mov", "avi"]:
        path = downloads_path(f"{job_id}.{ext}")
        if os.path.exists(path):
            return path
    return None
