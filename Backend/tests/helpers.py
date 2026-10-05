# Helpers for building synthetic pose data in tests.

from core.pose_extractor import LANDMARK_NAMES


def make_landmarks(points, width=1000, height=1000, visibility=0.99):
    # points: {name: (x, y)} in normalised coordinates. Unlisted landmarks are placed
    # at the centre. Returns the same structure as pose_extractor.to_named_landmarks().
    landmarks = {}
    for name in LANDMARK_NAMES.values():
        x, y = points.get(name, (0.5, 0.5))
        landmarks[name] = {"Position": (x, y), "Pixel": (x * width, y * height), "Visibility": visibility}
    return landmarks


# A plausible left-hander's stance (front side = batter's right), in a square frame.
LEFT_HANDER_STANCE = {
    "Nose": (0.50, 0.15),
    "Left Ear": (0.47, 0.15),
    "Right Ear": (0.53, 0.155),
    "Left Shoulder": (0.42, 0.28),
    "Right Shoulder": (0.58, 0.28),
    "Right Elbow": (0.62, 0.40),
    "Right Wrist": (0.55, 0.48),
    "Left Hip": (0.45, 0.55),
    "Right Hip": (0.55, 0.55),
    "Left Knee": (0.43, 0.72),
    "Right Knee": (0.60, 0.72),
    "Left Ankle": (0.43, 0.90),
    "Right Ankle": (0.57, 0.90),
}
