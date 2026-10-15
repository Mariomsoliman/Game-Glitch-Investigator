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

**AI tools.** I used two AI tools: Claude, through Claude Code in VS Code, and ChatGPT. Claude edited files and ran automated investigations, such as Streamlit AppTest reproductions and test runs. ChatGPT helped me understand concepts, review Claude's plans and diffs, question the score-drop inference, and follow the Git and testing workflow. I made the decisions about scope, and I did the browser checks and my local test runs myself.

**A suggestion I accepted.** The starter tests compared `check_guess` to a plain string like `"Win"`, but the function returns an `(outcome, message)` pair. Claude suggested keeping the pair and updating the tests to check both the outcome and the hint direction. It pointed out that the outcome labels were already correct, so the starter tests could never have caught the reversed hints. I verified this by seeing the new tests fail on the old code (a Claude-run `pytest` showed 10 failed, 3 passed), all for the expected reasons. After the fix, my own local run passed all 13 tests.

**A suggestion I changed.** In a draft of my bug log, Claude wrote that a guess of `100` was scored as "Too Low" because the score went down by 5. With ChatGPT's help, I questioned that, because a score drop can't prove the outcome: both "Too Low" and "Too High" (on odd attempts) subtract 5. Instead, we called `check_guess` directly with the same arguments the game would pass. `check_guess(100, "9")` returned `"Too Low"`, so the claim stayed, but now it rests on direct evidence and is labeled that way in Section 1.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

**Deciding whether a bug was fixed.** I only counted a bug as fixed if a test failed on the old code and passed after the fix, without loosening the test. For each repair, Claude ran the new tests against the unfixed code first. The results were 10 failed for the hint and comparison fix, 20 failed for input validation, and 17 failed for the round lifecycle, each for the expected reason. After each fix, the full suite passed, and I ran it locally myself (13 tests in 0.97 seconds, then 50, then 68 in 2.94 seconds). For behavior that tests can't fully show, I also checked the game in my browser.

**A test I ran and what it showed.** One useful Claude-assisted AppTest submits the same guess four times in a row, so it covers both even and odd attempt counts. Before the fix, it failed on the second submission because the hint flipped, which proved the comparison bug depended on the attempt count. The first submission passed by coincidence, because the two bugs cancelled each other out, so a single manual guess could easily have fooled me. In the browser, I confirmed three things after the round-lifecycle repair: New Game resets after a win, Easy shows the correct range and attempt limit, and toggling Show hint keeps the round. I have not manually checked repeated directional hints in the browser; that evidence comes from AppTest only.

**How AI helped with tests.** Claude proposed most of the regression tests and explained why each one was needed. For example, it suggested checking the hint direction and not just the outcome label, and using values where alphabetical and numeric order disagree. It also suggested AppTest for the submit handler, which unit tests can't reach, and a fake `random.randint` so secret-range bugs show up on the first try instead of by luck. I decided which behaviors were in scope, and I ran the final suites locally.

**Repair status** *(commit references show where each repair was committed)*

| Bug (see Section 1) | Status | Evidence |
|---------------------|--------|----------|
| Reversed high/low hint messages | Repaired (`d027945`) | Unit tests failed before the fix and pass after; my local run passed 13/13 |
| Secret converted to `str` on even attempts, plus the string-comparison fallback | Repaired (`d027945`) | Claude-assisted AppTest repeated-guess tests failed before and pass after; `test_type_mismatch_fails_loudly` passes |
| Invalid input counted as an attempt and recorded in history; decimals truncated; no range check | Repaired (`ceca5b0`) | Claude-run tests: 20 failed before, 50 passed after; my local run passed all 50 |
| Attempt counter starts at 1 | Repaired (`c280bf8`) | Claude-assisted AppTest: limit tests failed before, pass after; my browser check: Easy shows the correct range and attempt limit |
| "Attempts left" and debug panel drawn before the guess is processed (display lag) | Repaired (`c280bf8`) | Claude-assisted AppTest: display test failed before, passes after. Not separately checked in my browser |
| New Game does not reset status, score, or history | Repaired (`c280bf8`) | Claude-assisted AppTest: reset tests failed before, pass after; my browser check: New Game resets after a win |
| New Game and difficulty switch drew the secret from the wrong range or kept the old one (found during investigation) | Repaired (`c280bf8`) | Claude-assisted AppTest with a controlled `random.randint` |
| Scoring oddities (for example, +5 for a "Too High" guess on even attempts) | Not changed | Scoring rules were never specified; current behavior is documented in `update_score` and `tests/test_update_score.py` |

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

When a widget interaction is submitted, such as clicking a button, toggling a checkbox, or applying a text-input change, Streamlit runs your whole script again from top to bottom. That's a "rerun". Normal variables are rebuilt from scratch on each rerun, so anything the game needs to remember, like the secret, attempts, and score, has to live in `st.session_state`, which survives between reruns. Order matters too: in this game, the attempts and debug panel were drawn before the guess was processed, so they always showed the previous values. I also learned that a widget's stored value can't be changed after the widget is drawn in the same run, so resetting the guess box has to happen in a button callback, which runs before the page is drawn.

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.

**A habit I want to keep.** I want to keep writing a regression test, watching it fail on the broken code, and only then fixing the bug. Seeing the test fail for the right reason showed me that the test actually catches the bug, and seeing it pass afterwards gave me real evidence that the fix worked. I also want to keep labeling where each piece of evidence came from: my browser, my local test run, or an AI-assisted run.

**Something I'd do differently.** Next time I'll write down exact steps while testing in the browser. My first game's notes didn't record my final guess or whether I had clicked New Game, so we could only guess at part of what happened. I'd also ask the AI to separate what it has verified from what it is inferring before I accept a conclusion, since the score-drop claim looked convincing until we checked it directly.

**How this changed my view of AI-generated code.** AI-generated code can look finished and still hide several bugs that cover for each other. Now I treat AI output, including my AI teammate's suggestions, as a hypothesis to test, not as an answer.
