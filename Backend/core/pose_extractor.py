# =======================================================================
# pose_extractor.py
# Named pose landmarks are extracted from a video frame using MediaPipe.
# A dictionary of landmark names, their 2D positions and visibility score
# is returned. stance_rules.py uses this data for biomechanical analysis.
# =======================================================================

# ---- Imports ----
import cv2
import mediapipe as mp
import numpy as np
from core.frame_selector import select_best_frame

# ---- Pose Landmark Extraction ----
def extract_landmarks(frame):
    # MediaPipe is run on a single frame and extracts 17 named landmarks.
    # Each landmark contains normalised (x,y) positions and a visibility score.
    # A dictionary of landmark data is returned.
    # If no pose is detected, None is returned.
    
    mp_pose = mp.solutions.pose

    with mp_pose.Pose(static_image_mode=True) as pose:
        # ---- Run Pose Detection ----
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            # ---- Extract Named Landmarks ----
            landmarks = {
               "Nose": results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE],
               "Left Ear": results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_EAR],
               "Right Ear": results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_EAR],
               "Left Eye": results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_EYE],
               "Right Eye": results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_EYE],
               "Left Wrist": results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST],
               "Right Wrist": results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST],
               "Left Elbow": results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW],
               "Right Elbow": results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW],     
               "Left Shoulder": results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER],
               "Right Shoulder": results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER],
               "Left Hip": results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP],
               "Right Hip": results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP],
               "Left Knee": results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE],
               "Right Knee": results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE],
               "Left Ankle": results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE],
               "Right Ankle": results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE]                                       
            }

            # ---- Normalise Landmarks ----
            for landmark_name, landmark in landmarks.items():
                landmarks[landmark_name] = {
                    "Position": (landmark.x, landmark.y),
                    "Visibility": landmark.visibility
                }
            return landmarks
        else:
            return None

# ---- Test Case ----        
if __name__ == "__main__":
    result = select_best_frame("WK.mov", 1, 2)
    if result:
        frame, frame_num, visibility = result
        landmarks = extract_landmarks(frame)
        if landmarks:
            for name, data in landmarks.items():
                print(f"{name}: pos = {data['Position']}, visibility = {data['Visibility']}")
        else:
            print("No landmarks detected.")