# =======================================================================
# app.py
# FastAPI REST API server. Run locally with:
#     uvicorn app:app --reload --port 5000
#
# Endpoints (all require a signed-in user):
# POST /analyse       - Accepts a stance video and the batting hand, runs the pose
#                       estimation and stance analysis pipeline, stores the
#                       anonymised results privately and returns the feedback.
# POST /health        - Accepts user health data and returns calculated BMI,
#                       BMR, TDEE, macronutrient targets and calorie targets.
# POST /media/urls    - Returns short-lived links to the user's own private
#                       videos/frames (used by "Previous Sessions").
# POST /media/delete  - Deletes the user's own private videos/frames.
# =======================================================================

# ---- Imports ----
import logging
import os
import subprocess
import tempfile
import uuid
from datetime import timedelta
from typing import Literal

import cv2
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from firebase_admin import firestore
from pydantic import BaseModel, Field

from auth import get_current_user
from core.anonymise import anonymise_video
from core.feedback import generate_feedback
from core.frame_selector import VideoTooShortError, select_best_frame
from core.health_metrics import calculate_health_metrics
from core.pose_extractor import extract_video_landmarks
from core.stance_rules import analyse_stance
from firebase_admin_setup import get_bucket, get_db
from settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- Analysis Window (seconds into the video used to pick the best frame) ----
BEST_FRAME_WINDOW = (1, 2)
UPLOAD_CHUNK_BYTES = 1024 * 1024
FFMPEG_TIMEOUT_SECONDS = 120
MAX_MEDIA_PATHS = 50

# ---- FastAPI App Initialisation ----
app = FastAPI(title="Cricket Tracker API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().allowed_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---- Error Responses ----
# Errors are returned as {"error": "<message>"} so the frontend can show the message.
# Unexpected errors are logged in full but only a generic message is sent to the user.
@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    problems = "; ".join(f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in exc.errors())
    return JSONResponse({"error": f"Invalid input - {problems}"}, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse({"error": "Something went wrong. Please try again."}, status_code=500)


# ==== HELPERS ====

# ---- Save Upload to a Temporary File (with size limit) ----
def save_upload(upload: UploadFile, destination: str, max_bytes: int):
    written = 0
    with open(destination, "wb") as out:
        while chunk := upload.file.read(UPLOAD_CHUNK_BYTES):
            written += len(chunk)
            if written > max_bytes:
                raise HTTPException(
                    status.HTTP_413_CONTENT_TOO_LARGE,
                    f"Video is too large. The maximum size is {max_bytes // (1024 * 1024)} MB.",
                )
            out.write(chunk)


# ---- Run FFmpeg ----
def run_ffmpeg(args):
    command = [get_settings().ffmpeg_path, "-y", "-loglevel", "error", *args]
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=FFMPEG_TIMEOUT_SECONDS)
    except subprocess.CalledProcessError as e:
        logger.error("FFmpeg failed: %s", e.stderr.decode(errors="replace"))
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Could not read this video. Please try a different file."
        ) from None


# ---- Upload a File to Private Storage ----
def upload_private(local_path, storage_path, content_type):
    blob = get_bucket().blob(storage_path)
    blob.upload_from_filename(local_path, content_type=content_type)


# ---- Short-Lived Link to a Private File ----
def signed_url(storage_path):
    blob = get_bucket().blob(storage_path)
    return blob.generate_signed_url(
        version="v4", expiration=timedelta(minutes=get_settings().signed_url_minutes), method="GET"
    )


# ---- Storage Paths Belonging to a User ----
def user_media_prefix(uid):
    return f"users/{uid}/"


def check_owned_paths(paths, uid):
    prefix = user_media_prefix(uid)
    for path in paths:
        if not path.startswith(prefix) or ".." in path:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only access your own files.")


