from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def start_game(secret, difficulty="Normal"):
    at = AppTest.from_file(APP_PATH, default_timeout=10).run()
    if difficulty != "Normal":
        at.selectbox[0].select(difficulty).run()
    at.session_state["secret"] = secret
    return at


def submit(at, guess):
    at.text_input[0].input(guess)
    next(b for b in at.button if b.label.startswith("Submit")).click().run()
    assert not at.exception, f"app raised: {at.exception}"


def hint(at):
    return at.warning[0].value


def submit_repeatedly(secret, guess, expected, other):
    # Four submissions in a row cover both even and odd attempt counts,
    # whether the attempt counter starts at 0 or 1.
    at = start_game(secret)
    for n in range(1, 5):
        submit(at, guess)
        attempts = at.session_state["attempts"]
        assert expected in hint(at) and other not in hint(at), (
            f"submission {n} (attempts={attempts}): expected {expected}, got {hint(at)!r}"
        )


def test_same_high_guess_gets_same_hint_every_attempt():
    submit_repeatedly(secret=9, guess="10", expected="LOWER", other="HIGHER")


def test_same_low_guess_gets_same_hint_every_attempt():
    submit_repeatedly(secret=10, guess="9", expected="HIGHER", other="LOWER")


def test_win_on_first_submission():
    at = start_game(secret=9)
    submit(at, "9")
    assert at.session_state["status"] == "won"
    assert "You won" in at.success[0].value


def test_win_on_second_submission():
    # Winning on the next submission flips the attempt-count parity.
    at = start_game(secret=9)
    submit(at, "5")
    submit(at, "9")
    assert at.session_state["status"] == "won"
    assert "You won" in at.success[0].value


def game_state(at):
    ss = at.session_state
    return {
        "attempts": ss["attempts"],
        "score": ss["score"],
        "history": list(ss["history"]),
        "secret": ss["secret"],
        "status": ss["status"],
    }


@pytest.mark.parametrize("raw", ["", "   ", "abc", "9.7", "9.0", "0", "101"])
def test_rejected_input_leaves_game_state_unchanged(raw):
    at = start_game(secret=50)
    submit(at, "40")  # one accepted guess first, so the state is not all defaults
    before = game_state(at)
    submit(at, raw)
    assert game_state(at) == before
    assert at.error, "rejected input should show an error message"
    assert not at.warning, "rejected input should not show a hint"


def test_rejected_input_on_last_attempt_does_not_use_it_up():
    at = start_game(secret=50)
    while at.session_state["attempts"] < 7:  # Normal allows 8; leave one attempt
        submit(at, "40")
    before = game_state(at)
    submit(at, "abc")
    assert game_state(at) == before
    assert at.session_state["status"] == "playing"


def test_accepted_submission_updates_attempts_and_history_once():
    at = start_game(secret=50)
    before = game_state(at)
    submit(at, " 12 ")
    after = game_state(at)
    assert after["attempts"] == before["attempts"] + 1
    assert after["history"] == before["history"] + [12]
    assert after["secret"] == before["secret"]
    assert at.warning, "an accepted guess should show a hint"


@pytest.mark.parametrize("difficulty, low, high", [
    ("Easy", 1, 20),
    ("Normal", 1, 100),
    ("Hard", 1, 50),
])
def test_range_boundaries_follow_difficulty(difficulty, low, high):
    at = start_game(secret=(low + high) // 2, difficulty=difficulty)
    for raw in (str(low), str(high)):
        before = game_state(at)
        submit(at, raw)
        assert game_state(at)["history"] == before["history"] + [int(raw)], f"{raw} should be accepted"
    for raw in (str(low - 1), str(high + 1)):
        before = game_state(at)
        submit(at, raw)
        assert game_state(at) == before, f"{raw} should be rejected on {difficulty}"
