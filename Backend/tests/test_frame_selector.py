import pytest

from core.frame_selector import VideoTooShortError, select_best_frame
from core.pose_extractor import VideoPose
from tests.helpers import LEFT_HANDER_STANCE, make_landmarks


def make_video(visibilities, fps=10):
    frames = [None if v is None else make_landmarks(LEFT_HANDER_STANCE, visibility=v) for v in visibilities]
    return VideoPose(fps=fps, width=1000, height=1000, frames=frames)


def test_picks_most_visible_frame_inside_window():
    # 3 seconds at 10 fps; the most visible frame overall (index 0) is outside the 1-2s window
    visibilities = [1.0] + [0.5] * 9 + [0.6, 0.9, 0.7, None, 0.8] + [0.5] * 15
    frame_index, _, visibility = select_best_frame(make_video(visibilities), 1, 2)
    assert frame_index == 11
    assert visibility == pytest.approx(0.9)


def test_no_pose_in_window_returns_none():
    assert select_best_frame(make_video([0.9] * 10 + [None] * 10 + [0.9] * 10), 1, 2) is None


def test_too_short_video_raises():
    with pytest.raises(VideoTooShortError):
        select_best_frame(make_video([0.9] * 15), 1, 2)
