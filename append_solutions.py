new_sols = {
"A06": """import sys
def solve(data):
    lines = data.strip().split('\\n')
    n = int(lines[0])
    arr = list(map(int, lines[1].split()))
    t = int(lines[2])
    seen = set()
    for x in arr:
        if t - x in seen:
            return "YES"
        seen.add(x)
    return "NO"
print(solve(sys.stdin.read()))""",
"A07": """import sys
def solve(data):
    lines = data.strip().split('\\n')
    n, k = map(int, lines[0].split())
    arr = list(map(int, lines[1].split()))
    cur = sum(arr[:k])
    best = cur
    for i in range(k, len(arr)):
        cur += arr[i] - arr[i-k]
        best = max(best, cur)
    return str(best)
print(solve(sys.stdin.read()))""",
"A08": """import sys
def solve(data):
    lines = data.strip().split('\\n')
    arr = list(map(int, lines[1].split()))
    if not arr: return "0"
    l, r = 0, len(arr) - 1
    l_max, r_max = arr[l], arr[r]
    ans = 0
    while l < r:
        if l_max < r_max:
            l += 1
            l_max = max(l_max, arr[l])
            ans += l_max - arr[l]
        else:
            r -= 1
            r_max = max(r_max, arr[r])
            ans += r_max - arr[r]
    return str(ans)
print(solve(sys.stdin.read()))""",
"S06": """import sys
from collections import Counter
def solve(data):
    lines = data.strip().split('\\n')
    s = lines[0] if len(lines) > 0 else ""
    t = lines[1] if len(lines) > 1 else ""
    return "YES" if Counter(s) == Counter(t) else "NO"
print(solve(sys.stdin.read()))""",
"S07": """import sys
def solve(data):
    lines = data.strip().split('\\n')
    if len(lines) < 2: return ""
    strs = lines[1:]
    if not strs: return ""
    s1 = min(strs)
    s2 = max(strs)
    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s1
print(solve(sys.stdin.read()))""",
"S08": """import sys
from collections import defaultdict
def solve(data):
    lines = data.strip().split('\\n')
    if len(lines) < 2: return ""
    strs = lines[1:]
    d = defaultdict(list)
    for s in strs:
        d["".join(sorted(s))].append(s)
    res = []
    for k in d:
        d[k].sort()
        res.append(d[k])
    res.sort(key=lambda x: x[0])
    return "\\n".join(" ".join(g) for g in res)
print(solve(sys.stdin.read()))""",
"SE06": """import sys
def solve(data):
    lines = data.strip().split('\\n')
    n = int(lines[0])
    b = int(lines[1])
    def isBadVersion(v): return v >= b
    l, r = 1, n
    ans = -1
    while l <= r:
        m = (l+r)//2
        if isBadVersion(m):
            ans = m
            r = m - 1
        else:
            l = m + 1
    return str(ans)
print(solve(sys.stdin.read()))""",
"SE07": """import sys
def solve(data):
    lines = data.strip().split('\\n')
    arr = list(map(int, lines[1].split()))
    l, r = 0, len(arr)-1
    while l < r:
        m = (l+r)//2
        if arr[m] > arr[r]: l = m + 1
        else: r = m
    return str(arr[l])
print(solve(sys.stdin.read()))""",
"SE08": """import sys
def solve(data):
    lines = data.strip().split('\\n')
    n, m = map(int, lines[0].split())
    arr1 = list(map(int, lines[1].split())) if n > 0 else []
    arr2 = list(map(int, lines[2].split())) if m > 0 else []
    arr = sorted(arr1 + arr2)
    tot = len(arr)
    if tot % 2 == 1:
        ans = float(arr[tot//2])
    else:
        ans = (arr[tot//2 - 1] + arr[tot//2]) / 2.0
    return f"{ans:.1f}"
print(solve(sys.stdin.read()))""",
"SO06": """import sys
def solve(data):
    lines = data.strip().split('\\n')
    n = int(lines[0])
    intervals = []
    for i in range(1, n+1):
        intervals.append(list(map(int, lines[i].split())))
    if not intervals: return ""
    intervals.sort(key=lambda x: x[0])
    ans = [intervals[0]]
    for i in range(1, len(intervals)):
        if intervals[i][0] <= ans[-1][1]:
            ans[-1][1] = max(ans[-1][1], intervals[i][1])
        else:
            ans.append(intervals[i])
    return "\\n".join(f"{x[0]} {x[1]}" for x in ans)
print(solve(sys.stdin.read()))""",
"SO07": """import sys
def solve(data):
    lines = data.strip().split('\\n')
    n, k = map(int, lines[0].split())
    arr = list(map(int, lines[1].split()))
    arr.sort(reverse=True)
    return str(arr[k-1])
print(solve(sys.stdin.read()))""",
"SO08": """import sys
def solve(data):
    lines = data.strip().split('\\n')
    arr = list(map(int, lines[1].split()))
    arr.sort()
    return " ".join(map(str, arr))
print(solve(sys.stdin.read()))""",
"SO09": """import sys
def solve(data):
    lines = data.strip().split('\\n')
    arr = list(map(int, lines[1].split()))
    import bisect
    sorted_list = []
    ans = []
    for x in reversed(arr):
        idx = bisect.bisect_left(sorted_list, x)
        ans.append(idx)
        sorted_list.insert(idx, x)
    ans.reverse()
    return " ".join(map(str, ans))
print(solve(sys.stdin.read()))"""
}

with open("scratch/solutions.py", "a") as f:
    for k, v in new_sols.items():
        f.write(f'solutions["{k}"] = """{v}"""\n')
print("done")
