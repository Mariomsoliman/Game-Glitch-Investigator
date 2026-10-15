def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str, low: int, high: int):
    """
    Parse user input into a whole-number guess within [low, high] (inclusive).

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    # FIX: Decimals were silently truncated ("9.7" -> 9) and out-of-range
    # values were accepted. Found in a Claude-assisted review; whole numbers
    # in the difficulty's range are now the only valid guesses.
    if raw is None or raw.strip() == "":
        return False, None, "Enter a guess."

    try:
        value = int(raw.strip())
    except ValueError:
        return False, None, "Enter a whole number, like 42."

    if not low <= value <= high:
        return False, None, f"Enter a number from {low} to {high}."

    return True, value, None


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"
    """
    if guess == secret:
        return "Win", "🎉 Correct!"

    # FIX: Hint messages were reversed, and a TypeError fallback compared str
    # values alphabetically ("10" < "9"). Found in a Claude-assisted review of my
    # gameplay notes; I swapped the messages and removed the fallback so a type
    # mismatch raises instead of giving a wrong hint.
    if guess > secret:
        return "Too High", "📉 Go LOWER!"
    return "Too Low", "📈 Go HIGHER!"


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")
