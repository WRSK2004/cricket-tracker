# =======================================================================
# stance_rules.py
# The batting stance is analysed against biomechanical rules.
# Each check function analyses a specific body part using landmark positions
# from pose_extractor.py and thresholds defined as Pass/Warning/Fail ranges.
# Structured results consumed by feedback.py and anonymise.py for feedback
# generation and visualisation are returned.
# =======================================================================

# ---- Imports ----
from core.pose_extractor import extract_landmarks
from core.geometry import calculate_angle, calculate_distance, midpoint, in_range

# ---- Status Determination ----
def determine_status(value, pass_range, warning_range):
    if in_range(value, *pass_range):
        rgb = (0, 255, 0)
        return "Pass", rgb
    elif in_range(value, *warning_range):
        rgb = (0, 165, 255)
        return "Warning", rgb
    else:
        rgb = (0, 0, 255)
        return "Fail", rgb
    
# ---- Front Knee Check ----
def check_front_knee(landmarks):
    front_knee_visibility = landmarks["Right Knee"]["Visibility"]
    if front_knee_visibility > 0.6:
        front_knee_angle = calculate_angle(landmarks["Right Hip"]["Position"], landmarks["Right Knee"]["Position"], landmarks["Right Ankle"]["Position"])
        pass_range = (130, 160)
        warning_range = (120, 170)
        status, colour = determine_status(front_knee_angle, pass_range, warning_range)
        if status == "Pass":
            message = "Front knee angle is good."
        elif status == "Warning":
            if front_knee_angle < pass_range[0]:
                message = "Front knee angle is slightly off. Try to open it more."
            else:
                message = "Front knee angle is slightly off. Try to close it more."
        elif status == "Fail":
            if front_knee_angle < warning_range[0]:
                message = "Front knee angle is too closed. Try to open it more."
            else:
                message = "Front knee angle is too open. Try to close it more."

        return {
            "check": "Front Knee",
            "measured": round(front_knee_angle, 2),
            "status": status,
            "colour": colour,
            "message": message
        }
    else:
        return {
            "check": "Front Knee",
            "measured": None,
            "status": "Unknown",
            "colour": (128, 128, 128),
            "message": "Visibility too low to determine front knee angle."
        }

# ---- Back Knee Check ----
def check_back_knee(landmarks):
    back_knee_visibility = landmarks["Left Knee"]["Visibility"]
    if back_knee_visibility > 0.6:
        back_knee_angle = calculate_angle(landmarks["Left Hip"]["Position"], landmarks["Left Knee"]["Position"], landmarks["Left Ankle"]["Position"])
        pass_range = (130, 160)
        warning_range = (120, 170)
        status, colour = determine_status(back_knee_angle, pass_range, warning_range)
        if status == "Pass":
            message = "Back knee angle is good."
        elif status == "Warning":
            if back_knee_angle < pass_range[0]:
                message = "Back knee angle is slightly off. Try to open it more."
            else:
                message = "Back knee angle is slightly off. Try to close it more."
        elif status == "Fail":
            if back_knee_angle < warning_range[0]:
                message = "Back knee angle is too closed. Try to open it more."
            else:
                message = "Back knee angle is too open. Try to close it more."
        return {
            "check": "Back Knee",
            "measured": round(back_knee_angle, 2),
            "status": status,
            "colour": colour,
            "message": message
        }
    else:
        return {
            "check": "Back Knee",
            "measured": None,
            "status": "Unknown",
            "colour": (128, 128, 128),
            "message": "Visibility too low to determine back knee angle."
        }

# ---- Hip Lean Check ----
def check_hip_lean(landmarks):
    hip_visibility = (landmarks["Left Hip"]["Visibility"] + landmarks["Right Hip"]["Visibility"]) / 2
    ankle_visibility = (landmarks["Left Ankle"]["Visibility"] + landmarks["Right Ankle"]["Visibility"]) / 2
    if hip_visibility > 0.6 and ankle_visibility > 0.6:
        hip_midpoint = midpoint(landmarks["Left Hip"]["Position"], landmarks["Right Hip"]["Position"])
        ankle_midpoint = midpoint(landmarks["Left Ankle"]["Position"], landmarks["Right Ankle"]["Position"])
        difference = hip_midpoint[0] - ankle_midpoint[0]
        pass_range = (-0.05, 0.05)
        warning_range = (-0.1, 0.1)
        status, colour = determine_status(difference, pass_range, warning_range)
        if status == "Pass":
            message = "Hip lean is good."
        elif status == "Warning":
            if difference < pass_range[0]:
                message = "Hip lean is slightly off. Try to move hips more forward."
            else:
                message = "Hip lean is slightly off. Try to move hips more backward."
        elif status == "Fail":
            if difference < warning_range[0]:
                message = "Hip lean is too far forward. Try to move hips more backward."
            else:
                message = "Hip lean is too far backward. Try to move hips more forward."
        return {
            "check": "Hip Lean",
            "measured": round(difference, 2),
            "status": status,
            "colour": colour,
            "message": message
        }
    else:
        return {
            "check": "Hip Lean",
            "measured": None,
            "status": "Unknown",
            "colour": (128, 128, 128),
            "message": "Visibility too low to determine hip lean."
        }

