import pytest

from core.geometry import calculate_angle, calculate_distance, in_range, midpoint


def test_right_angle():
    assert calculate_angle((1, 0), (0, 0), (0, 1)) == pytest.approx(90)


def test_straight_line_is_180_degrees():
    assert calculate_angle((-1, 0), (0, 0), (1, 0)) == pytest.approx(180)


def test_angle_with_zero_length_side_is_none():
    assert calculate_angle((0, 0), (0, 0), (1, 1)) is None


def test_distance_and_midpoint():
    assert calculate_distance((1, 2), (4, 6)) == pytest.approx(5)
    assert midpoint((2, 2), (4, 4)) == (3, 3)


def test_in_range_is_inclusive():
    assert in_range(130, 130, 160)
    assert in_range(160, 130, 160)
    assert not in_range(160.01, 130, 160)
