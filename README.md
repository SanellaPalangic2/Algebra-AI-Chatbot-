# 🤖 Algebra Quest

A kid-friendly AI algebra tutor for middle schoolers (ages 11–14), built with **Python + Flask** and the **Claude API**.

- **7 levels** on a colorful quest map: Variables → Order of Operations → Like Terms → One-Step Equations → Two-Step Equations → Distributive Property → Inequalities
- **AI-written lessons** in age-friendly language, with an *"Explain it another way"* button
- **Practice problems** at the end of every lesson — fresh random numbers each time, 2 tries per problem, hints on mistakes
- **Levels unlock in order**: score 4 out of 5 to unlock the next one. Answers are checked on the server, so kids can't skip ahead by peeking at the page.
- **Algebot chat** on every screen — asks guiding questions instead of just giving practice answers, stays on-topic, and never asks for personal info
- Works even without an API key (uses built-in lessons; chat is turned off)

[demo link](https://algebra-quest.onrender.com/)

## How it works
| File | What it does |
|---|---|
| `app.py` | Flask server: lessons, practice, answer checking, level unlocking, Algebot chat |
| `lessons.py` | The 7 levels, built-in backup lessons, and random problem generators |
| `templates/index.html`, `static/` | The kid-friendly interface |
| `render.yaml` | One-click Render setup |
| `test_app.py` | Tests for answer checking and level locking |

**Progress** is saved in a signed browser cookie (no database, no accounts, no personal info). Each browser/device keeps its own progress; clearing cookies or clicking **↺ Reset** starts over.

**Changing things**
- Pass mark / problems per set: `PASS_SCORE` and `PROBLEMS_PER_SET` in `lessons.py`
- Add a level: add a dictionary to `LESSONS` in `lessons.py` with a few generator functions
- AI model: set `ANTHROPIC_MODEL` (default `claude-haiku-4-5-20251001`, fast and inexpensive; use `claude-sonnet-5-5` for richer lessons)
- Tutor personality/rules: `TUTOR_SYSTEM` in `app.py`

## Cost & safety notes
- Lessons are cached per level while the server runs, so most page views don't call the API. Chat messages are capped in length and history.
- Set a monthly spend limit in the Anthropic Console so a busy class can't surprise you.
- The API key only lives on the server; the browser never sees it.
- If students will use this under a school, check your school's policies on student-facing AI tools.