# ---- Head Position Check ----
def check_head_position(landmarks):
    left_ear_visibility = landmarks["Left Ear"]["Visibility"]
    right_ear_visibility = landmarks["Right Ear"]["Visibility"]
    if (left_ear_visibility + right_ear_visibility) / 2 > 0.6:
        left_ear_position = landmarks["Left Ear"]["Position"]
        right_ear_position = landmarks["Right Ear"]["Position"]
        difference = abs(left_ear_position[1] - right_ear_position[1])
        pass_range = (0, 0.03)
        warning_range = (0, 0.06)
        status, colour = determine_status(difference, pass_range, warning_range)
        if status == "Pass":
            message = "Head position is good."
        elif status == "Warning":
            if difference < pass_range[0]:
                message = "Head position is slightly off. Try to move head more forward."
            else:
                message = "Head position is slightly off. Try to move head more backward."
        elif status == "Fail":
            if difference < warning_range[0]:
                message = "Head position is too far forward. Try to move head more backward."
            else:
                message = "Head position is too far backward. Try to move head more forward." 
        return {
            "check": "Head Position",
            "measured": round(difference, 2),
            "status": status,
            "colour": colour,
            "message": message
        }
    else:
        return {
            "check": "Head Position",
            "measured": None,
            "status": "Unknown",
            "colour": (128, 128, 128),
            "message": "Visibility too low to determine head position."
        }

# ---- Elbow Position Check ----
def check_elbow_position(landmarks):
    right_wrist_visibility = landmarks["Right Wrist"]["Visibility"]
    right_elbow_visibility = landmarks["Right Elbow"]["Visibility"]
    right_shoulder_visibility = landmarks["Right Shoulder"]["Visibility"]
    if right_wrist_visibility > 0.6 and right_elbow_visibility > 0.6 and right_shoulder_visibility > 0.6:
        right_elbow_angle = calculate_angle(landmarks["Right Wrist"]["Position"], landmarks["Right Elbow"]["Position"], landmarks["Right Shoulder"]["Position"])
        pass_range = (70, 120)
        warning_range = (60, 140)
        status, colour = determine_status(right_elbow_angle, pass_range, warning_range)
        if status == "Pass":
            message = "Right elbow angle is good."
        elif status == "Warning":
            if right_elbow_angle < pass_range[0]:
                message = "Right elbow angle is slightly off. Try to open it more."
            else:
                message = "Right elbow angle is slightly off. Try to close it more."
        elif status == "Fail":
            if right_elbow_angle < warning_range[0]:
                message = "Right elbow angle is too closed. Try to open it more."
            else:
                message = "Right elbow angle is too open. Try to close it more."
        return {
            "check": "Right Elbow Position",
            "measured": round(right_elbow_angle, 2),
            "status": status,
            "colour": colour,
            "message": message
        }
    else:
        return {
            "check": "Right Elbow Position",
            "measured": None,
            "status": "Unknown",
            "colour": (128, 128, 128),
            "message": "Visibility too low to determine right elbow position."
        }

# ---- Shoulder Position Check ----
def check_shoulder_position(landmarks):
    right_shoulder_position = landmarks["Right Shoulder"]["Position"]
    left_shoulder_position = landmarks["Left Shoulder"]["Position"]
    shoulder_visibility = (landmarks["Right Shoulder"]["Visibility"] + landmarks["Left Shoulder"]["Visibility"]) / 2
    if shoulder_visibility > 0.6:
        difference = right_shoulder_position[1] - left_shoulder_position[1]
        pass_range = (-0.05, 0.05)
        warning_range = (-0.1, 0.1)
        status, colour = determine_status(difference, pass_range, warning_range)
        if status == "Pass":
            message = "Shoulder position is good."
        elif status == "Warning":
            if difference < pass_range[0]:
                message = "Shoulder position is slightly off. Try to raise the right shoulder."
            else:
                message = "Shoulder position is slightly off. Try to lower the right shoulder."
        elif status == "Fail":
            if difference < warning_range[0]:
                message = "Shoulder position is too low. Try to raise it."
            else:
                message = "Shoulder position is too high. Try to lower it."
        return {
            "check": "Shoulder Position",
            "measured": round(difference, 2),
            "status": status,
            "colour": colour,
            "message": message
        }
    else:
        return {
            "check": "Shoulder Position",
            "measured": None,
            "status": "Unknown",
            "colour": (128, 128, 128),
            "message": "Visibility too low to determine shoulder position."
        }

# ---- Main Analysis Function ----
def analyse_stance(landmarks):
    results = {}
    results["Front Knee"] = check_front_knee(landmarks)
    results["Back Knee"] = check_back_knee(landmarks)
    results["Hip Lean"] = check_hip_lean(landmarks)
    results["Head Position"] = check_head_position(landmarks)
    results["Elbow Position"] = check_elbow_position(landmarks)
    results["Shoulder Position"] = check_shoulder_position(landmarks)
    return results

# ---- Test Case ----
if __name__ == "__main__":
    from core.frame_selector import select_best_frame
    result = select_best_frame("WK.mov", 1, 2)
    if result:
        frame, frame_num, visibility = result
        landmarks = extract_landmarks(frame)
        if landmarks:
            analysis_results = analyse_stance(landmarks)
            for check, data in analysis_results.items():
                print(f"\n{check}")
                print(f" Status: {data['status']}")
                print(f" Measured: {data['measured']}")
                print(f" Message: {data['message']}")
        else:
            print("No landmarks detected.")