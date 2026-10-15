import pytest

from logic_utils import check_guess


def assert_says(message, direction):
    # Check the direction word, not the exact text, so emoji/wording tweaks
    # don't break the test but a reversed hint does.
    opposite = "HIGHER" if direction == "LOWER" else "LOWER"
    assert direction in message, f"expected a {direction} hint, got {message!r}"
    assert opposite not in message, f"hint also says {opposite}: {message!r}"


def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    outcome, message = check_guess(50, 50)
    assert outcome == "Win"
    assert "Correct" in message

def test_guess_too_high():
    # If secret is 50 and guess is 60, outcome is "Too High" and the hint says go LOWER
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"
    assert_says(message, "LOWER")

def test_guess_too_low():
    # If secret is 50 and guess is 40, outcome is "Too Low" and the hint says go HIGHER
    outcome, message = check_guess(40, 50)
    assert outcome == "Too Low"
    assert_says(message, "HIGHER")


@pytest.mark.parametrize("guess, secret, outcome, direction", [
    (51, 50, "Too High", "LOWER"),   # one above the secret
    (49, 50, "Too Low", "HIGHER"),   # one below the secret
    (10, 9, "Too High", "LOWER"),    # numeric order: 10 > 9, alphabetical: "10" < "9"
    (100, 9, "Too High", "LOWER"),   # numeric order: 100 > 9, alphabetical: "100" < "9"
    (9, 10, "Too Low", "HIGHER"),    # numeric order: 9 < 10, alphabetical: "9" > "10"
])
def test_numeric_comparison(guess, secret, outcome, direction):
    result_outcome, message = check_guess(guess, secret)
    assert result_outcome == outcome
    assert_says(message, direction)


def test_type_mismatch_fails_loudly():
    # A str secret should raise instead of silently comparing text alphabetically.
    with pytest.raises(TypeError):
        check_guess(10, "9")
