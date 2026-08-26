with open("app/routers/coding_arena.py", "r") as f:
    text = f.read()

text = text.replace("if not prior_attack_attempt:\n                attack.attempted += 1\n            print(f'DEBUG: prob={request.problem_id}, prior={prior_attack_attempt}, attempted={attack.attempted}', flush=True)",
                    "if not prior_attack_attempt:\n                attack.attempted += 1")

with open("app/routers/coding_arena.py", "w") as f:
    f.write(text)
