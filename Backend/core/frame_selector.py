# ============================================================
# frame_selector.py
# Selects the best frame from a video for pose analysis.
# Looks at the frames within a given time window and returns
# the one with the highest average landmark visibility score
# according to MediaPipe.
# ============================================================

# ---- Imports ----
import numpy as np


# ---- Raised When a Video is Too Short for the Time Window ----
class VideoTooShortError(ValueError):
    pass


# ---- Best Frame Selection ----
def select_best_frame(video_pose, start_second, end_second):
    # video_pose is the output of pose_extractor.extract_video_landmarks().
    # Returns (frame_index, landmarks, visibility_score) for the frame between
    # start_second and end_second with the highest average landmark visibility,
    # or None if no pose was detected in that window.
    if start_second < 0 or start_second >= end_second:
        raise ValueError("Invalid time range.")
    if video_pose.duration < end_second:
        raise VideoTooShortError(
            f"Video is {video_pose.duration:.1f}s long; it must be at least {end_second}s."
        )

    start_frame = int(start_second * video_pose.fps)
    end_frame = min(int(end_second * video_pose.fps), len(video_pose.frames))

    best = None
    best_visibility = -1.0
    for frame_index in range(start_frame, end_frame):
        landmarks = video_pose.frames[frame_index]
        if landmarks is None:
            continue
        average_visibility = float(np.mean([lm["Visibility"] for lm in landmarks.values()]))
        if average_visibility > best_visibility:
            best_visibility = average_visibility
            best = (frame_index, landmarks, average_visibility)

    return best
