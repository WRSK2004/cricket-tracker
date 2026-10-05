# ============================================================
# settings.py
# All backend configuration, read from environment variables
# (or Backend/.env during local development).
# See .env.example for the full list.
# ============================================================

# ---- Imports ----
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")


# ---- Settings ----
@dataclass(frozen=True)
class Settings:
    # Browser origins allowed to call the API (the frontend's address)
    allowed_origins: tuple
    # Firebase Storage bucket for anonymised videos and frames
    storage_bucket: str
    # Path to a service-account key file. Leave unset in production, where the
    # hosting platform's own service account is used instead.
    firebase_credentials: str | None
    # Largest video upload accepted, in megabytes
    max_upload_mb: int
    # How long links to private videos/frames stay valid, in minutes
    signed_url_minutes: int
    # FFmpeg executable (name on PATH, or a full path)
    ffmpeg_path: str


@lru_cache
def get_settings():
    default_key = BACKEND_DIR / "serviceAccountKey.json"
    origins = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:5501,http://localhost:5501")
    return Settings(
        allowed_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
        storage_bucket=os.getenv("STORAGE_BUCKET", "dissertation-4cc1f.firebasestorage.app"),
        firebase_credentials=os.getenv("FIREBASE_CREDENTIALS") or (str(default_key) if default_key.exists() else None),
        max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "100")),
        signed_url_minutes=int(os.getenv("SIGNED_URL_MINUTES", "60")),
        ffmpeg_path=os.getenv("FFMPEG_PATH", "ffmpeg"),
    )
