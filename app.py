"""
Algebra Quest — an AI algebra tutor for middle schoolers.

Run locally:   python app.py
On Render:     gunicorn app:app
"""
import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

import lessons as L

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("algebra-quest")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or "dev-only-change-me"
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),  # Render sets RENDER=true (HTTPS)
    PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 180,           # progress kept ~6 months
)

# ------------------------------------------------------------------ AI setup
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = None
if API_KEY:
    from anthropic import Anthropic
    client = Anthropic(api_key=API_KEY)
else:
    log.warning("ANTHROPIC_API_KEY not set — using built-in lessons, tutor chat disabled.")

LESSON_SYSTEM = """You are Algebot, a cheerful algebra teacher for middle schoolers (ages 11-14).
You write short, fun, crystal-clear lessons. Use simple words, short sentences, friendly emoji,
and real-life examples kids care about (games, snacks, sports, pets, music).
Format in Markdown. Use '## ' headings (each starting with an emoji), short paragraphs,
numbered steps for worked examples, bold for final answers, and a blockquote starting with
'⚠️ **Watch out!**' for the most common mistake. Write math in plain text (3x + 4 = 19, x², ≤),
never LaTeX. Do NOT include practice problems or a quiz — the app adds those after the lesson."""

TUTOR_SYSTEM = """You are Algebot 🤖, a warm, patient algebra tutor inside a learning app for
middle schoolers (ages 11-14).

How to talk:
- Simple words, short sentences, upbeat and encouraging. Replies under 120 words unless the
  student asks for more detail.
- Explain step by step. Write math in plain text (2x + 3 = 11, x², ≥), never LaTeX.
- Praise effort, and treat mistakes as a normal part of learning.

Rules:
- Stay on math and learning. If asked about something else, kindly steer back to algebra.
- If the student asks for the answer to one of their current practice problems, do NOT give the
  final answer. Give a hint or walk through a similar example with different numbers, then let
  them try.
- Never ask for personal information (full name, address, school, phone, photos, etc.).
- Keep everything age-appropriate. If a student says something that suggests they are upset,
  unsafe, or being hurt, respond kindly and encourage them to talk to a parent, teacher, or
  another trusted adult right away."""

_lesson_cache = {}  # lesson_id -> markdown


def generate_lesson(lesson, fresh=False):
    """Return (markdown, came_from_ai)."""
    if not client:
        return lesson["fallback"], False
    if not fresh and lesson["id"] in _lesson_cache:
        return _lesson_cache[lesson["id"]], True
    angle = ("Explain it in a DIFFERENT way than a typical textbook, with a new real-life story and new examples."
             if fresh else "")
    prompt = (f"Write Level {lesson['id']} of Algebra Quest: \"{lesson['title']}\".\n"
              f"Cover: {lesson['topics']}.\n"
              "Structure: a 2-3 sentence story hook, the key idea, 2-3 worked examples with numbered "
              "steps, one '⚠️ Watch out!' common mistake, and a short '🎒 Recap'. "
              f"Keep it under 450 words. {angle}")
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=1500, system=LESSON_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        md = "".join(b.text for b in resp.content if b.type == "text").strip()
        if md:
            _lesson_cache[lesson["id"]] = md
            return md, True
    except Exception as e:  # network/API problems shouldn't break class
        log.error("Lesson generation failed: %s", e)
    return lesson["fallback"], False


# ------------------------------------------------------------ progress helpers
def get_progress():
    return session.get("progress") or {"completed": [], "best": {}}


def save_progress(p):
    session.permanent = True
    session["progress"] = p


def is_unlocked(lesson_id, p):
    return lesson_id == 1 or (lesson_id - 1) in p["completed"]


def lesson_or_404(lesson_id):
    lesson = L.LESSONS_BY_ID.get(lesson_id)
    if not lesson:
        return None, (jsonify(error="That lesson doesn't exist."), 404)
    if not is_unlocked(lesson_id, get_progress()):
        return None, (jsonify(error=f"Finish Level {lesson_id - 1} first to unlock this one! 🔒"), 403)
    return lesson, None


# ---------------------------------------------------------------------- routes
@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/lessons")
def list_lessons():
    p = get_progress()
    out = []
    for l in L.LESSONS:
        status = ("completed" if l["id"] in p["completed"]
                  else "unlocked" if is_unlocked(l["id"], p) else "locked")
        out.append({**L.public_meta(l), "status": status, "best": p["best"].get(str(l["id"]))})
    return jsonify(lessons=out, ai_available=bool(client),
                   pass_score=L.PASS_SCORE, problems_per_set=L.PROBLEMS_PER_SET)


