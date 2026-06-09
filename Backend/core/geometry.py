# ============================================================
# geometry.py
# Provides mathematical functions for biomechanical analysis.
# Used by stance_rules.py to calculate joint angles, distances,
# midpoints, and range checks from pose landmarks.
# ============================================================

# ---- Imports ----
import numpy as np

# ---- Angle Calculation ----
def calculate_angle(a, b, c):
    ax, ay = a
    bx, by = b
    cx, cy = c

    ab_x, ab_y = ax - bx, ay - by
    cb_x, cb_y = cx - bx, cy - by

    magnitude_ab = np.sqrt(ab_x**2 + ab_y**2)
    magnitude_cb = np.sqrt(cb_x**2 + cb_y**2)

    dot = np.dot([ab_x, ab_y], [cb_x, cb_y])

    if magnitude_ab * magnitude_cb == 0:
        return None

    cos_angle = dot / (magnitude_ab * magnitude_cb)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    angle = np.arccos(cos_angle)
    return np.degrees(angle)

# ---- Distance Calculation ----
def calculate_distance(p1, p2):
    ax, ay = p1
    bx, by = p2
    euclidean = np.sqrt((bx - ax)**2 + (by - ay)**2)
    return euclidean

# ---- Midpoint Calculation ----
def midpoint(p1, p2):
    ax, ay = p1
    bx, by = p2
    return ((ax + bx) / 2, (ay + by) / 2)

# ---- Range Check ----
def in_range(value, min_val, max_val):
    return min_val <= value <= max_val

# ---- Test Cases ----
if __name__ == "__main__":
    print(calculate_angle((1,0), (0,0), (0,1)))
    print(calculate_distance((1,2), (3,4)))
    print(midpoint((2,2), (4,4)))
    print(in_range(145, 130, 160))