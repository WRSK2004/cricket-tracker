# Cricket Tracker 

## Overview

## Screenshots

## Video Demonstration

## Features

## Technologies Used
| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| Computer Vision | MediaPipe (Pose Landmarker), OpenCV |
| Database & Auth | Firebase Firestore, Firebase Auth |
| Storage | Firebase Cloud Storage |
| Video Processing | FFmpeg |
| Feedback Generation | Claude API (Anthropic) |

## Getting Started

### Requirements
- Python 3.13 and [uv](https://docs.astral.sh/uv/)
- FFmpeg (on your PATH, or set `FFMPEG_PATH` in `Backend/.env`)
- A Firebase project, with a service-account key saved as `Backend/serviceAccountKey.json`
- An Anthropic API key

### Backend
```bash
cd Backend
uv sync                              # install dependencies
cp .env.example .env                 # then fill in the values
uv run python scripts/download_models.py
uv run uvicorn app:app --reload --port 5000
```
Run the checks with `uv run ruff check .` and `uv run pytest`.

### Frontend
Serve the `Frontend` folder with any static server on port 5501 (for example VS Code's Live Server), then open `pages/Login/login.html`.

### Firebase rules
Security rules for Firestore and Storage are in `firestore.rules` and `storage.rules`. Deploy them with the Firebase CLI: `firebase deploy --only firestore,storage`.

## How It Was Built

## What I Learnt

## Future Improvements
