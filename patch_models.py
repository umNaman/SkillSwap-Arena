with open("app/models/coding_arena.py", "r") as f:
    text = f.read()
text = text.replace("attempted: Mapped[int] = mapped_column(Integer, default=0)",
                    "attempted: Mapped[int] = mapped_column(Integer, default=0)\n    submission_attempts: Mapped[int] = mapped_column(Integer, default=0)")
with open("app/models/coding_arena.py", "w") as f:
    f.write(text)
