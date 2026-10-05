# =======================================================================
# stance_rules.py
# The batting stance is analysed against biomechanical rules.
# Each check function analyses a specific body part using landmark positions
# from pose_extractor.py and thresholds defined as Pass/Warning/Fail ranges.
# Structured results consumed by feedback.py and anonymise.py for feedback
# generation and visualisation are returned.
#
# The checks are written for a LEFT-handed batter filmed front-on from the
# bowler's end (front side = the batter's right side). A right-handed batter
# filmed from the same place is a mirror image of this, so their landmarks
# are mirrored before the checks run (see mirror_landmarks).
#
# Angles are measured on pixel coordinates so they are not distorted by the
# video's aspect ratio. Position-difference checks use normalised coordinates.
# =======================================================================

# ---- Imports ----
from core.geometry import calculate_angle, in_range, midpoint

# ---- Batting Hands ----
BATTING_HANDS = ("left", "right")

# ---- Landmarks Each Check Relates To (for a left-handed batter) ----
# Used by anonymise.py to colour the skeleton.
CHECK_LANDMARKS = {
    "Front Knee": ["Right Knee"],
    "Back Knee": ["Left Knee"],
    "Hip Lean": ["Left Hip", "Right Hip"],
    "Head Position": ["Nose", "Left Ear", "Right Ear"],
    "Elbow Position": ["Right Elbow"],
    "Shoulder Position": ["Left Shoulder", "Right Shoulder"],
}

# ---- Checks Whose Measured Value is an Angle in Degrees ----
ANGLE_CHECKS = {"Front Knee", "Back Knee", "Elbow Position"}

# ---- Status Colours (BGR, for OpenCV drawing) ----
UNKNOWN_COLOUR = (128, 128, 128)


# ---- Swap "Left"/"Right" in a Landmark Name ----
def swap_side(name):
    if name.startswith("Left "):
        return "Right " + name[len("Left "):]
    if name.startswith("Right "):
        return "Left " + name[len("Right "):]
    return name


# ---- Mirror Landmarks (Right-Handed Batter -> Left-Handed Equivalent) ----
def mirror_landmarks(landmarks):
    # Flips the image horizontally and swaps left/right body parts.
    # Angles and distances are unchanged by a reflection, so pixel x is simply negated.
    mirrored = {}
    for name, data in landmarks.items():
        x, y = data["Position"]
        px, py = data["Pixel"]
        mirrored[swap_side(name)] = {
            "Position": (1 - x, y),
            "Pixel": (-px, py),
            "Visibility": data["Visibility"],
        }
    return mirrored


# ---- Real Landmark Names for a Check, Given the Batting Hand ----
def landmarks_for_check(check_name, batting_hand):
    names = CHECK_LANDMARKS.get(check_name, [])
    if batting_hand == "right":
        return [swap_side(name) for name in names]
    return list(names)


# ---- Status Determination ----
def determine_status(value, pass_range, warning_range):
    if in_range(value, *pass_range):
        return "Pass", (0, 255, 0)
    elif in_range(value, *warning_range):
        return "Warning", (0, 165, 255)
    else:
        return "Fail", (0, 0, 255)


# ---- Result When a Check Cannot be Measured ----
def unknown_result(check, what):
    return {
        "check": check,
        "measured": None,
        "status": "Unknown",
        "colour": UNKNOWN_COLOUR,
        "message": f"Visibility too low to determine {what}.",
    }


# ---- Shared Knee Angle Check ----
def check_knee(landmarks, side, check):
    # side is "Right" (front knee) or "Left" (back knee) for a left-handed batter
    if landmarks[f"{side} Knee"]["Visibility"] <= 0.6:
        return unknown_result(check, f"{check.lower()} angle")

    knee_angle = calculate_angle(
        landmarks[f"{side} Hip"]["Pixel"], landmarks[f"{side} Knee"]["Pixel"], landmarks[f"{side} Ankle"]["Pixel"]
    )
    if knee_angle is None:
        return unknown_result(check, f"{check.lower()} angle")

    pass_range = (130, 160)
    warning_range = (120, 170)
    status, colour = determine_status(knee_angle, pass_range, warning_range)
    if status == "Pass":
        message = f"{check} angle is good."
    elif status == "Warning":
        if knee_angle < pass_range[0]:
            message = f"{check} is slightly too bent. Try to straighten it a little."
        else:
            message = f"{check} is slightly too straight. Try to bend it a little more."
    else:
        if knee_angle < warning_range[0]:
            message = f"{check} is bent too much. Try to straighten it."
        else:
            message = f"{check} is too straight. Try to bend it more."

    return {"check": check, "measured": round(knee_angle, 2), "status": status, "colour": colour, "message": message}


# ---- Front Knee Check ----
def check_front_knee(landmarks):
    return check_knee(landmarks, "Right", "Front Knee")


# ---- Back Knee Check ----
def check_back_knee(landmarks):
    return check_knee(landmarks, "Left", "Back Knee")


