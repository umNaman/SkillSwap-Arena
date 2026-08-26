import re

with open("app/routers/coding_arena.py", "r") as f:
    text = f.read()

# 1. Update /submit
# Find:
#            prior_attack_solve = await db.scalar(select(CodingSubmission.id).where(
#                CodingSubmission.user_id == current_user.id, CodingSubmission.session_id == request.session_id,
#                CodingSubmission.problem_id == request.problem_id, CodingSubmission.accepted == True,
#                CodingSubmission.id != submission.id).limit(1))
#            attack.attempted += 1; attack.total_seconds += solve_seconds
#            if accepted and not prior_attack_solve:

new_submit_logic = """            prior_attack_solve = await db.scalar(select(CodingSubmission.id).where(
                CodingSubmission.user_id == current_user.id, CodingSubmission.session_id == request.session_id,
                CodingSubmission.problem_id == request.problem_id, CodingSubmission.accepted == True,
                CodingSubmission.id != submission.id).limit(1))
            prior_attack_attempt = await db.scalar(select(CodingSubmission.id).where(
                CodingSubmission.user_id == current_user.id, CodingSubmission.session_id == request.session_id,
                CodingSubmission.problem_id == request.problem_id,
                CodingSubmission.id != submission.id).limit(1))
                
            attack.submission_attempts += 1
            if not prior_attack_attempt:
                attack.attempted += 1
                
            attack.total_seconds += solve_seconds
            if accepted and not prior_attack_solve:"""

old_submit_logic = """            prior_attack_solve = await db.scalar(select(CodingSubmission.id).where(
                CodingSubmission.user_id == current_user.id, CodingSubmission.session_id == request.session_id,
                CodingSubmission.problem_id == request.problem_id, CodingSubmission.accepted == True,
                CodingSubmission.id != submission.id).limit(1))
            attack.attempted += 1; attack.total_seconds += solve_seconds
            if accepted and not prior_attack_solve:"""

text = text.replace(old_submit_logic, new_submit_logic)


# 2. Update /attack/{session_id}/end
old_attack_end = """    return {"attempted": attack.attempted, "solved": attack.solved,
        "accuracy": round(attack.solved / attack.attempted * 100, 1) if attack.attempted else 0,
        "average_solve_seconds": round(attack.total_seconds / attack.attempted) if attack.attempted else None,"""

new_attack_end = """    return {"attempted": attack.attempted, "solved": attack.solved,
        "submission_attempts": attack.submission_attempts,
        "accuracy": round(attack.solved / attack.attempted * 100, 1) if attack.attempted else 0,
        "average_solve_seconds": round(attack.total_seconds / attack.attempted) if attack.attempted else None,"""

text = text.replace(old_attack_end, new_attack_end)


# 3. We also need to update `/history` because it returns attack sessions and we should include submission_attempts
old_history = """"attack_sessions": [{"id": str(a.id), "attempted": a.attempted, "solved": a.solved,"""
new_history = """"attack_sessions": [{"id": str(a.id), "attempted": a.attempted, "solved": a.solved, "submission_attempts": a.submission_attempts,"""

text = text.replace(old_history, new_history)

with open("app/routers/coding_arena.py", "w") as f:
    f.write(text)

