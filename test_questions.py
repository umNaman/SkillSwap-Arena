import asyncio
from app.services.problem_catalog import PROBLEMS, BY_ID, VALIDATORS
from app.services.code_execution import Judge0ExecutionProvider, outputs_match
from app.config import settings
from scratch.solutions import solutions

async def main():
    provider = Judge0ExecutionProvider(settings.JUDGE0_URL, settings.JUDGE0_API_KEY, settings.JUDGE0_API_HOST)
    
    print(f"Total problems: {len(PROBLEMS)}")
    
    # 1. Test correct solutions
    for p in PROBLEMS:
        print(f"Testing Correct {p.id}...")
        code = solutions[p.id]
        passed = 0
        for test in p.hidden_tests:
            res = await provider.execute("python", code, test["input"])
            if res.status != "accepted":
                print(f"  FAILED on {p.id}: {res.status} stderr={res.stderr}")
                break
            
            match = False
            if p.id in VALIDATORS:
                match = VALIDATORS[p.id](res.stdout, test)
            else:
                match = outputs_match(res.stdout, test["output"])
            
            if not match:
                print(f"  WRONG ANSWER on {p.id}. Output: {repr(res.stdout)}, Expected: {repr(test['output'])}")
                break
            passed += 1
        if passed == len(p.hidden_tests):
            print(f"  {p.id}: ACCEPTED")
    
    # 2. Test intentionally wrong solutions
    wrong_targets = ["A01", "A04", "S01", "S04", "SE02", "SE04", "SO01", "SO04"]
    for pid in wrong_targets:
        print(f"Testing Wrong {pid}...")
        p = BY_ID[pid]
        code = solutions[pid].replace("return ", "return 'X' + ") # introduces wrong answer
        res = await provider.execute("python", code, p.hidden_tests[0]["input"])
        print(f"  {pid} wrong returned: {res.status}")

if __name__ == '__main__':
    asyncio.run(main())
