import requests
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath("scratch"))
from solutions import solutions

base_url = "http://127.0.0.1:9005"
s = requests.Session()

email = f"test_{uuid.uuid4().hex[:8]}@example.com"
r = s.post(f"{base_url}/api/auth/register", json={
    "email": email, "password": "password123", "default_alias": "tester"
})
token = r.json().get("token")
s.headers.update({"Authorization": f"Bearer {token}"})

def run_case1():
    r = s.post(f"{base_url}/api/coding/attack/start", json={"language": "python", "difficulty": "easy", "topic": "arrays"})
    session_id = r.json()["session_id"]
    problem_id = r.json()["problem"]["id"]
    
    for _ in range(4):
        s.post(f"{base_url}/api/coding/submit", json={
            "session_id": session_id, "problem_id": problem_id, "language": "python",
            "source_code": "print('wrong')", "mode": "attack", "solve_seconds": 10
        })
    
    s.post(f"{base_url}/api/coding/submit", json={
        "session_id": session_id, "problem_id": problem_id, "language": "python",
        "source_code": solutions[problem_id], "mode": "attack", "solve_seconds": 10
    })
    r_end = s.post(f"{base_url}/api/coding/attack/{session_id}/end")
    stats = r_end.json()
    assert stats["attempted"] == 1, stats["attempted"]
    assert stats["solved"] == 1, stats["solved"]
    assert stats["submission_attempts"] == 5, stats["submission_attempts"]
    assert stats["accuracy"] == 100.0, stats["accuracy"]
    print("CASE 1 PASS")

def run_case2():
    r = s.post(f"{base_url}/api/coding/attack/start", json={"language": "python", "difficulty": "easy", "topic": "arrays"})
    session_id = r.json()["session_id"]
    probA = r.json()["problem"]["id"]
    
    s.post(f"{base_url}/api/coding/submit", json={
        "session_id": session_id, "problem_id": probA, "language": "python",
        "source_code": "print('wrong')", "mode": "attack", "solve_seconds": 10
    })
    r_sub = s.post(f"{base_url}/api/coding/submit", json={
        "session_id": session_id, "problem_id": probA, "language": "python",
        "source_code": solutions[probA], "mode": "attack", "solve_seconds": 10
    })
    
    probB = r_sub.json()["next_problem"]["id"]
    for _ in range(3):
        s.post(f"{base_url}/api/coding/submit", json={
            "session_id": session_id, "problem_id": probB, "language": "python",
            "source_code": "print('wrong')", "mode": "attack", "solve_seconds": 10
        })
        
    r_end = s.post(f"{base_url}/api/coding/attack/{session_id}/end")
    stats = r_end.json()
    assert stats["attempted"] == 2, stats["attempted"]
    assert stats["solved"] == 1, stats["solved"]
    assert stats["submission_attempts"] == 5, stats["submission_attempts"]
    assert stats["accuracy"] == 50.0, stats["accuracy"]
    print("CASE 2 PASS")
    return session_id

def run_case3():
    r = s.post(f"{base_url}/api/coding/attack/start", json={"language": "python", "difficulty": "easy", "topic": "arrays"})
    session_id = r.json()["session_id"]
    probA = r.json()["problem"]["id"]
    
    for _ in range(3):
        s.post(f"{base_url}/api/coding/run", json={
            "problem_id": probA, "language": "python", "source_code": "print('run')"
        })
        
    r_end = s.post(f"{base_url}/api/coding/attack/{session_id}/end")
    stats = r_end.json()
    assert stats["attempted"] == 0, stats["attempted"]
    assert stats["solved"] == 0, stats["solved"]
    assert stats["submission_attempts"] == 0, stats["submission_attempts"]
    print("CASE 3 PASS")

def run_case4(session_id):
    r = s.get(f"{base_url}/api/coding/history")
    hist = r.json()
    sess = next(se for se in hist["attack_sessions"] if se["id"] == session_id)
    assert sess["attempted"] == 2, sess["attempted"]
    assert sess["solved"] == 1, sess["solved"]
    assert sess["submission_attempts"] == 5, sess["submission_attempts"]
    print("CASE 4 PASS")

run_case1()
sess2 = run_case2()
run_case3()
run_case4(sess2)
