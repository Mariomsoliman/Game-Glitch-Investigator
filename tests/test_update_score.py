# These tests document the scoring rules as they currently exist. The
# assignment never specified scoring, so they pin down today's behavior
# (including its oddities) rather than endorse it.
import pytest

from logic_utils import update_score


@pytest.mark.parametrize("attempt_number, points", [
    (1, 80),   # first guess
    (2, 70),
    (8, 10),   # 100 - 90 = 10
    (9, 10),   # would be 0, but never less than 10
    (20, 10),
])
def test_win_points_shrink_with_attempts_but_never_below_10(attempt_number, points):
    assert update_score(0, "Win", attempt_number) == points


@pytest.mark.parametrize("attempt_number, change", [
    (1, -5),
    (2, +5),   # current oddity: a wrong guess on an even attempt adds points
    (3, -5),
    (4, +5),
])
def test_too_high_alternates_by_attempt_parity(attempt_number, change):
    assert update_score(10, "Too High", attempt_number) == 10 + change


@pytest.mark.parametrize("attempt_number", [1, 2, 3])
def test_too_low_always_subtracts_5(attempt_number):
    assert update_score(10, "Too Low", attempt_number) == 5


def test_unknown_outcome_leaves_score_unchanged():
    assert update_score(10, "Something else", 1) == 10


def test_score_can_go_negative():
    assert update_score(0, "Too Low", 1) == -5
