# =======================================================================
# download_models.py
# Downloads the MediaPipe model files the backend needs into Backend/models/.
# Model files are not committed to git; run this once after cloning:
#     python scripts/download_models.py
# =======================================================================

# ---- Imports ----
import sys
import urllib.request
from pathlib import Path

# ---- Model Sources (official MediaPipe model storage) ----
MODELS = {
    "pose_landmarker_full.task": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_full/float16/latest/pose_landmarker_full.task"
    ),
}

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


# ---- Download Missing Models ----
def main():
    MODELS_DIR.mkdir(exist_ok=True)
    for filename, url in MODELS.items():
        destination = MODELS_DIR / filename
        if destination.exists():
            print(f"{filename} already present, skipping.")
            continue
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, destination)
        print(f"Saved to {destination} ({destination.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    sys.exit(main())
