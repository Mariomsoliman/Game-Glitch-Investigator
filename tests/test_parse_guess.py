import pytest

from logic_utils import parse_guess


def assert_rejected(result):
    ok, value, err = result
    assert ok is False, f"expected rejection, got {result!r}"
    assert value is None, f"rejected input must not produce a value, got {value!r}"
    assert err, "rejected input must come with an error message"


@pytest.mark.parametrize("raw, low, high, expected", [
    ("1", 1, 100, 1),       # Normal lower boundary
    ("100", 1, 100, 100),   # Normal upper boundary
    ("20", 1, 20, 20),      # Easy upper boundary
    ("50", 1, 50, 50),      # Hard upper boundary
    (" 12 ", 1, 100, 12),   # surrounding spaces
    ("\t7\n", 1, 100, 7),   # surrounding tab/newline
])
def test_accepts_whole_numbers_in_range(raw, low, high, expected):
    assert parse_guess(raw, low, high) == (True, expected, None)


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_rejects_empty_input(raw):
    assert_rejected(parse_guess(raw, 1, 100))


@pytest.mark.parametrize("raw", ["abc", "abc ", "=", "h", "12abc", "1 2"])
def test_rejects_nonnumeric_text(raw):
    assert_rejected(parse_guess(raw, 1, 100))


@pytest.mark.parametrize("raw", ["9.7", "9.0", "9.", ".5", "1e2"])
def test_rejects_decimal_notation_without_truncating(raw):
    assert_rejected(parse_guess(raw, 1, 100))


@pytest.mark.parametrize("raw, low, high", [
    ("0", 1, 100),     # just below Normal
    ("101", 1, 100),   # just above Normal
    ("-5", 1, 100),    # negative
    ("21", 1, 20),     # just above Easy
    ("51", 1, 50),     # just above Hard
])
def test_rejects_out_of_range(raw, low, high):
    result = parse_guess(raw, low, high)
    assert_rejected(result)
    # The message should tell the player the valid range.
    assert str(low) in result[2] and str(high) in result[2]
