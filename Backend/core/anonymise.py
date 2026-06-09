# =======================================================================
# anonymise.py
# Video and image frames are processed to anonymise the participant.
# This respects the participant's privacy.
# The original video is replaced with a white silhouette on a black background.
# A colour-coded skeleton overlay is added to show the pose landmarks.
# The colours indicate which joints passed, failed or were in warning zones.
# The best frame is also annotated with angle measurements for any failing/warning joints.
#
# anonymise_video() - The full video is processed
# anonymise_frame() - The best frame is processed with additional angle annotations
# =======================================================================

# --- Imports ---
import cv2
import mediapipe as mp
import numpy as np

# ==== HELPER: Build Landmark Colour Map ====
def build_colour_maps(rule_results):
    # Two dictionaries are built from the rule_results:
    # - landmark_colours: maps landmark name to BGR colour for skeleton drawing
    # - angle_annotations: maps landmark name to (angle, colour) for annotating angles on the best frame

    # --- Default Colour (Grey = Unknown/Pass) ---
    landmark_colours = {
        name: (128, 128, 128) for name in [
            "Nose", "Left Ear", "Right Ear", "Left Eye", "Right Eye",
            "Left Wrist", "Right Wrist", "Left Elbow", "Right Elbow",
            "Left Shoulder", "Right Shoulder", "Left Hip", "Right Hip",
            "Left Knee", "Right Knee", "Left Ankle", "Right Ankle"
        ]
    }

    # --- Apply Rule Colours ---
    for check_name, result in rule_results.items():
        colour = result["colour"]
        if check_name == "Front Knee":
            landmark_colours["Right Knee"] = colour
        elif check_name == "Back Knee":
            landmark_colours["Left Knee"] = colour
        elif check_name == "Hip Lean":
            landmark_colours["Left Hip"] = colour
            landmark_colours["Right Hip"] = colour
        elif check_name == "Elbow Position":
            landmark_colours["Right Elbow"] = colour
        elif check_name == "Shoulder Position":
            landmark_colours["Left Shoulder"] = colour
            landmark_colours["Right Shoulder"] = colour
        elif check_name == "Head Position":
            landmark_colours["Nose"] = colour
            landmark_colours["Left Ear"] = colour
            landmark_colours["Right Ear"] = colour

    # --- Build Angle Annotations for Failing/Warning Joints ---
    angle_annotations = {}
    for check_name, result in rule_results.items():
        if result["status"] in ("Fail", "Warning") and result["measured"] is not None:
            if check_name == "Front Knee":
                angle_annotations["Right Knee"] = (result["measured"], result["colour"])
            elif check_name == "Back Knee":
                angle_annotations["Left Knee"] = (result["measured"], result["colour"])
            elif check_name == "Hip Lean":
                angle_annotations["Left Hip"] = (result["measured"], result["colour"])
                angle_annotations["Right Hip"] = (result["measured"], result["colour"])
            elif check_name == "Elbow Position":
                angle_annotations["Right Elbow"] = (result["measured"], result["colour"])

    return landmark_colours, angle_annotations

# ==== HELPER: Build Silhouette Frame ====
def build_silhouette(results, frame_width, frame_height, kernel):
    # The segmentation mask is converted into a clean silhouette
    # and returns it as a BGR image.

    silhouette = cv2.resize(
        results.segmentation_mask, (frame_width, frame_height),
        interpolation=cv2.INTER_NEAREST
    )
    silhouette = (silhouette > 0.5).astype(np.uint8) * 255
    silhouette = cv2.morphologyEx(silhouette, cv2.MORPH_CLOSE, kernel)
    silhouette = cv2.medianBlur(silhouette, 5)
    silhouette = (silhouette > 0).astype(np.uint8) * 255
    return cv2.cvtColor(silhouette, cv2.COLOR_GRAY2BGR)

