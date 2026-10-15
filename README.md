# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

- [x] Describe the game's purpose.
- [x] Detail which bugs you found.
- [x] Explain what fixes you applied.

**Purpose.** This is a number guessing game built with Streamlit. The player picks a difficulty, then tries to guess a secret whole number within that difficulty's range before running out of attempts. After each guess, the game says whether to go higher or lower.

**Bugs I found.** I started from my own browser game, where the attempt counter, debug panel, and final message disagreed with each other. I then investigated with Claude (code reading plus AppTest reproductions). The full evidence is in Section 1 of `reflection.md`. The main bugs were:

1. The high/low hint messages were reversed.
2. On every even attempt, the secret was turned into text, so guesses were compared alphabetically (`"10" < "9"`). Together with bug 1, this made the same guess get opposite hints on different attempts.
3. Invalid text, decimals, and out-of-range numbers were accepted or still used up an attempt. Decimals were silently truncated (`9.7` became `9`).
4. The attempt counter started at 1, so you got one fewer guess than advertised.
5. "Attempts left" and the debug panel were drawn before the guess was processed, so they always showed the previous values.
6. New Game did not reset status, score, or history, and always picked the secret from 1–100, even on Easy.
7. Switching difficulty kept the old secret, even when it was outside the new range.
8. The prompt always said "between 1 and 100", whatever the difficulty.

**Fixes I applied.**

- **Hints and comparisons:** swapped the reversed hint messages, always passed the secret as an integer, and removed the alphabetical-comparison fallback. A type mix-up now raises an error instead of giving a wrong hint.
- **Input validation:** only whole numbers inside the selected range are accepted, and surrounding spaces are allowed. Rejected input shows an error and changes nothing else.
- **Round setup:** one small helper, `start_new_round()`, starts every round (first load, New Game, and difficulty change). It resets attempts, score, history, status, the guess box, and old feedback, and picks the secret from the selected range.
- **Displays and game over:** attempts and the debug panel are filled in after the guess is processed. You get exactly the advertised number of guesses, and guesses after a win or loss are ignored. The last hint or result stays visible on ordinary reruns, and balloons only appear on the winning guess.
- **Refactor:** moved `get_range_for_difficulty`, `parse_guess`, `check_guess`, and `update_score` into `logic_utils.py`, and added regression tests (unit tests plus Streamlit AppTest).

**Not changed: scoring.** The assignment never defined scoring rules, so I kept the existing formula and only documented it (see the `update_score` docstring and `tests/test_update_score.py`):

- A win adds `100 - 10 × (attempt number + 1)`, with a minimum of 10. For example, a first-guess win adds 80.
- "Too Low" always subtracts 5.
- "Too High" adds 5 on even-numbered attempts and subtracts 5 on odd ones. That is an oddity I noticed but did not change.
- Scores can go negative.

Because the attempt counter now correctly starts at 0, each guess has an attempt number one lower than in the original code. So the same formula gives different numbers than before (for example, a first-guess win used to score 70).

## 📸 Demo Walkthrough

Describe your fixed game in numbered steps so a reader can follow along without watching a video:

1. Install the requirements and start the app with `python -m streamlit run app.py`.
2. In the sidebar, choose a difficulty. The sidebar shows its range and attempt limit (Easy: 1–20, 6 attempts; Normal: 1–100, 8 attempts; Hard: 1–50, 5 attempts). The prompt above the guess box shows the same range and how many attempts are left. Changing difficulty starts a fresh round.
3. Type a whole number in the guess box and click **Submit Guess 🚀**. A hint tells you to go higher or lower, and "Attempts left" goes down by one right away. Unticking **Show hint** hides the hint without changing the round.
4. If you type something invalid (text, a decimal like `9.7`, or a number outside the range), the game shows an error and does not use up an attempt.
5. Keep guessing. A correct guess shows "Correct!", balloons, and your final score. If your last allowed guess is wrong, the game shows "Out of attempts!" and reveals the secret. Further submissions are ignored until you start a new round.
6. Click **New Game 🔁** to start over. Attempts, score, and history reset, the guess box clears, and a new secret is picked from the selected range.

*Example game (illustrative only, not a recorded browser run; the values come from the current scoring rules and were checked with an automated AppTest run):* on Easy with a secret of 13, entering `25` shows "Enter a number from 1 to 20." and `abc` shows "Enter a whole number, like 42." Neither uses an attempt, so it still says "Attempts left: 6". Guessing `10` shows "Go HIGHER!" (5 left, score −5). Guessing `15` shows "Go LOWER!" (4 left, score 0). Guessing `13` shows "Correct!" and "You won! The secret was 13. Final score: 60".

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

Final suite, run by Claude after the last change (moving `update_score`), with pytest's session header omitted because it contains a local file path. My own most recent local run, before that last change, passed all 68 tests that existed then in 2.94 seconds.

```
$ pytest
collected 82 items

tests/test_app_flow.py ................                                  [ 19%]
tests/test_game_logic.py .........                                       [ 30%]
tests/test_parse_guess.py .........................                      [ 60%]
tests/test_round_lifecycle.py ..................                         [ 82%]
tests/test_update_score.py ..............                                [100%]

============================== 82 passed in 2.48s ==============================
```

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
