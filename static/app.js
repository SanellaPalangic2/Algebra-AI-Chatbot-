/* Algebra Quest — front end */
const $ = (s, el = document) => el.querySelector(s);
const view = $("#view");
const chatLog = $("#chat-log");
const chatInput = $("#chat-input");
const chatPanel = $("#chat-panel");

const state = { lessons: [], lesson: null, practice: null, chat: [], busy: false };

const CHEERS = ["Nailed it! 🎉", "Awesome! ⭐", "You're on fire! 🔥", "Correct! 🙌", "Math wizard! 🧙", "Boom! 💥", "Super smart! 🧠"];
const cheer = () => CHEERS[Math.floor(Math.random() * CHEERS.length)];

/* ---------- helpers ---------- */
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function md(text) {
  if (window.marked && window.DOMPurify) return DOMPurify.sanitize(marked.parse(text || ""));
  return esc(text).replace(/\n/g, "<br>");
}
async function api(path, body) {
  const opts = body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  };
  const res = await fetch(path, opts);
  let data = {};
  try { data = await res.json(); } catch { /* ignore */ }
  if (!res.ok) throw new Error(data.error || "Oops! Something went wrong. Try again.");
  return data;
}
function toast(msg) {
  const t = document.createElement("div");
  t.className = "toast"; t.textContent = msg;
  document.body.appendChild(t);
  requestAnimationFrame(() => t.classList.add("show"));
  setTimeout(() => { t.classList.remove("show"); setTimeout(() => t.remove(), 350); }, 2800);
}
const loader = msg => `<div class="loader"><div class="bounce">🤖</div><p>${esc(msg)}</p></div>`;
const errorBox = msg => `<div class="error-box"><div class="big-emoji">🙈</div><h2>${esc(msg)}</h2>
  <div class="lesson-actions" style="justify-content:center"><button class="btn primary" onclick="showHome()">Back to the quest map</button></div></div>`;

function setXP() {
  const done = state.lessons.filter(l => l.status === "completed").length;
  $("#xp").textContent = `⭐ ${done}/${state.lessons.length || 7}`;
}

