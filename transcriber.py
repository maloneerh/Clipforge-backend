# services/transcriber.py
# Extracts audio from a video file and transcribes it
# using OpenAI Whisper (runs locally, no API cost).
# Returns timestamped segments so we know exactly when
# each word was spoken.

import os
import subprocess
import whisper
from config import DOWNLOADS_DIR, WHISPER_MODEL

# Load Whisper model once at startup (not on every request)
_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL}")
        _model = whisper.load_model(WHISPER_MODEL)
    return _model

class TranscribeError(Exception):
    pass

def extract_audio(video_path: str, job_id: str) -> str:
    """
    Extract audio from a video file into a WAV file.
    WAV works best with Whisper.
    Returns the path to the audio file.
    """
    audio_path = os.path.join(DOWNLOADS_DIR, f"{job_id}_audio.wav")

    cmd = [
        "ffmpeg",
        "-i", video_path,          # input video
        "-vn",                      # no video
        "-acodec", "pcm_s16le",    # raw WAV audio
        "-ar", "16000",             # 16kHz sample rate (Whisper standard)
        "-ac", "1",                 # mono channel
        "-y",                       # overwrite if exists
        audio_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise TranscribeError(f"Audio extraction failed: {result.stderr}")

    return audio_path


def transcribe(video_path: str, job_id: str) -> list[dict]:
    """
    Transcribe a video and return timestamped segments.

    Each segment looks like:
    {
        "start": 12.4,      ← seconds from start of video
        "end":   18.7,
        "text":  "And that's why I think this matters..."
    }
    """
    try:
        audio_path = extract_audio(video_path, job_id)
        model      = get_model()

        result = model.transcribe(
            audio_path,
            verbose=False,
            # word_timestamps gives us more granular data
            word_timestamps=False,
        )

        segments = [
            {
                "start": round(seg["start"], 2),
                "end":   round(seg["end"],   2),
                "text":  seg["text"].strip(),
            }
            for seg in result.get("segments", [])
            if seg.get("text", "").strip()
        ]

        # Clean up audio file after transcription
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return segments

    except TranscribeError:
        raise
    except Exception as e:
        raise TranscribeError(f"Transcription failed: {str(e)}")
