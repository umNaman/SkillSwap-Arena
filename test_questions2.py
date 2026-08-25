import asyncio
from app.services.problem_catalog import PROBLEMS, BY_ID, VALIDATORS
from app.services.code_execution import Judge0ExecutionProvider, outputs_match
from app.config import settings
from scratch.solutions import solutions

async def main():
    provider = Judge0ExecutionProvider(settings.JUDGE0_URL, settings.JUDGE0_API_KEY, settings.JUDGE0_API_HOST)
    
    wrong_targets = ["A01", "A04", "S01", "S04", "SE02", "SE04", "SO01", "SO04"]
    for pid in wrong_targets:
        p = BY_ID[pid]
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