# ==== HELPER: Draw Skeleton ====
def draw_skeleton(sil_bgr, pose_landmarks, mp_pose, index_to_colour, landmark_colours, w, h, angle_annotations=None, index_to_name=None):
    # Colour-coded skeleton connections and joint circles are drawn onto the silhouette image.
    # If angle_annotations is provided, joints with measured angles are annotated with the angle value in degrees.

    # --- Draw Connections ---
    for connection in mp_pose.POSE_CONNECTIONS:
        start_idx, end_idx = connection
        sl = pose_landmarks.landmark[start_idx]
        el = pose_landmarks.landmark[end_idx]
        if sl.visibility > 0.5 and el.visibility > 0.5:
            start_px = (int(sl.x * w), int(sl.y * h))
            end_px = (int(el.x * w), int(el.y * h))
            key = index_to_colour.get(start_idx)
            colour = landmark_colours.get(key, (128, 128, 128))
            cv2.line(sil_bgr, start_px, end_px, colour, 2)

    # --- Draw Joint Circles and Angle Annotations ---
    for idx, landmark in enumerate(pose_landmarks.landmark):
        if landmark.visibility > 0.5:
            px = (int(landmark.x * w), int(landmark.y * h))
            key = index_to_colour.get(idx)
            colour = landmark_colours.get(key, (128, 128, 128))
            cv2.circle(sil_bgr, px, 8, colour, -1)

            # --- Angle Annotation (Best Frame Only) ---
            if angle_annotations and index_to_name:
                joint_name = index_to_name.get(idx)
                if joint_name and joint_name in angle_annotations:
                    angle_val, ann_colour = angle_annotations[joint_name]
                    text = f"{int(angle_val)} deg"
                    cv2.putText(
                        sil_bgr, text, (px[0] + 12, px[1] - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, ann_colour, 2
                    )

# ==== PUBLIC: Anonymise Full Video ====
def anonymise_video(input_video_path, output_video_path, rule_results):
    # Every frame is processed and the footage is replaced with a silhouette and colour-coded skeleton.
    # The anonymised output is written to output_video_path.

    # --- Landmark Index to Name Map ---
    index_to_colour = {
        0: "Nose", 7: "Left Ear", 8: "Right Ear",
        11: "Left Shoulder", 12: "Right Shoulder",
        13: "Left Elbow", 14: "Right Elbow",
        15: "Left Wrist", 16: "Right Wrist",
        23: "Left Hip", 24: "Right Hip",
        25: "Left Knee", 26: "Right Knee",
        27: "Left Ankle", 28: "Right Ankle"
    }

    landmark_colours, _ = build_colour_maps(rule_results)

    try:
        # ---- Open Video ----
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise FileNotFoundError("Error: Could not open video.")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 30.0
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # --- Setup Video Writer ---
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height), isColor=True)
        if not out.isOpened():
            raise IOError("Error: Could not open video writer.")

        # --- Setup MediaPipe Pose ---
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            static_image_mode=False, model_complexity=1,
            enable_segmentation=True,
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

        # --- Process Frames ---
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            if results.segmentation_mask is None:
                out.write(frame)
                continue

            sil_bgr = build_silhouette(results, frame_width, frame_height, kernel)

            if results.pose_landmarks:
                h, w = sil_bgr.shape[:2]
                draw_skeleton(sil_bgr, results.pose_landmarks, mp_pose,
                               index_to_colour, landmark_colours, w, h)

            out.write(sil_bgr)

        return output_video_path

    finally:
        cap.release()
        out.release()
        pose.close()

# ==== PUBLIC: Anonymise Single Best Frame ====
def anonymise_frame(frame, rule_results):
    # The single (best) frame is processed in the same way as the full video.
    # However, if any joints have failing or warning status, the measured angle is annotated next to the joint on the frame.

    # --- Landmark Index Maps ---
    index_to_colour = {
        0: "Nose", 7: "Left Ear", 8: "Right Ear",
        11: "Left Shoulder", 12: "Right Shoulder",
        13: "Left Elbow", 14: "Right Elbow",
        15: "Left Wrist", 16: "Right Wrist",
        23: "Left Hip", 24: "Right Hip",
        25: "Left Knee", 26: "Right Knee",
        27: "Left Ankle", 28: "Right Ankle"
    }

    index_to_name = {
        13: "Left Elbow", 14: "Right Elbow",
        23: "Left Hip", 24: "Right Hip",
        25: "Left Knee", 26: "Right Knee"
    }

    landmark_colours, angle_annotations = build_colour_maps(rule_results)

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=True, model_complexity=1,
        enable_segmentation=True, min_detection_confidence=0.5
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

    try:
        # --- Run Pose Detection ---
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.segmentation_mask is None:
            return frame

        # --- Build Silhouette ---
        h, w = frame.shape[:2]
        sil_bgr = build_silhouette(results, w, h, kernel)

        # --- Draw Skeleton with Angle Annotations ---
        if results.pose_landmarks:
            draw_skeleton(sil_bgr, 
                        results.pose_landmarks, 
                        mp_pose,
                        index_to_colour, 
                        landmark_colours, 
                        w, h,
                        angle_annotations=angle_annotations,
                        index_to_name=index_to_name)

        return sil_bgr

    finally:
        pose.close()

# --- Local Test ---
if __name__ == "__main__":
    rule_results = {
        "Front Knee":{"colour": (0, 0, 255), "status": "Fail", "measured": 175.0},
        "Back Knee":{"colour": (0, 255, 0), "status": "Pass", "measured": 145.0},
        "Hip Lean":{"colour": (255, 0, 0), "status": "Fail", "measured": 0.12},
        "Elbow Position":{"colour": (255, 255, 0), "status": "Warning", "measured": 130.0},
        "Shoulder Position":{"colour": (255, 0, 255), "status": "Pass", "measured": 0.02},
        "Head Position":{"colour": (0, 255, 255), "status": "Pass", "measured": 0.01},
    }
    anonymised_path = anonymise_video("WK.mov", "anonymised_output.mp4", rule_results)
    print(f"Anonymised video saved to: {anonymised_path}")