/* ---------- HOME / QUEST MAP ---------- */
async function showHome() {
  state.lesson = null; state.practice = null;
  setChatContext(null);
  view.innerHTML = loader("Loading your quest map…");
  try {
    const d = await api("/api/lessons");
    state.lessons = d.lessons;
    state.passScore = d.pass_score; state.perSet = d.problems_per_set;
  } catch (e) { view.innerHTML = errorBox(e.message); return; }

  setXP();
  const total = state.lessons.length;
  const done = state.lessons.filter(l => l.status === "completed").length;
  const nextUp = state.lessons.find(l => l.status === "unlocked");
  const pct = Math.round((done / total) * 100);

  view.innerHTML = `
    <section class="hero">
      <div>
        <h1>${done === total ? "You're an Algebra Champion! 👑" : "Welcome, Math Explorer! 🚀"}</h1>
        <p>${done === total
          ? "You beat every level! Replay any level to practice more."
          : `Beat each level's practice to unlock the next one. ${nextUp ? `Up next: <b>${esc(nextUp.title)}</b>.` : ""} Algebot is here whenever you get stuck!`}</p>
      </div>
      <div class="progress-box">
        <div class="progress-label"><span>Quest progress</span><span>${done}/${total}</span></div>
        <div class="meter"><div style="width:0%"></div></div>
      </div>
    </section>
    <h2 class="section-title">🗺️ Your Levels</h2>
    <section class="quest-map">${state.lessons.map(cardHTML).join("")}</section>`;

  requestAnimationFrame(() => { $(".meter > div").style.width = pct + "%"; });

  view.querySelectorAll(".lesson-card").forEach(el => el.addEventListener("click", () => {
    const l = state.lessons.find(x => x.id === +el.dataset.id);
    if (l.status === "locked") {
      el.classList.remove("shake"); void el.offsetWidth; el.classList.add("shake");
      toast(`Finish Level ${l.id - 1} first to unlock this one! 🔑`);
      return;
    }
    showLesson(l.id);
  }));
  window.scrollTo(0, 0);
}

function cardHTML(l) {
  const locked = l.status === "locked";
  const badge = l.status === "completed" ? "✅ Mastered" : locked ? "🔒 Locked" : "▶ Start";
  return `
    <button class="lesson-card ${l.status}" style="--c:${l.color}" data-id="${l.id}"
      aria-label="Level ${l.id}: ${esc(l.title)} (${locked ? "locked" : l.status})" ${locked ? 'aria-disabled="true"' : ""}>
      <div class="card-top"><span class="level">Level ${l.id}</span><span class="badge">${badge}</span></div>
      <div class="card-emoji">${locked ? "🔒" : l.emoji}</div>
      <h3>${esc(l.title)}</h3>
      <p>${esc(l.tagline)}</p>
      ${l.best != null ? `<div class="best">Best score: ${l.best}/${state.perSet || 5}</div>` : ""}
    </button>`;
}

/* ---------- LESSON ---------- */
async function showLesson(id, fresh = false) {
  view.innerHTML = loader(fresh ? "Algebot is thinking of a new way to explain… 💡" : "Algebot is writing your lesson… ✏️");
  window.scrollTo(0, 0);
  let d;
  try { d = await api(`/api/lessons/${id}${fresh ? "?fresh=1" : ""}`); }
  catch (e) { view.innerHTML = errorBox(e.message); return; }

  state.lesson = d.lesson; state.practice = null;
  setChatContext(`Level ${d.lesson.id}: ${d.lesson.title}`);

  view.innerHTML = `
    <button class="back" id="back">← Quest map</button>
    <header class="lesson-banner" style="--c:${d.lesson.color}">
      <span class="banner-emoji">${d.lesson.emoji}</span>
      <div>
        <div class="level">Level ${d.lesson.id}</div>
        <h1>${esc(d.lesson.title)}</h1>
        <p>${esc(d.lesson.tagline)}</p>
      </div>
    </header>
    <article class="lesson-body">${md(d.content)}</article>
    ${d.ai ? "" : `<p class="note">📘 Showing the built-in lesson${d.ai_available ? " (Algebot couldn't write a new one just now)" : ""}.</p>`}
    <div class="lesson-actions">
      ${d.ai_available ? `<button class="btn ghost" id="again">🔄 Explain it another way</button>` : ""}
      <button class="btn primary big" id="go">I'm ready to practice! 🚀</button>
    </div>`;

  $("#back").onclick = showHome;
  $("#go").onclick = () => startPractice(id);
  const again = $("#again");
  if (again) again.onclick = () => showLesson(id, true);
}

/* ---------- PRACTICE ---------- */
async function startPractice(id) {
  view.innerHTML = loader("Cooking up practice problems… 🍳");
  window.scrollTo(0, 0);
  let d;
  try { d = await api(`/api/lessons/${id}/practice`, {}); }
  catch (e) { view.innerHTML = errorBox(e.message); return; }

  const lesson = state.lesson;
  state.practice = { id, problems: d.problems };
  setChatContext(`Practice: ${lesson.title}`);

  view.innerHTML = `
    <button class="back" id="back">← Back to lesson</button>
    <header class="practice-head" style="--c:${lesson.color}">
      <h1>Practice Time! 💪</h1>
      <p>Get <b>${d.pass_needed} out of ${d.total}</b> right to unlock the next level. You get <b>2 tries</b> on each problem.</p>
      <div class="score-dots">${d.problems.map((_, i) => `<span class="dot" id="dot-${i}"></span>`).join("")}</div>
    </header>
    <p class="tip">✍️ <b>How to answer:</b> for equations just type the number (like <b>7</b>). For expressions type things like <b>3x + 5</b>. For inequalities type <b>x > 4</b> or use <b>>=</b> and <b><=</b>.</p>
    <div class="problems">${d.problems.map((p, i) => problemHTML(p, i, lesson.color)).join("")}</div>
    <div id="result"></div>`;

  $("#back").onclick = () => showLesson(id);
  view.querySelectorAll(".problem").forEach(form => form.addEventListener("submit", e => {
    e.preventDefault(); checkAnswer(form);
  }));
  const first = $(".problem input"); if (first) first.focus({ preventScroll: true });
}

function problemHTML(p, i, color) {
  return `
    <form class="problem" data-i="${i}" style="--c:${color}">
      <div class="p-num">${i + 1}</div>
      <div class="p-main">
        <div class="p-q">${esc(p.q)}</div>
        <div class="p-row">
          <input name="answer" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="Your answer" aria-label="Answer to problem ${i + 1}">
          <button class="btn primary" type="submit">Check ✓</button>
        </div>
        <div class="p-feedback" aria-live="polite"></div>
      </div>
    </form>`;
}

async function checkAnswer(form) {
  const i = +form.dataset.i;
  const input = form.answer;
  const btn = $("button[type=submit]", form);
  const val = input.value.trim();
  if (!val) { toast("Type an answer first! ✍️"); input.focus(); return; }

  btn.disabled = true;
  let r;
  try { r = await api(`/api/lessons/${state.practice.id}/check`, { index: i, answer: val }); }
  catch (e) { toast(e.message); btn.disabled = false; return; }

  const fb = $(".p-feedback", form);
  const dot = $(`#dot-${i}`);
  const lock = () => { input.disabled = true; btn.disabled = true; };

  if (r.correct) {
    form.classList.add("right");
    fb.innerHTML = `<span class="yay">${cheer()}</span>`;
    dot.classList.add("right"); dot.textContent = "✓";
    lock(); focusNext(i);
  } else if (!r.final) {
    form.classList.remove("wobble"); void form.offsetWidth; form.classList.add("wobble");
    fb.innerHTML = `<span class="oops">Not quite — try once more!</span><span class="hint">💡 ${esc(r.hint)}</span>`;
    btn.disabled = false; input.select();
  } else {
    form.classList.add("wrong");
    fb.innerHTML = `<span class="oops">The answer was <b>${esc(r.answer)}</b>. You'll get the next one!</span>
      <span class="hint">💡 ${esc(r.hint)}</span>
      <button type="button" class="link ask">Ask Algebot why 🤖</button>`;
    $(".ask", fb).onclick = () => askAbout(state.practice.problems[i].q, r.answer);
    dot.classList.add("wrong"); dot.textContent = "✗";
    lock(); focusNext(i);
  }

  if (r.done) showResult(r);
}

