"""Run with:  python -m pytest -q"""
import os

os.environ.pop("ANTHROPIC_API_KEY", None)  # tests never call the real API

import pytest

import app as appmod
import lessons as L


@pytest.fixture
def client():
    appmod.app.config["TESTING"] = True
    with appmod.app.test_client() as c:
        yield c


def test_every_generator_accepts_its_own_answer():
    for lesson in L.LESSONS:
        for gen in lesson["generators"]:
            for _ in range(300):
                p = gen()
                for a in p["accept"]:
                    assert L.is_correct(a, p), (gen.__name__, p, a)
                assert L.is_correct(p["answer"], p), (gen.__name__, p)


def test_answer_formats():
    n = {"kind": "number", "answer": "7", "accept": ["7"]}
    for ok in ["7", " 7 ", "x=7", "x = 7", "7.0", "14/2", "7 hours", "$7"]:
        assert L.is_correct(ok, n), ok
    for bad in ["", "8", "seven", "x"]:
        assert not L.is_correct(bad, n), bad

    e = {"kind": "text", "answer": "7x+2", "accept": ["7x+2", "2+7x"]}
    for ok in ["7x + 2", "2 + 7x", "7*x+2", "7X + 2"]:
        assert L.is_correct(ok, e), ok
    assert not L.is_correct("9x", e)

    i = {"kind": "text", "answer": "x ≥ 4", "accept": ["x>=4", "4<=x"]}
    for ok in ["x >= 4", "x ≥ 4", "4 ≤ x", "x=>4"]:
        assert L.is_correct(ok, i), ok
    assert not L.is_correct("x > 4", i)


def test_level_gating_and_unlock(client):
    d = client.get("/api/lessons").get_json()
    assert [l["status"] for l in d["lessons"]][:2] == ["unlocked", "locked"]

    # Locked lesson and its practice are refused by the server
    assert client.get("/api/lessons/2").status_code == 403
    assert client.post("/api/lessons/2/practice", json={}).status_code == 403

    # Fail level 1 (all wrong, two tries each) -> still locked
    client.post("/api/lessons/1/practice", json={})
    for i in range(5):
        client.post("/api/lessons/1/check", json={"index": i, "answer": "-999"})
        r = client.post("/api/lessons/1/check", json={"index": i, "answer": "-999"}).get_json()
    assert r["done"] and not r["passed"]
    assert client.get("/api/lessons/2").status_code == 403

    # Pass level 1 -> level 2 unlocks
    client.post("/api/lessons/1/practice", json={})
    with client.session_transaction() as s:
        answers = [p["answer"] for p in s["practice"]["problems"]]
    for i, a in enumerate(answers):
        r = client.post("/api/lessons/1/check", json={"index": i, "answer": a}).get_json()
    assert r["passed"] and r["next_lesson"]["id"] == 2
    assert client.get("/api/lessons/2").status_code == 200
    statuses = [l["status"] for l in client.get("/api/lessons").get_json()["lessons"]]
    assert statuses[:3] == ["completed", "unlocked", "locked"]


def test_answers_not_leaked(client):
    d = client.post("/api/lessons/1/practice", json={}).get_json()
    assert all(set(p) == {"q"} for p in d["problems"])


def test_two_tries_then_hint_and_reveal(client):
    client.post("/api/lessons/1/practice", json={})
    r1 = client.post("/api/lessons/1/check", json={"index": 0, "answer": "-999"}).get_json()
    assert not r1["final"] and "hint" in r1 and "answer" not in r1
    r2 = client.post("/api/lessons/1/check", json={"index": 0, "answer": "-999"}).get_json()
    assert r2["final"] and "answer" in r2
    r3 = client.post("/api/lessons/1/check", json={"index": 0, "answer": "1"})
    assert r3.status_code == 400


def test_chat_without_key_is_friendly(client):
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "hi"}]}).get_json()
    assert "API key" in r["reply"]


def test_home_page(client):
    assert b"Algebra Quest" in client.get("/").data
