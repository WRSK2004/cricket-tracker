# =======================================================================
# pose_extractor.py
# Named pose landmarks are extracted from every frame of a video using the
# MediaPipe Tasks PoseLandmarker (VIDEO mode, which tracks the person
# between frames). stance_rules.py uses this data for biomechanical analysis.
#
# Each landmark is stored as:
#   "Position"   - normalised (x, y) in the range 0-1 (x by width, y by height)
#   "Pixel"      - (x, y) in pixels. Angles must be measured on these, because
#                  normalised coordinates stretch one axis when the video is
#                  not square (e.g. a 9:16 phone video).
#   "Visibility" - MediaPipe's confidence that the landmark is visible
# =======================================================================

# ---- Imports ----
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

# ---- Model Location (downloaded by scripts/download_models.py) ----
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "pose_landmarker_full.task"

# ---- Landmarks Used by the Analysis (MediaPipe index -> name) ----
LANDMARK_NAMES = {
    0: "Nose",
    2: "Left Eye",
    5: "Right Eye",
    7: "Left Ear",
    8: "Right Ear",
    11: "Left Shoulder",
    12: "Right Shoulder",
    13: "Left Elbow",
    14: "Right Elbow",
    15: "Left Wrist",
    16: "Right Wrist",
    23: "Left Hip",
    24: "Right Hip",
    25: "Left Knee",
    26: "Right Knee",
    27: "Left Ankle",
    28: "Right Ankle",
}


# ---- Result of Running Pose Detection on a Whole Video ----
@dataclass
class VideoPose:
    fps: float
    width: int
    height: int
    frames: list = field(default_factory=list)  # one named-landmark dict (or None) per frame

    @property
    def duration(self):
        return len(self.frames) / self.fps


# ---- Create a PoseLandmarker ----
def create_pose_landmarker(segmentation=False):
    # VIDEO mode is used so that MediaPipe tracks the person across frames.
    # Segmentation masks are only needed when drawing the anonymised silhouette.
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Pose model not found at {MODEL_PATH}. Run: python scripts/download_models.py")
    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        output_segmentation_masks=segmentation,
    )
    return vision.PoseLandmarker.create_from_options(options)


# ---- Convert MediaPipe Output to Named Landmarks ----
def to_named_landmarks(pose_landmarks, width, height):
    landmarks = {}
    for index, name in LANDMARK_NAMES.items():
        landmark = pose_landmarks[index]
        landmarks[name] = {
            "Position": (landmark.x, landmark.y),
            "Pixel": (landmark.x * width, landmark.y * height),
            "Visibility": landmark.visibility if landmark.visibility is not None else 0.0,
        }
    return landmarks


# ---- Frame Timestamp for VIDEO Mode (must increase every frame) ----
def frame_timestamp_ms(frame_index, fps):
    return int(frame_index * 1000 / fps)


# ---- Open a Video and Read its Properties ----
def open_video(video_path):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError("Could not open video.")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0
    return cap, fps


# ---- Pose Landmark Extraction for Every Frame ----
def extract_video_landmarks(video_path):
    # Runs pose detection on every frame of the video.
    # Frames where no person is detected are stored as None.
    cap, fps = open_video(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_pose = VideoPose(fps=fps, width=width, height=height)

    try:
        with create_pose_landmarker() as landmarker:
            frame_index = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                height, width = frame.shape[:2]
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                result = landmarker.detect_for_video(image, frame_timestamp_ms(frame_index, fps))
                if result.pose_landmarks:
                    video_pose.frames.append(to_named_landmarks(result.pose_landmarks[0], width, height))
                else:
                    video_pose.frames.append(None)
                frame_index += 1
    finally:
        cap.release()

    # Frame size is taken from decoded frames in case the container reports it before rotation
    video_pose.width, video_pose.height = width, height
    return video_pose


# ---- Local Test ----
if __name__ == "__main__":
    import sys

    pose = extract_video_landmarks(sys.argv[1])
    detected = sum(1 for f in pose.frames if f)
    print(f"{len(pose.frames)} frames, {detected} with a pose, {pose.width}x{pose.height} @ {pose.fps:.1f} fps")
