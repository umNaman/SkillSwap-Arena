with open("scratch/solutions.py", "r") as f:
    text = f.read()

# the literal newline was injected because I used `\n` in the script.
# Let's just fix it by replacing `.split('\n')` where it actually broke to a newline.
# Actually, the string in solutions.py literally has a newline inside the split!