# ---- Hip Lean Check ----
def check_hip_lean(landmarks):
    hip_visibility = (landmarks["Left Hip"]["Visibility"] + landmarks["Right Hip"]["Visibility"]) / 2
    ankle_visibility = (landmarks["Left Ankle"]["Visibility"] + landmarks["Right Ankle"]["Visibility"]) / 2
    if hip_visibility <= 0.6 or ankle_visibility <= 0.6:
        return unknown_result("Hip Lean", "hip lean")

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
    else:
        if difference < warning_range[0]:
            message = "Hip lean is too far forward. Try to move hips more backward."
        else:
            message = "Hip lean is too far backward. Try to move hips more forward."

    return {
        "check": "Hip Lean",
        "measured": round(difference, 2),
        "status": status,
        "colour": colour,
        "message": message,
    }


# ---- Head Position Check ----
def check_head_position(landmarks):
    # Measures how level the head is: the height difference between the two ears.
    # A level head keeps the eyes level, which helps judge line and length.
    if (landmarks["Left Ear"]["Visibility"] + landmarks["Right Ear"]["Visibility"]) / 2 <= 0.6:
        return unknown_result("Head Position", "head position")

    difference = abs(landmarks["Left Ear"]["Position"][1] - landmarks["Right Ear"]["Position"][1])
    pass_range = (0, 0.03)
    warning_range = (0, 0.06)
    status, colour = determine_status(difference, pass_range, warning_range)
    if status == "Pass":
        message = "Head is level, so your eyes are level. Good."
    elif status == "Warning":
        message = "Head is slightly tilted. Try to keep your eyes level."
    else:
        message = "Head is tilted. Try to keep your head still and your eyes level."

    return {
        "check": "Head Position",
        "measured": round(difference, 2),
        "status": status,
        "colour": colour,
        "message": message,
    }


# ---- Elbow Position Check ----
def check_elbow_position(landmarks):
    # Front elbow (the batter's right elbow for a left-hander)
    if (
        landmarks["Right Wrist"]["Visibility"] <= 0.6
        or landmarks["Right Elbow"]["Visibility"] <= 0.6
        or landmarks["Right Shoulder"]["Visibility"] <= 0.6
    ):
        return unknown_result("Front Elbow", "front elbow position")

    elbow_angle = calculate_angle(
        landmarks["Right Wrist"]["Pixel"], landmarks["Right Elbow"]["Pixel"], landmarks["Right Shoulder"]["Pixel"]
    )
    if elbow_angle is None:
        return unknown_result("Front Elbow", "front elbow position")

    pass_range = (70, 120)
    warning_range = (60, 140)
    status, colour = determine_status(elbow_angle, pass_range, warning_range)
    if status == "Pass":
        message = "Front elbow angle is good."
    elif status == "Warning":
        if elbow_angle < pass_range[0]:
            message = "Front elbow is slightly too bent. Try to open it a little."
        else:
            message = "Front elbow is slightly too straight. Try to bend it a little."
    else:
        if elbow_angle < warning_range[0]:
            message = "Front elbow is bent too much. Try to open it more."
        else:
            message = "Front elbow is too straight. Try to bend it more."

    return {
        "check": "Front Elbow",
        "measured": round(elbow_angle, 2),
        "status": status,
        "colour": colour,
        "message": message,
    }


# ---- Shoulder Position Check ----
def check_shoulder_position(landmarks):
    # Height difference between the front shoulder and the back shoulder
    shoulder_visibility = (landmarks["Right Shoulder"]["Visibility"] + landmarks["Left Shoulder"]["Visibility"]) / 2
    if shoulder_visibility <= 0.6:
        return unknown_result("Shoulder Position", "shoulder position")

    difference = landmarks["Right Shoulder"]["Position"][1] - landmarks["Left Shoulder"]["Position"][1]
    pass_range = (-0.05, 0.05)
    warning_range = (-0.1, 0.1)
    status, colour = determine_status(difference, pass_range, warning_range)
    if status == "Pass":
        message = "Shoulder position is good."
    elif status == "Warning":
        if difference < pass_range[0]:
            message = "Front shoulder is slightly high. Try to lower it a little."
        else:
            message = "Front shoulder is slightly low. Try to raise it a little."
    else:
        if difference < warning_range[0]:
            message = "Front shoulder is too high. Try to lower it so your shoulders are level."
        else:
            message = "Front shoulder is too low. Try to raise it so your shoulders are level."

    return {
        "check": "Shoulder Position",
        "measured": round(difference, 2),
        "status": status,
        "colour": colour,
        "message": message,
    }


# ---- Main Analysis Function ----
def analyse_stance(landmarks, batting_hand):
    if batting_hand not in BATTING_HANDS:
        raise ValueError(f"batting_hand must be one of {BATTING_HANDS}")
    if batting_hand == "right":
        landmarks = mirror_landmarks(landmarks)

    return {
        "Front Knee": check_front_knee(landmarks),
        "Back Knee": check_back_knee(landmarks),
        "Hip Lean": check_hip_lean(landmarks),
        "Head Position": check_head_position(landmarks),
        "Elbow Position": check_elbow_position(landmarks),
        "Shoulder Position": check_shoulder_position(landmarks),
    }
