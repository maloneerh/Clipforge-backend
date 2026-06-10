# utils/file_manager.py
# Handles creating unique file IDs, tracking temp files,
# and cleaning up old clips so the server doesn't fill up.

import os
import uuid
import time
import glob
from config import DOWNLOADS_DIR, CLIPS_DIR, CLIP_EXPIRY_SECONDS

def new_job_id() -> str:
    """Generate a unique ID for each processing job."""
    return str(uuid.uuid4()).replace("-", "")[:16]

def downloads_path(filename: str) -> str:
    """Full path for a file in the downloads temp folder."""
    return os.path.join(DOWNLOADS_DIR, filename)

def clips_path(filename: str) -> str:
    """Full path for a file in the clips output folder."""
    return os.path.join(CLIPS_DIR, filename)

def clip_url(request_base_url: str, filename: str) -> str:
    """Build the public download URL for a finished clip."""
    base = str(request_base_url).rstrip("/")
    return f"{base}/clips/{filename}"

def cleanup_old_files():
    """
    Delete temp files older than CLIP_EXPIRY_SECONDS.
    Call this periodically so the server doesn't run out of disk space.
    """
    now = time.time()
    for folder in [DOWNLOADS_DIR, CLIPS_DIR]:
        for filepath in glob.glob(os.path.join(folder, "*")):
            try:
                if os.path.isfile(filepath):
                    age = now - os.path.getmtime(filepath)
                    if age > CLIP_EXPIRY_SECONDS:
                        os.remove(filepath)
            except Exception:
                pass  # if we can't delete it, skip silently

def delete_file(filepath: str):
    """Delete a single file safely."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass
