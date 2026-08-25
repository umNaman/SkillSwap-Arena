from app.services.problem_catalog import PROBLEMS

topics = {}
difficulties = {}
for p in PROBLEMS:
    topics[p.topic] = topics.get(p.topic, 0) + 1
    difficulties[p.difficulty] = difficulties.get(p.difficulty, 0) + 1

print(f"Total: {len(PROBLEMS)}")
print("Topics:", topics)
print("Difficulties:", difficulties)
