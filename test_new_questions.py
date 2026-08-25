import asyncio
from app.services.problem_catalog import PROBLEMS, BY_ID, VALIDATORS
from app.services.code_execution import Judge0ExecutionProvider, outputs_match
from app.config import settings
from scratch.solutions import solutions

async def main():
    provider = Judge0ExecutionProvider(settings.JUDGE0_URL, settings.JUDGE0_API_KEY, settings.JUDGE0_API_HOST)
    
    new_ids = ["A06", "A07", "A08", "S06", "S07", "S08", "SE06", "SE07", "SE08", "SO06", "SO07", "SO08", "SO09"]
    print(f"Testing {len(new_ids)} new problems")
    
    # 1. Test correct solutions
    for pid in new_ids:
        print(f"Testing Correct {pid}...")
        p = BY_ID[pid]
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
    
    # 2. Test some intentionally wrong solutions
    wrong_targets = ["A08", "S08", "SE08", "SO09"]
    for pid in wrong_targets:
        p = BY_ID[pid]
        # break it
        code = solutions[pid].replace("return ", "return 'X' + ")
        res = await provider.execute("python", code, p.hidden_tests[0]["input"])
        match = False
        if pid in VALIDATORS:
            match = VALIDATORS[pid](res.stdout, p.hidden_tests[0])
        else:
            match = outputs_match(res.stdout, p.hidden_tests[0]["output"])
        status = res.status
        if status == "accepted" and not match:
            status = "wrong_answer"
        print(f"{pid} wrong test: {status}")

if __name__ == '__main__':
    asyncio.run(main())
