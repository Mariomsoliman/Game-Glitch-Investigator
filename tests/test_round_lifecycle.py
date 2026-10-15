import json
import random
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")

RANGES = {"Easy": (1, 20), "Normal": (1, 100), "Hard": (1, 50)}
LIMITS = {"Easy": 6, "Normal": 8, "Hard": 5}
DIFFICULTIES = ["Easy", "Normal", "Hard"]


@pytest.fixture
def randint_calls(monkeypatch):
    # Controlled randomness: randint always returns its upper bound (so the
    # secret is predictable) and records the bounds it was called with.
    calls = []

    def fake_randint(low, high):
        calls.append((low, high))
        return high

    monkeypatch.setattr(random, "randint", fake_randint)
    return calls


def open_app(difficulty="Normal"):
    at = AppTest.from_file(APP_PATH, default_timeout=10).run()
    if difficulty != "Normal":
        at.selectbox[0].select(difficulty).run()
    return at


def click(at, label):
    next(b for b in at.button if b.label.startswith(label)).click().run()
    assert not at.exception, f"app raised: {at.exception}"


def submit(at, guess):
    at.text_input[0].input(guess)
    click(at, "Submit")


def rerun_without_action(at):
    at.checkbox[0].uncheck().run()
    at.checkbox[0].check().run()


def game_state(at):
    ss = at.session_state
    return {
        "attempts": ss["attempts"],
        "score": ss["score"],
        "history": list(ss["history"]),
        "secret": ss["secret"],
        "status": ss["status"],
    }


def fresh_round(secret):
    return {"attempts": 0, "score": 0, "history": [], "secret": secret, "status": "playing"}


def info_text(at):
    return " ".join(i.value for i in at.info)


def debug_text(at):
    return " ".join(m.value for m in at.markdown)


def finish_round(at, outcome):
    # With controlled randomness the secret is the range's upper bound, and
    # 1 is always a wrong guess.
    if outcome == "won":
        submit(at, str(at.session_state["secret"]))
    else:
        while at.session_state["status"] == "playing":
            submit(at, "1")
    assert at.session_state["status"] == outcome, "could not finish the round"


def test_initial_round(randint_calls):
    at = open_app()
    assert game_state(at) == fresh_round(secret=100)
    assert randint_calls == [(1, 100)]
    assert "between 1 and 100" in info_text(at)
    assert "Attempts left: 8" in info_text(at)


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_wrong_final_guess_loses_after_exactly_the_allowed_guesses(randint_calls, difficulty):
    limit = LIMITS[difficulty]
    at = open_app(difficulty)
    for n in range(1, limit):
        submit(at, "1")
        assert at.session_state["status"] == "playing", f"round ended after {n} of {limit} guesses"
    submit(at, "1")
    assert at.session_state["status"] == "lost"
    assert at.session_state["attempts"] == limit
    assert len(at.session_state["history"]) == limit
    assert any("Out of attempts" in e.value for e in at.error)
    assert "Attempts left: 0" in info_text(at)


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_correct_final_guess_wins(randint_calls, difficulty):
    low, high = RANGES[difficulty]
    limit = LIMITS[difficulty]
    at = open_app(difficulty)
    for n in range(1, limit):
        submit(at, str(low))
        assert at.session_state["status"] == "playing", f"round ended after {n} of {limit} guesses"
    submit(at, str(high))
    assert at.session_state["status"] == "won"
    assert at.session_state["attempts"] == limit
    assert any("You won" in s.value for s in at.success)


@pytest.mark.parametrize("outcome", ["won", "lost"])
def test_submissions_after_round_over_are_ignored(randint_calls, outcome):
    at = open_app()
    finish_round(at, outcome)
    before = game_state(at)
    for raw in ("100", "1", "abc"):
        submit(at, raw)
        assert game_state(at) == before, f"submitting {raw!r} after the round changed state"
        assert not at.get("balloons"), "balloons repeated after the round was over"
    if outcome == "won":
        assert any("You won" in s.value for s in at.success), "win result is no longer shown"
    else:
        assert any("Out of attempts" in e.value for e in at.error), "loss result is no longer shown"


@pytest.mark.parametrize("outcome", ["won", "lost"])
def test_new_game_resets_round(randint_calls, outcome):
    at = open_app()
    finish_round(at, outcome)
    at.text_input[0].input("7").run()  # leave text in the guess box
    calls_before = len(randint_calls)
    click(at, "New Game")
    assert game_state(at) == fresh_round(secret=100)
    assert randint_calls[calls_before:] == [(1, 100)]
    assert at.text_input[0].value == "", "guess box was not cleared"
    assert not (at.success or at.error or at.warning), "previous feedback is still shown"
    assert "Attempts left: 8" in info_text(at)


def test_switching_difficulty_starts_fresh_round_and_switching_back(randint_calls):
    at = open_app()
    submit(at, "1")
    at.text_input[0].input("5").run()

    at.selectbox[0].select("Easy").run()
    assert game_state(at) == fresh_round(secret=20)
    assert randint_calls[-1] == (1, 20)
    assert at.text_input[0].value == ""
    assert not (at.success or at.error or at.warning)
    assert "between 1 and 20" in info_text(at)
    assert "Attempts left: 6" in info_text(at)

    submit(at, "1")
    at.selectbox[0].select("Normal").run()
    assert game_state(at) == fresh_round(secret=100)
    assert randint_calls[-1] == (1, 100)
    assert "between 1 and 100" in info_text(at)
    assert "Attempts left: 8" in info_text(at)


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_secret_is_drawn_from_selected_range(randint_calls, difficulty):
    low, high = RANGES[difficulty]
    at = open_app(difficulty)
    assert randint_calls[-1] == (low, high)
    assert at.session_state["secret"] == high
    click(at, "New Game")
    assert randint_calls[-1] == (low, high)
    assert at.session_state["secret"] == high


def test_ordinary_reruns_keep_the_round(randint_calls):
    at = open_app()
    submit(at, "40")
    before = game_state(at)
    calls_before = len(randint_calls)
    hint = at.warning[0].value

    at.checkbox[0].uncheck().run()
    assert game_state(at) == before
    assert not at.warning, "hint should hide when 'Show hint' is off"

    at.checkbox[0].check().run()
    assert [w.value for w in at.warning] == [hint], "latest hint should come back"

    at.text_input[0].input("41").run()  # typing without submitting
    assert game_state(at) == before
    assert len(randint_calls) == calls_before, "secret was regenerated on a rerun"


def test_displays_reflect_state_right_after_submission(randint_calls):
    at = open_app()
    for guess in ("40", "60"):
        submit(at, guess)
        state = game_state(at)
        assert f"Attempts left: {8 - state['attempts']}" in info_text(at)
        assert f"Attempts: `{state['attempts']}`" in debug_text(at)
        assert f"Score: `{state['score']}`" in debug_text(at)
        assert json.loads(at.json[0].value) == state["history"]


def test_balloons_only_on_the_winning_submission(randint_calls):
    at = open_app()
    submit(at, "100")
    assert at.get("balloons"), "winning should release balloons"
    win_messages = [s.value for s in at.success]
    rerun_without_action(at)
    assert not at.get("balloons"), "balloons repeated on an ordinary rerun"
    assert [s.value for s in at.success] == win_messages, "win result should stay visible"