# ==== ENDPOINT: /analyse ====
@app.post("/analyse")
def analyse(
    video: UploadFile = File(...),
    batting_hand: Literal["left", "right"] = Form(...),
    uid: str = Depends(get_current_user),
):
    # A video file undergoes the following pipeline:
    # 1: Save the upload (with a size limit)
    # 2: Convert to MP4 with H.264 (also applies phone rotation and limits resolution)
    # 3: Extract pose landmarks from every frame
    # 4: Select the best frame within the analysis window
    # 5: Analyse the stance and generate feedback
    # 6: Render the anonymised video and best frame
    # 7: Re-encode the anonymised video for browser playback
    # 8: Upload both to private storage
    # 9: Store the analysis results in Firestore
    # 10: Return feedback, results and short-lived links
    # Temporary files are always cleaned up.
    settings = get_settings()
    if not (video.content_type or "").startswith("video/"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Please upload a video file.")

    with tempfile.TemporaryDirectory() as work_dir:
        input_path = os.path.join(work_dir, "input")
        converted_path = os.path.join(work_dir, "converted.mp4")
        anonymised_raw_path = os.path.join(work_dir, "anonymised_raw.mp4")
        anonymised_path = os.path.join(work_dir, "anonymised.mp4")
        frame_path = os.path.join(work_dir, "best_frame.jpg")

        # ---- 1: Save Upload ----
        save_upload(video, input_path, settings.max_upload_mb * 1024 * 1024)

        # ---- 2: Convert (H.264, no audio, longest side at most 1280px) ----
        run_ffmpeg([
            "-i", input_path,
            "-vf", "scale='min(1280,iw)':'min(1280,ih)':force_original_aspect_ratio=decrease,"
                   "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-an",
            converted_path,
        ])

        # ---- 3: Extract Pose Landmarks ----
        video_pose = extract_video_landmarks(converted_path)

        # ---- 4: Select Best Frame ----
        try:
            best = select_best_frame(video_pose, *BEST_FRAME_WINDOW)
        except VideoTooShortError:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Video is too short. Please record at least {BEST_FRAME_WINDOW[1] + 1} seconds.",
            ) from None
        if best is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "We couldn't find a person in the video. Make sure your whole body is in the frame.",
            )
        frame_index, landmarks, visibility = best

        # ---- 5: Analyse Stance and Generate Feedback ----
        rule_results = analyse_stance(landmarks, batting_hand)
        feedback = generate_feedback(rule_results)

        # ---- 6: Render Anonymised Video and Best Frame ----
        best_frame_image = anonymise_video(converted_path, anonymised_raw_path, rule_results, batting_hand, frame_index)

        # ---- 7: Re-encode Anonymised Video for Browser Playback ----
        run_ffmpeg([
            "-i", anonymised_raw_path,
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            anonymised_path,
        ])

        # ---- 8: Upload to Private Storage ----
        analysis_id = uuid.uuid4().hex
        base_path = f"{user_media_prefix(uid)}analyses/{analysis_id}"
        video_path = f"{base_path}/video.mp4"
        upload_private(anonymised_path, video_path, "video/mp4")

        best_frame_path = None
        if best_frame_image is not None:
            cv2.imwrite(frame_path, best_frame_image)
            best_frame_path = f"{base_path}/best_frame.jpg"
            upload_private(frame_path, best_frame_path, "image/jpeg")

    serialised_results = {
        name: {key: val for key, val in result.items() if key != "colour"} for name, result in rule_results.items()
    }

    # ---- 9: Store Analysis Results in Firestore ----
    get_db().collection("analyses").document(analysis_id).set({
        "user_id": uid,
        "drill": "batting-stance",
        "batting_hand": batting_hand,
        "video_path": video_path,
        "best_frame_path": best_frame_path,
        "frame_number": frame_index,
        "visibility": visibility,
        "rule_results": serialised_results,
        "feedback": feedback,
        "created_at": firestore.SERVER_TIMESTAMP,
    })

    # ---- 10: Return Feedback and Links ----
    return {
        "analysis_id": analysis_id,
        "feedback": feedback,
        "results": serialised_results,
        "video_path": video_path,
        "best_frame_path": best_frame_path,
        "video_url": signed_url(video_path),
        "best_frame_url": signed_url(best_frame_path) if best_frame_path else None,
        "frame_number": frame_index,
        "visibility": visibility,
    }


# ==== ENDPOINT: /health ====
class HealthInput(BaseModel):
    age: int = Field(ge=5, le=100)
    gender: Literal["male", "female"]
    height: float = Field(ge=100, le=250, description="Height in cm")
    weight: float = Field(ge=20, le=300, description="Weight in kg")
    activity: Literal["sedentary", "lightly active", "moderately active", "very active", "extra active"]


@app.post("/health")
def health(data: HealthInput, uid: str = Depends(get_current_user)):
    return calculate_health_metrics(data.age, data.gender, data.height, data.weight, data.activity)


# ==== ENDPOINTS: /media ====
class MediaPaths(BaseModel):
    paths: list[str] = Field(max_length=MAX_MEDIA_PATHS)


@app.post("/media/urls")
def media_urls(body: MediaPaths, uid: str = Depends(get_current_user)):
    check_owned_paths(body.paths, uid)
    return {"urls": {path: signed_url(path) for path in body.paths}}


@app.post("/media/delete")
def media_delete(body: MediaPaths, uid: str = Depends(get_current_user)):
    check_owned_paths(body.paths, uid)
    bucket = get_bucket()
    for path in body.paths:
        blob = bucket.blob(path)
        if blob.exists():
            blob.delete()
    return {"deleted": len(body.paths)}