function focusNext(i) {
  const next = view.querySelectorAll(".problem input:not(:disabled)")[0];
  if (next) next.focus({ preventScroll: false });
}

function showResult(r) {
  const box = $("#result");
  const id = state.practice.id;
  if (r.passed) {
    confetti();
    box.innerHTML = `
      <div class="result pass">
        <div class="big-emoji">🏆</div>
        <h2>Level complete!</h2>
        <p>You got <b>${r.score} out of ${r.total}</b>!
        ${r.next_lesson
          ? `Level ${r.next_lesson.id}: <b>${esc(r.next_lesson.title)}</b> ${r.next_lesson.emoji} is now unlocked!`
          : "You beat every level in Algebra Quest. You're an algebra champion! 👑"}</p>
        <div class="lesson-actions">
          <button class="btn ghost" id="map">🗺️ Quest map</button>
          ${r.next_lesson ? `<button class="btn primary big" id="next">Next level →</button>` : ""}
        </div>
      </div>`;
    if (r.next_lesson) $("#next").onclick = () => showLesson(r.next_lesson.id);
  } else {
    box.innerHTML = `
      <div class="result fail">
        <div class="big-emoji">🌱</div>
        <h2>So close — keep growing!</h2>
        <p>You got <b>${r.score} out of ${r.total}</b>. You need <b>${r.pass_needed}</b> to unlock the next level.
        Every try makes your brain stronger! 💪</p>
        <div class="lesson-actions">
          <button class="btn ghost" id="review">📖 Review the lesson</button>
          <button class="btn primary big" id="retry">Try a new set 🔁</button>
        </div>
      </div>`;
    $("#retry").onclick = () => startPractice(id);
    $("#review").onclick = () => showLesson(id);
  }
  const map = $("#map"); if (map) map.onclick = showHome;
  api("/api/lessons").then(d => { state.lessons = d.lessons; setXP(); }).catch(() => {});
  box.scrollIntoView({ behavior: "smooth", block: "center" });
}

