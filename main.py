# main.py
# This is the entry point for the ClipForge backend.
# It creates the FastAPI app, connects all the routers,
# and sets up CORS so the frontend can talk to this server.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import ALLOWED_ORIGINS, CLIPS_DIR
from routers import analyze, render, download

# ── Create the app ───────────────────────────────────────
app = FastAPI(
    title="ClipForge API",
    description="AI-powered video clip extraction backend",
    version="1.0.0"
)

# ── CORS middleware ──────────────────────────────────────
# This allows the ClipForge HTML frontend (running in a browser)
# to make requests to this server, even if they're on different domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount static folder for serving finished clips ───────
# When a clip is ready, we serve it as a direct download link.
app.mount("/clips", StaticFiles(directory=CLIPS_DIR), name="clips")

# ── Connect routers ──────────────────────────────────────
# Each router handles a specific group of endpoints.
app.include_router(analyze.router,  prefix="/analyze",  tags=["Analyze"])
app.include_router(render.router,   prefix="/render",   tags=["Render"])
app.include_router(download.router, prefix="/download", tags=["Download"])

# ── Health check ─────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "ClipForge backend is running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
