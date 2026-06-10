# services/clipper.py
# The core of ClipForge — uses FFmpeg to cut the video
# at exact timestamps and apply all the visual transforms.

import os
import subprocess
from config import CLIPS_DIR
from utils.file_manager import new_job_id

class ClipError(Exception):
    pass

def cut_clip(
    video_path:  str,
    start:       float,
    end:         float,
    job_id:      str = None,
    reframe:     bool = False,
    captions:    bool = False,
    originality: bool = False,
) -> str:
    """
    Cut a single clip from a video between start and end seconds.
    Applies optional transforms.
    Returns the path to the output clip file.
    """
    if job_id is None:
        job_id = new_job_id()

    duration    = end - start
    output_file = os.path.join(CLIPS_DIR, f"{job_id}.mp4")

    # ── Build FFmpeg filter chain ────────────────────────
    filters = []

    if reframe:
        # Crop to 9:16 vertical (center crop)
        # This takes the center portion of the frame and scales to 1080x1920
        filters.append(
            "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,"
            "scale=1080:1920"
        )

    if originality:
        # Subtle transforms that make the clip look "fresh" to platform algorithms:
        # slight zoom in, minor color grade shift
        zoom_filter = "zoompan=z='min(zoom+0.001,1.05)':d=1:fps=30" if not reframe else None
        color_filter = "eq=contrast=1.05:brightness=0.02:saturation=1.1"
        if zoom_filter:
            filters.append(zoom_filter)
        filters.append(color_filter)

    # Build the complete FFmpeg command
    cmd = [
        "ffmpeg",
        "-ss",  str(start),         # seek to start time (fast seek before -i)
        "-i",   video_path,          # input file
        "-t",   str(duration),       # duration of clip
        "-c:v", "libx264",           # H.264 video codec (widely compatible)
        "-c:a", "aac",               # AAC audio codec
        "-b:a", "192k",              # audio bitrate
        "-movflags", "+faststart",   # optimize for web streaming
        "-y",                        # overwrite output if exists
    ]

    # Add video filters if any
    if filters:
        cmd.extend(["-vf", ",".join(filters)])
    else:
        # If no filters, copy video stream (faster)
        cmd[cmd.index("-c:v")] = "-c:v"
        cmd[cmd.index("libx264")] = "libx264"

    cmd.append(output_file)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise ClipError(f"FFmpeg failed: {result.stderr[-500:]}")  # last 500 chars of error

    if not os.path.exists(output_file):
        raise ClipError("Clip file was not created.")

    return output_file


def cut_multiple_clips(
    video_path:  str,
    clips:       list[dict],
    reframe:     bool = False,
    captions:    bool = False,
    originality: bool = False,
) -> list[dict]:
    """
    Cut multiple clips from the same video.
    clips is a list of dicts with 'start', 'end', and 'title'.
    Returns the same list with 'output_file' and 'filename' added to each.
    """
    results = []

    for i, clip in enumerate(clips):
        clip_job_id = new_job_id()
        try:
            output_file = cut_clip(
                video_path   = video_path,
                start        = float(clip["start"]),
                end          = float(clip["end"]),
                job_id       = clip_job_id,
                reframe      = reframe,
                captions     = captions,
                originality  = originality,
            )
            results.append({
                **clip,
                "clip_id":     clip_job_id,
                "output_file": output_file,
                "filename":    f"{clip_job_id}.mp4",
                "status":      "ready",
            })
        except ClipError as e:
            results.append({
                **clip,
                "clip_id": clip_job_id,
                "status":  "error",
                "error":   str(e),
            })

    return results
