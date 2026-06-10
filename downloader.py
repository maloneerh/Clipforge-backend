# services/downloader.py
# Downloads videos from YouTube, TikTok, and Instagram
# using yt-dlp — the same tool that powers most video downloaders.

import os
import yt_dlp
from config import DOWNLOADS_DIR, MAX_VIDEO_DURATION_SECONDS
from utils.file_manager import new_job_id

class DownloadError(Exception):
    """Raised when a video can't be downloaded."""
    pass

def download_video(url: str) -> dict:
    """
    Download a video from a URL.
    Returns a dict with: job_id, filepath, title, duration, platform
    Raises DownloadError if something goes wrong.
    """
    job_id = new_job_id()
    output_template = os.path.join(DOWNLOADS_DIR, f"{job_id}.%(ext)s")

    ydl_opts = {
        # Download best quality video+audio merged, prefer mp4
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        # Don't download playlists — single video only
        "noplaylist": True,
        # Abort if video is longer than our limit
        "match_filter": yt_dlp.utils.match_filter_func(
            f"duration <= {MAX_VIDEO_DURATION_SECONDS}"
        ),
        # Merge video+audio into mp4
        "merge_output_format": "mp4",
        # Add cookies for platforms that need login (optional, helps TikTok)
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First extract info without downloading to validate
            info = ydl.extract_info(url, download=False)

            if not info:
                raise DownloadError("Could not read video info from this URL.")

            duration = info.get("duration", 0)
            if duration and duration > MAX_VIDEO_DURATION_SECONDS:
                raise DownloadError(
                    f"Video is {duration//60} minutes long. "
                    f"Maximum allowed is {MAX_VIDEO_DURATION_SECONDS//60} minutes."
                )

            title    = info.get("title", "Untitled Video")
            platform = info.get("extractor_key", "unknown").lower()

            # Now actually download
            ydl.download([url])

        # Find the downloaded file (yt-dlp picks the extension)
        filepath = _find_downloaded_file(job_id)
        if not filepath:
            raise DownloadError("Download finished but file not found.")

        return {
            "job_id":   job_id,
            "filepath": filepath,
            "title":    title,
            "duration": duration,
            "platform": platform,
        }

    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(f"Download failed: {str(e)}")
    except DownloadError:
        raise
    except Exception as e:
        raise DownloadError(f"Unexpected error: {str(e)}")


def _find_downloaded_file(job_id: str) -> str | None:
    """Find the file yt-dlp saved for this job (any extension)."""
    for ext in ["mp4", "mkv", "webm", "mov", "avi"]:
        path = os.path.join(DOWNLOADS_DIR, f"{job_id}.{ext}")
        if os.path.exists(path):
            return path
    return None