@app.get("/api/lessons/<int:lesson_id>")
def get_lesson(lesson_id):
    lesson, err = lesson_or_404(lesson_id)
    if err:
        return err
    md, from_ai = generate_lesson(lesson, fresh=request.args.get("fresh") == "1")
    return jsonify(lesson=L.public_meta(lesson), content=md, ai=from_ai, ai_available=bool(client))


@app.post("/api/lessons/<int:lesson_id>/practice")
def start_practice(lesson_id):
    lesson, err = lesson_or_404(lesson_id)
    if err:
        return err
    problems = L.make_practice(lesson_id)
    session["practice"] = {"lesson_id": lesson_id, "problems": problems, "tries": {}, "results": {}}
    return jsonify(problems=[{"q": p["q"]} for p in problems],
                   total=len(problems), pass_needed=L.PASS_SCORE)


@app.post("/api/lessons/<int:lesson_id>/check")
def check_answer(lesson_id):
    pr = session.get("practice")
    if not pr or pr["lesson_id"] != lesson_id:
        return jsonify(error="Start the practice first!"), 400
    data = request.get_json(silent=True) or {}
    try:
        idx = int(data.get("index"))
        prob = pr["problems"][idx]
    except (TypeError, ValueError, IndexError):
        return jsonify(error="Unknown problem."), 400
    answer = str(data.get("answer", ""))[:60]
    if not answer.strip():
        return jsonify(error="Type an answer first! ✍️"), 400

    key = str(idx)
    if key in pr["results"]:
        return jsonify(error="You already finished this one!"), 400

    correct = L.is_correct(answer, prob)
    tries = pr["tries"].get(key, 0) + 1
    pr["tries"][key] = tries
    final = correct or tries >= 2          # 2 tries per problem
    if final:
        pr["results"][key] = correct

    total = len(pr["problems"])
    answered = len(pr["results"])
    score = sum(1 for v in pr["results"].values() if v)
    done = answered == total
    passed = done and score >= L.PASS_SCORE

    next_lesson = None
    if done:
        p = get_progress()
        best = p["best"].get(str(lesson_id), 0)
        p["best"][str(lesson_id)] = max(best, score)
        if passed and lesson_id not in p["completed"]:
            p["completed"].append(lesson_id)
        save_progress(p)
        nxt = L.LESSONS_BY_ID.get(lesson_id + 1)
        if passed and nxt:
            next_lesson = L.public_meta(nxt)
    session["practice"] = pr

    resp = {"correct": correct, "final": final, "score": score, "answered": answered,
            "total": total, "done": done, "passed": passed, "pass_needed": L.PASS_SCORE,
            "next_lesson": next_lesson}
    if not correct:
        resp["hint"] = prob["hint"]
    if final and not correct:
        resp["answer"] = prob["answer"]
    return jsonify(resp)


@app.post("/api/chat")
def chat():
    if not client:
        return jsonify(reply="Algebot is taking a nap 😴 — your teacher needs to add an API key "
                             "to wake me up. You can still do all the lessons and practice!")
    data = request.get_json(silent=True) or {}

    # Clean up history: only user/assistant text, capped length, alternating roles.
    msgs = []
    for m in (data.get("messages") or [])[-12:]:
        role, content = m.get("role"), str(m.get("content", ""))[:600].strip()
        if role not in ("user", "assistant") or not content:
            continue
        if msgs and msgs[-1]["role"] == role:
            msgs[-1]["content"] += "\n" + content
        else:
            msgs.append({"role": role, "content": content})
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    if not msgs or msgs[-1]["role"] != "user":
        return jsonify(error="Say something to Algebot first!"), 400

    system = TUTOR_SYSTEM
    lesson_id = data.get("lesson_id")
    if isinstance(lesson_id, int) and lesson_id in L.LESSONS_BY_ID and is_unlocked(lesson_id, get_progress()):
        lesson = L.LESSONS_BY_ID[lesson_id]
        system += f"\n\nThe student is on Level {lesson_id}: {lesson['title']} ({lesson['topics']})."
        pr = session.get("practice")
        if pr and pr["lesson_id"] == lesson_id:
            qs = "\n".join(f"- {p['q']}" for p in pr["problems"])
            system += ("\nThey are working on these practice problems right now. Give hints, "
                       f"never the final answers:\n{qs}")

    try:
        resp = client.messages.create(model=MODEL, max_tokens=600, system=system, messages=msgs)
        reply = "".join(b.text for b in resp.content if b.type == "text").strip()
    except Exception as e:
        log.error("Chat failed: %s", e)
        return jsonify(error="Algebot's brain glitched 🤖💫 Try again in a moment!"), 502
    return jsonify(reply=reply or "Hmm, can you ask that another way? 🤔")


@app.post("/api/reset")
def reset():
    session.pop("progress", None)
    session.pop("practice", None)
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
