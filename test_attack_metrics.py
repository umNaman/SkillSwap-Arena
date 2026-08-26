import requests
import time
import json
import uuid

base_url = "http://127.0.0.1:9005"
s = requests.Session()

# 1. Login with Register instead of Guest to bypass CAPTCHA
email = f"test_{uuid.uuid4().hex[:8]}@example.com"
r = s.post(f"{base_url}/api/auth/register", json={
    "email": email, "password": "password123", "default_alias": "tester"
})
token = r.json().get("token")
if not token:
    print("Login failed", r.text)
    exit(1)
s.headers.update({"Authorization": f"Bearer {token}"})

def run_case1():
    print("--- CASE 1: 1 problem, 4 wrong, 1 accepted ---")
    r = s.post(f"{base_url}/api/coding/attack/start", json={"language": "python", "difficulty": "easy", "topic": "arrays"})
    session_id = r.json()["session_id"]
    problem_id = r.json()["problem"]["id"]
    
    # 4 wrong submissions
    for _ in range(4):
        s.post(f"{base_url}/api/coding/submit", json={
            "session_id": session_id, "problem_id": problem_id, "language": "python",
            "source_code": "print('wrong')", "mode": "attack", "solve_seconds": 10
        })
    
    # 1 correct submission
    correct_code = """import sys
def solve(data):
    lines = data.strip().split('\\n')
    n = int(lines[0])
    arr = lines[1].split()
    x, p = lines[2].split()
    arr.insert(int(p), x)
    return ' '.join(arr)
print(solve(sys.stdin.read()))"""
    r_sub = s.post(f"{base_url}/api/coding/submit", json={
        "session_id": session_id, "problem_id": problem_id, "language": "python",
        "source_code": correct_code, "mode": "attack", "solve_seconds": 10
    })
    # end session
    r_end = s.post(f"{base_url}/api/coding/attack/{session_id}/end")
    stats = r_end.json()
    print("Expected: Attempted=1, Solved=1, Submissions=5, Acc=100.0")
    print("Actual:  ", stats)

def run_case2():
    print("--- CASE 2: 2 unique problems, A accepted after 2 submits, B never accepted after 3 submits ---")
    r = s.post(f"{base_url}/api/coding/attack/start", json={"language": "python", "difficulty": "easy", "topic": "arrays"})
    session_id = r.json()["session_id"]
    probA = r.json()["problem"]["id"]
    
    # Prob A: 1 wrong, 1 right
    s.post(f"{base_url}/api/coding/submit", json={
        "session_id": session_id, "problem_id": probA, "language": "python",
        "source_code": "print('wrong')", "mode": "attack", "solve_seconds": 10
    })
    correct_code = """import sys
def solve(data):
    lines = data.strip().split('\\n')
    n = int(lines[0])
    arr = lines[1].split()
    x, p = lines[2].split()
    arr.insert(int(p), x)
    return ' '.join(arr)
print(solve(sys.stdin.read()))"""
    r_sub = s.post(f"{base_url}/api/coding/submit", json={
        "session_id": session_id, "problem_id": probA, "language": "python",
        "source_code": correct_code, "mode": "attack", "solve_seconds": 10
    })
    
    # Get Prob B
    probB = r_sub.json()["next_problem"]["id"]
    
    # Prob B: 3 wrong
    for _ in range(3):
        s.post(f"{base_url}/api/coding/submit", json={
            "session_id": session_id, "problem_id": probB, "language": "python",
            "source_code": "print('wrong')", "mode": "attack", "solve_seconds": 10
        })
        
    r_end = s.post(f"{base_url}/api/coding/attack/{session_id}/end")
    stats = r_end.json()
    print("Expected: Attempted=2, Solved=1, Submissions=5, Acc=50.0")
    print("Actual:  ", stats)
    return session_id

def run_case3():
    print("--- CASE 3: Run Code multiple times without Submit ---")
    r = s.post(f"{base_url}/api/coding/attack/start", json={"language": "python", "difficulty": "easy", "topic": "arrays"})
    session_id = r.json()["session_id"]
    probA = r.json()["problem"]["id"]
    
    for _ in range(3):
        s.post(f"{base_url}/api/coding/run", json={
            "problem_id": probA, "language": "python", "source_code": "print('run')"
        })
        
    r_end = s.post(f"{base_url}/api/coding/attack/{session_id}/end")
    stats = r_end.json()
    print("Expected: Attempted=0, Solved=0, Submissions=0")
    print("Actual:  ", stats)

def run_case4(session_id):
    print("--- CASE 4: Reopen History ---")
    r = s.get(f"{base_url}/api/coding/history")
    hist = r.json()
    sess = next(s for s in hist["attack_sessions"] if s["id"] == session_id)
    print("History for session from Case 2:")
    print("Expected: Attempted=2, Solved=1, Submissions=5")
    print("Actual:  ", sess)

run_case1()
sess2 = run_case2()
run_case3()
run_case4(sess2)