/* ---------- CHAT ---------- */
function setChatContext(text) {
  $("#chat-context").textContent = text ? `Helping with ${text}` : "Ask me anything about algebra!";
}
function addBubble(role, text, extra = "") {
  const b = document.createElement("div");
  b.className = `bubble ${role} ${extra}`;
  b.innerHTML = role === "assistant" ? md(text) : esc(text);
  chatLog.appendChild(b);
  chatLog.scrollTop = chatLog.scrollHeight;
  return b;
}
async function sendChat(text) {
  text = (text || "").trim();
  if (!text || state.busy) return;
  state.busy = true;
  chatInput.value = "";
  addBubble("user", text);
  state.chat.push({ role: "user", content: text });

  const typing = addBubble("assistant", "", "typing");
  typing.innerHTML = "<span></span><span></span><span></span>";
  try {
    const r = await api("/api/chat", { messages: state.chat.slice(-12), lesson_id: state.lesson ? state.lesson.id : null });
    typing.remove();
    addBubble("assistant", r.reply);
    state.chat.push({ role: "assistant", content: r.reply });
  } catch (e) {
    typing.remove();
    addBubble("assistant", e.message, "error");
    state.chat.pop();
  } finally {
    state.busy = false;
    chatInput.focus({ preventScroll: true });
  }
}
function askAbout(question, answer) {
  openChat();
  sendChat(`I got this one wrong: "${question}". The answer was ${answer}. Can you explain why, step by step?`);
}
function openChat() { chatPanel.classList.add("open"); }
function closeChat() { chatPanel.classList.remove("open"); }

$("#chat-form").addEventListener("submit", e => { e.preventDefault(); sendChat(chatInput.value); });
$("#chips").addEventListener("click", e => { if (e.target.tagName === "BUTTON") sendChat(e.target.textContent); });
$("#chat-toggle").onclick = openChat;
$("#chat-close").onclick = closeChat;

/* ---------- confetti ---------- */
function confetti() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const c = document.createElement("canvas");
  c.id = "confetti"; document.body.appendChild(c);
  const ctx = c.getContext("2d");
  const W = c.width = innerWidth, H = c.height = innerHeight;
  const colors = ["#FF4D8D", "#FF9F1C", "#FFD23F", "#1FC7B6", "#3A86FF", "#7B2FF7", "#2DC66B"];
  const bits = Array.from({ length: 160 }, () => ({
    x: W / 2 + (Math.random() - .5) * 200, y: H * .35,
    vx: (Math.random() - .5) * 16, vy: -Math.random() * 14 - 4,
    s: Math.random() * 8 + 5, r: Math.random() * 6, vr: (Math.random() - .5) * .3,
    c: colors[Math.floor(Math.random() * colors.length)],
  }));
  const start = performance.now();
  (function frame(t) {
    ctx.clearRect(0, 0, W, H);
    bits.forEach(b => {
      b.vy += .35; b.vx *= .99; b.x += b.vx; b.y += b.vy; b.r += b.vr;
      ctx.save(); ctx.translate(b.x, b.y); ctx.rotate(b.r);
      ctx.fillStyle = b.c; ctx.fillRect(-b.s / 2, -b.s / 4, b.s, b.s / 2); ctx.restore();
    });
    if (t - start < 3200) requestAnimationFrame(frame); else c.remove();
  })(start);
}

/* ---------- init ---------- */
$("#logo").onclick = showHome;
$("#reset").onclick = async () => {
  if (!confirm("Start over from Level 1? This erases your progress.")) return;
  await api("/api/reset", {});
  toast("Fresh start! 🌟");
  showHome();
};
addBubble("assistant", "Hi there! I'm **Algebot** 🤖. Stuck on something? Ask me anything about algebra — I'll help you figure it out step by step!");
showHome();
