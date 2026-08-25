import asyncio
from app.services.problem_catalog import PROBLEMS, BY_ID
from app.services.code_execution import Judge0ExecutionProvider, outputs_match
from app.config import settings

async def main():
    provider = Judge0ExecutionProvider(settings.JUDGE0_URL, settings.JUDGE0_API_KEY, settings.JUDGE0_API_HOST)
    pid = "array-insert"
    code = """import sys
def solve(data: str) -> str:
    lines = data.strip().split('\n')
    n = int(lines[0])
    arr = lines[1].split()
    val, pos = lines[2].split()
    arr.insert(int(pos), val)
    return 'X' + ' '.join(arr)
print(solve(sys.stdin.read().strip()))"""
    t = BY_ID[pid].hidden_tests[0]
    res = await provider.execute("python", code, t["input"])
    print(f"Status: {res.status}")
    print(f"Stdout: {res.stdout!r}")
    print(f"Expected: {t['output']!r}")
    print(f"outputs_match: {outputs_match(res.stdout, t['output'])}")

if __name__ == '__main__':
    asyncio.run(main())
