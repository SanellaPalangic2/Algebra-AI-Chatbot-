# 🤖 Algebra Quest

A kid-friendly AI algebra tutor for middle schoolers (ages 11–14), built with **Python + Flask** and the **Claude API**.

- **7 levels** on a colorful quest map: Variables → Order of Operations → Like Terms → One-Step Equations → Two-Step Equations → Distributive Property → Inequalities
- **AI-written lessons** in age-friendly language, with an *"Explain it another way"* button
- **Practice problems** at the end of every lesson — fresh random numbers each time, 2 tries per problem, hints on mistakes
- **Levels unlock in order**: score 4 out of 5 to unlock the next one. Answers are checked on the server, so kids can't skip ahead by peeking at the page.
- **Algebot chat** on every screen — asks guiding questions instead of just giving practice answers, stays on-topic, and never asks for personal info
- Works even without an API key (uses built-in lessons; chat is turned off)

---

## 1. Get an API key
1. Go to <https://console.anthropic.com>, sign in, and add a little billing credit.
2. **API Keys → Create Key**. Copy it (starts with `sk-ant-`). Treat it like a password.

## 2. Run it on your computer
```bash
cd algebra-quest
python -m venv .venv
# Mac/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
```
Open `.env` and paste your key after `ANTHROPIC_API_KEY=`, then:
```bash
python app.py
```
Visit <http://localhost:5000> 🎉

Run the tests any time with `pip install pytest` then `python -m pytest -q`.

## 3. Put it on GitHub
Create an **empty** repository on <https://github.com/new> (no README), then:
```bash
git init
git add .
git commit -m "Algebra Quest"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/algebra-quest.git
git push -u origin main
```
✅ `.gitignore` keeps your `.env` (and your API key) **out** of GitHub. Double-check that `.env` is not listed on the GitHub page.

## 4. Deploy on Render
**Easiest (Blueprint):**
1. On <https://render.com>, click **New + → Blueprint** and connect your GitHub repo.
2. Render reads `render.yaml` and asks for `ANTHROPIC_API_KEY` — paste your key.
3. Click **Apply**. In a few minutes you'll get a URL like `https://algebra-quest.onrender.com`.

**Or manually:** New + → Web Service → pick the repo, then set
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --workers 2 --threads 4 --timeout 120`
- Environment variables: `ANTHROPIC_API_KEY` (your key), `SECRET_KEY` (any long random string), `PYTHON_VERSION` = `3.12.7`

Every `git push` to `main` redeploys automatically.

> Free Render services go to sleep after ~15 minutes of no visits, so the first load afterward can take up to a minute.

---

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
