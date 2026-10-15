# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").

When I first ran the game, the interface loaded and I could submit guesses, but its feedback was inconsistent. In one game with a secret of 9, the top showed one attempt remaining while the result said I was out of attempts. The debug panel showed a score of −45, but the final message showed −50. My history also contained text and numbers outside the displayed range. I used Claude to investigate these observations and traced additional problems to reversed hints, string comparisons, and incomplete game resets.

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error | Suspected Code Location | Evidence Source |
|-------|-------------------|-----------------|------------------------|-------------------------|-----------------|
| Normal, secret 50. Fresh session, submit `60`, `40`, `60`, `70` in order. | 60 → "Go LOWER!", 40 → "Go HIGHER!", 60 → "Go LOWER!", 70 → "Go LOWER!" | "Go HIGHER!", "Go LOWER!", "Go HIGHER!", "Go HIGHER!" (every hint points the wrong way) | No Python exception raised in the AppTest run | `app.py`, `check_guess`, lines 37–40: the "Too High" outcome returns "Go HIGHER!" and "Too Low" returns "Go LOWER!" | Claude-assisted AppTest reproduction; cause confirmed by my code review |
| Normal, secret 9. Fresh session, submit `10`, `10`, `100` in order. | The same guess always gets the same hint; 10 and 100 are both above 9, so each should be "Too High" with the hint "Go LOWER!" | Displayed hints: `10` → "Go LOWER!", `10` → "Go HIGHER!", `100` → "Go LOWER!". Outcomes from direct `check_guess` calls with the same arguments: `check_guess(10, "9")` → "Too Low", `check_guess(10, 9)` → "Too High", `check_guess(100, "9")` → "Too Low". This row shows two bugs **interacting**, not an isolated type bug: on even attempts the string comparison produces the wrong outcome, and the reversed message then turns it into a hint that happens to point the right way. On odd attempts the outcome is correct but the message is reversed | No Python exception raised in the AppTest run | `app.py` submit handler, lines 158–161 (secret becomes a `str` when `attempts` is even); `check_guess` `TypeError` fallback, lines 41–47 (compares text alphabetically, so `"10" < "9"`); reversed messages at lines 38/40 and 46/47 | Claude-assisted AppTest reproduction (displayed hints); Claude-assisted direct `check_guess` calls (outcome labels); causes confirmed by my code review |
| Normal (8 attempts allowed), secret 9. Played until the game ended. | When the game ends, "Attempts left" shows 0 and the debug panel matches the final score | Top showed "Attempts left: 1" and debug showed Attempts: 7, Score: -45, while the final message said "Out of attempts! The secret was 9. Score: -50." | Not recorded | `app.py` lines 109–119 draw "Attempts left" and the debug panel **before** the submit handler (lines 147–188) updates `attempts` and `score` on the same rerun | Browser observation (my game). Claude-assisted AppTest reproduction produced the same values, assuming New Game was clicked after the 4th entry and a final guess of `5` (neither confirmed from my game) |
| Normal, fresh session. Submit `abc`, then `-5`. | UI says "Guess a number between 1 and 100", so `-5` should be rejected. Invalid text should not count as a guess (assumption: README does not define this) | `abc`: "That is not a number." but attempts still went 1 → 2 and `"abc"` was added to history. `-5`: accepted with no range error, given a hint, and scored −5 | No Python exception raised in the AppTest run | `app.py` line 148 (attempt counted before parsing); line 153 (raw invalid text appended to history); `parse_guess`, lines 14–29 (no range check; `low`/`high` from line 87 never used) | Browser observation (my game history contained `"="`, `"h"`, `0`, `-1`, `-2`, `-20`, `-30`). Claude-assisted AppTest reproduction for the `abc` / `-5` steps |
| Normal, fresh session, secret 9. Submit `50` until the game ends. | 8 guesses allowed, matching "Attempts allowed: 8" | Fresh game showed "Attempts left: 7"; the game ended after the 7th submission | No Python exception raised in the AppTest run | `app.py` line 96: `attempts` starts at `1` instead of `0` | Claude-assisted AppTest reproduction |
| Normal. Lose a game, then click "New Game" and submit a guess. | A new, playable game with attempts, score, history, and status reset | "Attempts left: 8" and "Game over. Start a new game to try again." shown together; guesses are ignored. Score and history carried over from the old game | No Python exception raised in the AppTest run | `app.py` New Game handler, lines 134–138: resets `attempts` (to 0) and `secret` only, not `status`, `score`, or `history` | Claude-assisted AppTest reproduction |

