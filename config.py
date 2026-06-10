# config.py
# Central settings for ClipForge backend.
# All sensitive values (like API keys) come from environment variables,
# never hardcoded here.

import os
from dotenv import load_dotenv

load_dotenv()  # reads from .env file if present (for local dev)

# ── API Keys ─────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── Paths ────────────────────────────────────────────────
BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR          = os.path.join(BASE_DIR, "temp")
DOWNLOADS_DIR     = os.path.join(TEMP_DIR, "downloads")   # raw downloaded videos
CLIPS_DIR         = os.path.join(TEMP_DIR, "clips")       # finished cut clips

# Make sure folders exist on startup
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)

# ── Limits ───────────────────────────────────────────────
MAX_VIDEO_DURATION_SECONDS = 3600   # 1 hour max input video
MAX_CLIPS_PER_REQUEST      = 15     # cap how many clips Claude can suggest
CLIP_EXPIRY_SECONDS        = 3600   # delete clips from server after 1 hour

# ── Whisper model ────────────────────────────────────────
# "base" is fast and good enough for clip detection.
# Options: tiny, base, small, medium, large
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# ── CORS ─────────────────────────────────────────────────
# In production, replace "*" with your actual frontend domain.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
