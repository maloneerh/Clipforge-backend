# routers/download.py
# Endpoint: GET /download/{clip_id}
# Serves a finished clip as a file download.
# (The /clips/ static mount in main.py also serves files directly —
#  this router adds a forced-download header for convenience.)

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from utils.file_manager import clips_path

router = APIRouter()

@router.get("/{clip_id}")
async def download_clip(clip_id: str):
    """
    Download a rendered clip by its ID.
    Forces the browser to download the file rather than play it inline.
    """
    # Sanitize — only allow alphanumeric IDs, no path traversal
    if not clip_id.isalnum():
        raise HTTPException(status_code=400, detail="Invalid clip ID.")

    filepath = clips_path(f"{clip_id}.mp4")

    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail="Clip not found. It may have expired (clips are kept for 1 hour)."
        )

    return FileResponse(
        path              = filepath,
        media_type        = "video/mp4",
        filename          = f"clipforge_{clip_id}.mp4",
        headers           = {"Content-Disposition": f'attachment; filename="clipforge_{clip_id}.mp4"'}
    )
