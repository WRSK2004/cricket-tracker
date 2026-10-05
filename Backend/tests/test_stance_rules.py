import pytest

from core.stance_rules import (
    analyse_stance,
    check_front_knee,
    check_head_position,
    check_shoulder_position,
    landmarks_for_check,
    mirror_landmarks,
)
from tests.helpers import LEFT_HANDER_STANCE, make_landmarks


def mirror_points(points):
    # Mirror image of a stance: flip x and swap left/right body parts
    def swap(name):
        if name.startswith("Left "):
            return "Right " + name[5:]
        if name.startswith("Right "):
            return "Left " + name[6:]
        return name

    return {swap(name): (1 - x, y) for name, (x, y) in points.items()}


def test_right_hander_gets_same_results_as_mirrored_left_hander():
    left = analyse_stance(make_landmarks(LEFT_HANDER_STANCE), "left")
    right = analyse_stance(make_landmarks(mirror_points(LEFT_HANDER_STANCE)), "right")
    for check in left:
        assert left[check]["status"] == right[check]["status"], check
        assert left[check]["measured"] == pytest.approx(right[check]["measured"]), check


def test_wrong_batting_hand_changes_which_leg_is_front():
    landmarks = make_landmarks(LEFT_HANDER_STANCE)
    as_left = analyse_stance(landmarks, "left")
    as_right = analyse_stance(landmarks, "right")
    assert as_left["Front Knee"]["measured"] == pytest.approx(as_right["Back Knee"]["measured"])


def test_invalid_batting_hand_rejected():
    with pytest.raises(ValueError):
        analyse_stance(make_landmarks(LEFT_HANDER_STANCE), "none")


def test_mirroring_twice_is_identity():
    landmarks = make_landmarks(LEFT_HANDER_STANCE)
    twice = mirror_landmarks(mirror_landmarks(landmarks))
    for name, data in landmarks.items():
        assert twice[name]["Position"] == pytest.approx(data["Position"])
        assert twice[name]["Pixel"] == pytest.approx(data["Pixel"])


def test_knee_angle_uses_pixels_not_stretched_coordinates():
    # The same physical 90 degree knee filmed in a 9:16 portrait video.
    # Hip directly above the knee, ankle directly to the side, 300px each.
    width, height = 1080, 1920
    points = {
        "Right Hip": (540 / width, 600 / height),
        "Right Knee": (540 / width, 900 / height),
        "Right Ankle": (840 / width, 900 / height),
    }
    result = check_front_knee(make_landmarks(points, width, height))
    assert result["measured"] == pytest.approx(90, abs=0.01)


def test_low_visibility_gives_unknown():
    result = check_front_knee(make_landmarks(LEFT_HANDER_STANCE, visibility=0.3))
    assert result["status"] == "Unknown"
    assert result["measured"] is None


def test_front_shoulder_higher_says_lower_it():
    # y grows downwards, so a smaller y for the front (right) shoulder means it is higher
    points = dict(LEFT_HANDER_STANCE, **{"Right Shoulder": (0.58, 0.20), "Left Shoulder": (0.42, 0.28)})
    result = check_shoulder_position(make_landmarks(points))
    assert result["status"] == "Warning"
    assert "lower" in result["message"]


def test_level_head_passes_and_tilted_head_fails():
    level = check_head_position(make_landmarks(dict(LEFT_HANDER_STANCE, **{"Right Ear": (0.53, 0.15)})))
    tilted = check_head_position(make_landmarks(dict(LEFT_HANDER_STANCE, **{"Right Ear": (0.53, 0.25)})))
    assert level["status"] == "Pass"
    assert tilted["status"] == "Fail"
    assert "tilted" in tilted["message"]


def test_landmarks_for_check_swaps_sides_for_right_hander():
    assert landmarks_for_check("Front Knee", "left") == ["Right Knee"]
    assert landmarks_for_check("Front Knee", "right") == ["Left Knee"]
    assert landmarks_for_check("Head Position", "right") == ["Nose", "Right Ear", "Left Ear"]
