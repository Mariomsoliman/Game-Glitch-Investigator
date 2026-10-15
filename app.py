import random
import streamlit as st

from logic_utils import check_guess, get_range_for_difficulty, parse_guess, update_score


def start_new_round():
    # FIX: Initial setup, New Game, and difficulty changes each reset only part
    # of the round (attempts started at 1; New Game kept status, score, and
    # history and drew the secret from 1-100). Found in a Claude-assisted
    # review; this one helper now starts every round.
    low, high = get_range_for_difficulty(st.session_state.difficulty)
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.history = []
    st.session_state.status = "playing"
    st.session_state.feedback = []
    # Allowed here because this runs before the guess box is drawn
    # (initial setup, or a widget callback at the start of a rerun).
    st.session_state.guess_input = ""


st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
    key="difficulty",
    on_change=start_new_round,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if "secret" not in st.session_state:
    start_new_round()

st.subheader("Make a guess")

# FIX: The status line and debug panel were drawn before the submission was
# processed, so they showed the previous guess's values. Found in a
# Claude-assisted review; they keep their place on the page but are filled
# in at the end of the script.
status_area = st.container()
debug_area = st.expander("Developer Debug Info")

raw_guess = st.text_input("Enter your guess:", key="guess_input")

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    st.button("New Game 🔁", on_click=start_new_round)
with col3:
    show_hint = st.checkbox("Show hint", value=True)

# Submissions after a win or loss are ignored.
if submit and st.session_state.status == "playing":
    # FIX: The attempt was counted and raw input added to history before
    # validation. Found in a Claude-assisted review; rejected input now leaves
    # game state untouched.
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    if not ok:
        st.session_state.feedback = [("error", err)]
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        # FIX: The secret was converted to str on even attempts, causing
        # alphabetical comparisons. Found in a Claude-assisted review and AppTest
        # reproduction; the int secret is now always passed.
        outcome, message = check_guess(guess_int, st.session_state.secret)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )
        st.session_state.feedback = [("hint", message)]

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.session_state.feedback.append((
                "success",
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}",
            ))
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            st.session_state.feedback.append((
                "error",
                f"Out of attempts! "
                f"The secret was {st.session_state.secret}. "
                f"Score: {st.session_state.score}",
            ))

# Feedback is stored, so it stays visible on ordinary reruns.
for kind, text in st.session_state.feedback:
    if kind == "hint":
        if show_hint:
            st.warning(text)
    elif kind == "success":
        st.success(text)
    else:
        st.error(text)

if st.session_state.status != "playing":
    st.caption("Round over. Click New Game 🔁 to play again.")

with status_area:
    st.info(
        f"Guess a number between {low} and {high}. "
        f"Attempts left: {attempt_limit - st.session_state.attempts}"
    )

with debug_area:
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
