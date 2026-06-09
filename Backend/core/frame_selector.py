# ============================================================
# frame_selector.py
# Selects the best frame from a video for pose analysis.
# Iterates through frames within a given time window.
# Returns the frame with the highest average landmark visibility
# score according to MediaPipe. 
# ============================================================

# ---- Imports ----
import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

#---- Best Frame Selection ----
def select_best_frame(video_path, start_second, end_second):
    # A video is opened and frames are read between start_second and end_second.
    # The frame with the highest average landmark visibility (best_frame, frame_number, visibility_score) is returned.
    # If the video connot be opened or no pose is detected, None is returned.

    try:
        # ---- Open Video ----
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Could not open video.")
            return None
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 30.0

        # ---- Valaidate Time Range ----
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        time = frame_count / fps

        if start_second < 0 or end_second > time or start_second >= end_second:
            print("Error: Invalid time range.")
            return None
        
        start_frame = int(start_second * fps)
        end_frame = int(end_second * fps) - 1 

        # ---- Scan Frames for Best Visibility ----
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        best_frame = None
        best_visibility = -1
        best_frame_num = start_frame

        with mp_pose.Pose(static_image_mode=True) as pose:
            for frame_num in range(start_frame, end_frame + 1):
                ret, frame = cap.read()
                if not ret:
                    print(f"Error: Could not read frame {frame_num}.")
                    break

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb)
                if results.pose_landmarks:
                    average_visibility = np.mean([landmark.visibility for landmark in results.pose_landmarks.landmark])
                    if average_visibility > best_visibility:
                        best_visibility = average_visibility
                        best_frame = frame.copy()
                        best_frame_num = frame_num
        
        return best_frame, best_frame_num, best_visibility
        
    finally:
        cap.release()    

# ---- Test Case ----
if __name__ == "__main__":
    INPUT_VIDEO_PATH = "WK.mov"
    result = select_best_frame(INPUT_VIDEO_PATH, 1, 2)
    if result:
        frame, frame_num, visibility = result
        print(f"Best frame number: {frame_num}")
        print(f"Visibility Score: {visibility}")