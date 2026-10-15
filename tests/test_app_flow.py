from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def start_game(secret):
    at = AppTest.from_file(APP_PATH, default_timeout=10).run()
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
