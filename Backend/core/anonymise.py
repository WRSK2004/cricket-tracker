# =======================================================================
# anonymise.py
# Video frames are processed to anonymise the participant.
# This respects the participant's privacy.
# The original video is replaced with a white silhouette on a black background.
# A colour-coded skeleton overlay is added to show the pose landmarks.
# The colours indicate which joints passed, failed or were in warning zones.
# The best frame is also annotated with angle measurements for any failing/warning joints.
#
# Frames where no person is detected are written as plain black frames, so the
# original footage never appears in the output.
#
# anonymise_video() - The full video is processed in a single pass, and the
#                     anonymised best frame (with angle annotations) is returned.
# =======================================================================

# --- Imports ---
import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision

from core.pose_extractor import create_pose_landmarker, frame_timestamp_ms, open_video
from core.stance_rules import ANGLE_CHECKS, UNKNOWN_COLOUR, landmarks_for_check

# --- Skeleton Connections and Landmark Index -> Name Map ---
POSE_CONNECTIONS = [(c.start, c.end) for c in vision.PoseLandmarksConnections.POSE_LANDMARKS]
INDEX_TO_NAME = {
    0: "Nose", 7: "Left Ear", 8: "Right Ear",
    11: "Left Shoulder", 12: "Right Shoulder",
    13: "Left Elbow", 14: "Right Elbow",
    15: "Left Wrist", 16: "Right Wrist",
    23: "Left Hip", 24: "Right Hip",
    25: "Left Knee", 26: "Right Knee",
    27: "Left Ankle", 28: "Right Ankle",
}
VISIBILITY_THRESHOLD = 0.5


# ==== HELPER: Build Landmark Colour Map ====
def build_colour_maps(rule_results, batting_hand):
    # Two dictionaries are built from the rule_results:
    # - landmark_colours: maps landmark name to BGR colour for skeleton drawing
    # - angle_annotations: maps landmark name to (angle, colour) for annotating angles on the best frame
    landmark_colours = {name: UNKNOWN_COLOUR for name in INDEX_TO_NAME.values()}
    angle_annotations = {}

    for check_name, result in rule_results.items():
        for landmark_name in landmarks_for_check(check_name, batting_hand):
            landmark_colours[landmark_name] = result["colour"]
            if (
                check_name in ANGLE_CHECKS
                and result["status"] in ("Fail", "Warning")
                and result["measured"] is not None
            ):
                angle_annotations[landmark_name] = (result["measured"], result["colour"])

    return landmark_colours, angle_annotations


# ==== HELPER: Build Silhouette Frame ====
def build_silhouette(segmentation_mask, frame_width, frame_height, kernel):
    # The segmentation mask is converted into a clean silhouette and returned as a BGR image.
    mask = np.squeeze(segmentation_mask.numpy_view())
    mask = cv2.resize(mask, (frame_width, frame_height), interpolation=cv2.INTER_NEAREST)
    silhouette = (mask > 0.5).astype(np.uint8) * 255
    silhouette = cv2.morphologyEx(silhouette, cv2.MORPH_CLOSE, kernel)
    silhouette = cv2.medianBlur(silhouette, 5)
    silhouette = (silhouette > 0).astype(np.uint8) * 255
    return cv2.cvtColor(silhouette, cv2.COLOR_GRAY2BGR)


# ==== HELPER: Draw Skeleton ====
def draw_skeleton(image, pose_landmarks, landmark_colours, angle_annotations=None):
    # Colour-coded skeleton connections and joint circles are drawn onto the silhouette image.
    # If angle_annotations is provided, joints with measured angles are annotated with the angle value in degrees.
    h, w = image.shape[:2]

    def colour_for(index):
        return landmark_colours.get(INDEX_TO_NAME.get(index), UNKNOWN_COLOUR)

    def visible(landmark):
        return (landmark.visibility or 0.0) > VISIBILITY_THRESHOLD

    # --- Draw Connections ---
    for start_idx, end_idx in POSE_CONNECTIONS:
        start, end = pose_landmarks[start_idx], pose_landmarks[end_idx]
        if visible(start) and visible(end):
            start_px = (int(start.x * w), int(start.y * h))
            end_px = (int(end.x * w), int(end.y * h))
            cv2.line(image, start_px, end_px, colour_for(start_idx), 2)

    # --- Draw Joint Circles and Angle Annotations ---
    for idx, landmark in enumerate(pose_landmarks):
        if not visible(landmark):
            continue
        px = (int(landmark.x * w), int(landmark.y * h))
        cv2.circle(image, px, 8, colour_for(idx), -1)

        joint_name = INDEX_TO_NAME.get(idx)
        if angle_annotations and joint_name in angle_annotations:
            angle_val, ann_colour = angle_annotations[joint_name]
            cv2.putText(
                image, f"{int(angle_val)} deg", (px[0] + 12, px[1] - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, ann_colour, 2,
            )


# ==== PUBLIC: Anonymise Full Video ====
def anonymise_video(input_video_path, output_video_path, rule_results, batting_hand, best_frame_index):
    # Every frame is replaced with a silhouette and colour-coded skeleton and written to output_video_path.
    # The anonymised best frame (with angle annotations) is returned, or None if no pose was found in it.
    landmark_colours, angle_annotations = build_colour_maps(rule_results, batting_hand)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    best_frame_image = None

    cap, fps = open_video(input_video_path)
    out = None
    try:
        with create_pose_landmarker(segmentation=True) as landmarker:
            frame_index = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                h, w = frame.shape[:2]

                # --- Setup Video Writer (on first frame, using decoded frame size) ---
                if out is None:
                    out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
                    if not out.isOpened():
                        raise OSError("Could not open video writer.")

                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                result = landmarker.detect_for_video(image, frame_timestamp_ms(frame_index, fps))

                if result.pose_landmarks and result.segmentation_masks:
                    output_frame = build_silhouette(result.segmentation_masks[0], w, h, kernel)
                    draw_skeleton(output_frame, result.pose_landmarks[0], landmark_colours)
                    if frame_index == best_frame_index:
                        best_frame_image = build_silhouette(result.segmentation_masks[0], w, h, kernel)
                        draw_skeleton(best_frame_image, result.pose_landmarks[0], landmark_colours, angle_annotations)
                else:
                    # No person found: write a black frame rather than the original footage
                    output_frame = np.zeros_like(frame)

                out.write(output_frame)
                frame_index += 1
    finally:
        cap.release()
        if out is not None:
            out.release()

    return best_frame_image
