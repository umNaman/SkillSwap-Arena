import asyncio
from app.services.problem_catalog import PROBLEMS, BY_ID, STD
from app.services.code_execution import Judge0ExecutionProvider, outputs_match
from app.config import settings

async def main():
    if not settings.JUDGE0_URL:
        print("JUDGE0_URL not configured")
        return
    provider = Judge0ExecutionProvider(settings.JUDGE0_URL, settings.JUDGE0_API_KEY, settings.JUDGE0_API_HOST)
    
    print("TOTAL QUESTIONS:", len(PROBLEMS))
    topics = {}
    for p in PROBLEMS:
        topics[p.topic] = topics.get(p.topic, 0) + 1
    for k, v in topics.items():
        print(f"{k.capitalize()}: {v}")
    
    print("\nQUESTION INVENTORY:")
    for p in PROBLEMS:
        print(f"ID: {p.id}")
        print(f"Title: {p.title}")
        print(f"Topic: {p.topic}")
        print(f"Difficulty: {p.difficulty}")
        print(f"Languages: python, cpp, java")
        print(f"Public tests: {len(p.visible_tests)}")
        print(f"Hidden tests: {len(p.hidden_tests)}")
        print(f"Hints: {len(p.hints)}")
        print("---")
        
    print("\nVALIDATION RUN:")
    # We will test one problem from each topic
    to_test = [
        ("arrays", "array-insert", """import sys\ndef solve(data: str) -> str:\n    lines = data.strip().split('\\n')\n    n = int(lines[0])\n    arr = lines[1].split()\n    val, pos = lines[2].split()\n    arr.insert(int(pos), val)\n    return ' '.join(arr)\nprint(solve(sys.stdin.read().strip()))"""),
        ("strings", "string-reverse-words", """import sys\ndef solve(data: str) -> str:\n    return ' '.join(data.strip().split()[::-1])\nprint(solve(sys.stdin.read().strip()))"""),
        ("searching", "search-linear", """import sys\ndef solve(data: str) -> str:\n    lines = data.strip().split('\\n')\n    n = int(lines[0])\n    arr = lines[1].split()\n    target = lines[2]\n    try:\n        return str(arr.index(target))\n    except ValueError:\n        return '-1'\nprint(solve(sys.stdin.read().strip()))"""),
        ("sorting", "sort-numbers", """import sys\ndef solve(data: str) -> str:\n    lines = data.strip().split('\\n')\n    n = int(lines[0])\n    arr = list(map(int, lines[1].split()))\n    return ' '.join(map(str, sorted(arr)))\nprint(solve(sys.stdin.read().strip()))""")
    ]
    
    for topic, pid, code in to_test:
        print(f"Testing {pid} (Correct)")
        p = BY_ID[pid]
        all_passed = True
        for t in p.hidden_tests:
            res = await provider.execute("python", code, t["input"])
            if res.status != "accepted" or not outputs_match(res.stdout, t["output"]):
                all_passed = False
                print(f"Failed {pid}: {res.status} {res.stdout!r} vs {t['output']!r}")
        if all_passed:
            print(f"{pid}: ACCEPTED")
            
        print(f"Testing {pid} (Incorrect)")
        bad_code = code.replace("return ", "return 'X' + ")
        res = await provider.execute("python", bad_code, p.hidden_tests[0]["input"])
        if res.status != "accepted" or outputs_match(res.stdout, p.hidden_tests[0]["output"]):
            if res.status == "accepted":
                print(f"{pid} incorrect: WRONG ANSWER (as expected)")
            else:
                print(f"{pid} incorrect: {res.status} (as expected)")
        else:
            print(f"{pid} incorrect: INCORRECTLY ACCEPTED")

if __name__ == '__main__':
    asyncio.run(main())