*Note on evidence: AppTest runs used Streamlit's `streamlit.testing.v1.AppTest` to simulate clicks headlessly; the secret was set directly in `st.session_state` to make results repeatable. I have not yet manually repeated those exact steps in the browser.*

*Note on code references: the file names and line numbers in this table refer to the original code at commit `481fa66`. This log is kept as a historical record; later changes moved `check_guess` into `logic_utils.py`, so current line numbers differ.*

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

**Deciding whether a bug was fixed.** I only counted a bug as fixed if a test failed before the fix and passed after it, without changing the test's assertions. Before the fixes, a Claude-run `pytest` against the moved but still-buggy `check_guess` reported 10 failed and 3 passed. Every failure was either a hint pointing the wrong way or the string-comparison fallback not raising `TypeError`. After the fixes, my own local run of `python -m pytest -v` passed all 13 tests in 0.97 seconds. I then played one game in the browser as a final check.

**Tests I ran and what they showed.**
- *Unit tests (`tests/test_game_logic.py`):* these check both the outcome and the hint direction for higher, lower, and equal guesses. They also cover guesses one away from the secret, cases where number order and alphabetical order disagree (`10` vs `9`, `100` vs `9`, `9` vs `10`), and a `str` secret, which must now raise `TypeError`. The original starter tests only checked the outcome label, which was already correct, so they could not have caught the reversed hints.
- *AppTest (`tests/test_app_flow.py`, Claude-assisted):* these submit the same guess four times in a row, so both even and odd attempt counts are covered, and check winning on either parity. Before the fix, both repeated-guess tests failed on submission 2 (attempts=3) because the hint flipped. I have not manually verified repeated directional hints in the browser; that evidence comes from AppTest only.
- *Browser (manual):* the secret was 78, and submitting `78` displayed "Correct!" and "You won! The secret was 78. Final score: 30." This confirms winning works after the refactor. On its own it does not prove the comparison fix, because wins already worked before the fix (the two AppTest win tests passed both before and after). The debug panel still showed the pre-submission values Attempts 4, Score -10, and history `[55, "abc ", 9]`, so the display-lag bug remains, and invalid text is still recorded in history.

**How AI helped with tests.** Claude proposed the regression tests. It suggested checking the hint direction and not just the outcome label, using values where alphabetical and numeric order disagree, and using AppTest for the submit handler, which unit tests on `check_guess` cannot reach. Claude also ran the suite before the fixes and showed which tests failed and why. I ran the final suite locally myself.

**Repaired vs. remaining**

| Bug (see Section 1) | Status | Evidence |
|---------------------|--------|----------|
| Reversed high/low hint messages | Repaired | Unit tests failed before the fix and pass after; my local run passed 13/13 |
| Secret converted to `str` on even attempts, plus the string-comparison fallback | Repaired | AppTest repeated-guess tests failed before the fix and pass after; `test_type_mismatch_fails_loudly` passes |
| "Attempts left" and debug panel drawn before the submit handler (display lag) | Remaining | My browser game (secret 78) still showed pre-submission debug values |
| Invalid input recorded in history and counted as an attempt; no range check | Remaining | My browser game history contained `"abc "`; Section 1 table |
| Attempt counter starts at 1 | Remaining | Section 1 table (Claude-assisted AppTest) |
| New Game does not reset status, score, or history | Remaining | Section 1 table (Claude-assisted AppTest) |

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
