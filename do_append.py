with open("app/services/problem_catalog.py", "r") as f:
    content = f.read()

new_problems = """
 _p("A06", "Pair Sum Check", "arrays", "easy",
    "Given an integer array and target, determine whether any two distinct elements sum to the target.",
    "Line 1: n\\nLine 2: n integers\\nLine 3: target", "YES or NO.",
    [
        ("5\\n1 2 3 4 5\\n9", "YES"),
        ("5\\n1 2 3 4 5\\n10", "NO"),
        ("2\\n2 2\\n4", "YES"),
        ("3\\n1 5 9\\n6", "YES"),
        ("4\\n-1 -2 -3 -4\\n-7", "YES"),
        ("4\\n1 2 3 4\\n8", "NO"),
        ("1\\n5\\n5", "NO")
    ], ("Use a hash set to track visited elements.", "Check if target - current exists in the set.")),

 _p("A07", "Maximum Subarray Sum of Fixed Size K", "arrays", "easy",
    "Given an integer array and k, find the maximum sum of any contiguous subarray containing exactly k elements.",
    "Line 1: n k\\nLine 2: n integers", "Maximum sum.",
    [
        ("5 2\\n1 2 3 4 5", "9"),
        ("4 1\\n1 2 3 4", "4"),
        ("6 3\\n1 -1 5 -2 3 4", "5"),
        ("3 3\\n10 20 30", "60"),
        ("5 2\\n-1 -2 -3 -4 -5", "-3"),
        ("4 2\\n10 2 3 10", "13"),
        ("5 4\\n10 10 10 10 10", "40")
    ], ("Calculate the sum of the first k elements.", "Slide the window by adding the next element and removing the first element of the window.")),

 _p("A08", "Trapping Rain Water", "arrays", "hard",
    "Given non-negative bar heights where each bar has width 1, calculate the total trapped rain water.",
    "Line 1: n\\nLine 2: n integers", "Total trapped water.",
    [
        ("12\\n0 1 0 2 1 0 1 3 2 1 2 1", "6"),
        ("6\\n4 2 0 3 2 5", "9"),
        ("3\\n1 0 1", "1"),
        ("5\\n5 4 3 2 1", "0"),
        ("5\\n1 2 3 4 5", "0"),
        ("7\\n1 0 2 0 3 0 4", "6"),
        ("1\\n5", "0")
    ], ("Water trapped at index i depends on the maximum heights to its left and right.", "Use two pointers from both ends to optimize space.")),

 _p("S06", "Valid Anagram", "strings", "easy",
    "Given strings s and t, determine whether they contain exactly the same characters with the same frequencies.",
    "Line 1: s\\nLine 2: t", "YES or NO.",
    [
        ("listen\\nsilent", "YES"),
        ("hello\\nworld", "NO"),
        ("rat\\ncar", "NO"),
        ("a\\na", "YES"),
        ("ab\\na", "NO"),
        ("aacc\\nccac", "NO"),
        ("anagram\\nnagaram", "YES")
    ], ("Count the frequency of each character in both strings.", "If the counts match perfectly, they are anagrams.")),

 _p("S07", "Longest Common Prefix", "strings", "easy",
    "Given an array of strings, output their longest common prefix. If none exists, output an empty string.",
    "Line 1: n\\nNext n lines: one string per line", "Longest common prefix.",
    [
        ("3\\nflower\\nflow\\nflight", "fl"),
        ("3\\ndog\\nracecar\\ncar", ""),
        ("1\\nhello", "hello"),
        ("2\\nabc\\nab", "ab"),
        ("2\\nflower\\nflower", "flower"),
        ("3\\na\\nb\\nc", ""),
        ("2\\nskill\\nswap", "s")
    ], ("Compare the first and last strings after sorting them.", "Alternatively, check characters column by column.")),

 _p("S08", "Group Anagrams", "strings", "medium",
    "Given multiple strings, group strings that are anagrams of one another. Output each group on a new line, sorted lexicographically inside the group, and sort the groups by their first string.",
    "Line 1: n\\nNext n lines: strings", "Groups of anagrams.",
    [
        ("6\\neat\\ntea\\ntan\\nate\\nnat\\nbat", "ate eat tea\\nbat\\nnat tan"),
        ("1\\nhello", "hello"),
        ("3\\na\\nb\\nc", "a\\nb\\nc"),
        ("4\\nzz\\nzz\\nzz\\nzz", "zz zz zz zz"),
        ("5\\nabc\\nbca\\ncab\\ndef\\nfed", "abc bca cab\\ndef fed"),
        ("4\\nxy\\nyx\\nza\\naz", "az za\\nxy yx"),
        ("2\\nxyz\\nzyx", "xyz zyx")
    ], ("Use the sorted string as a key in a hash map.", "Format the output exactly as requested, handling sorting appropriately.")),

 _p("SE06", "First Bad Version", "searching", "easy",
    "Given n versions where every version from some first bad version onward is bad, identify the first bad version using binary-search logic.\\n\\nFor this platform, you will receive n and the first bad version b directly in the input.",
    "Line 1: n\\nLine 2: b", "The first bad version.",
    [
        ("5\\n4", "4"),
        ("1\\n1", "1"),
        ("10\\n1", "1"),
        ("10\\n10", "10"),
        ("100\\n50", "50"),
        ("1000\\n999", "999"),
        ("2\\n2", "2")
    ], ("Binary search over the range of versions.", "Since you are given b in the input, you could theoretically just print b, but practicing the search logic is encouraged.")),

 _p("SE07", "Find Minimum in Rotated Sorted Array", "searching", "medium",
    "Given a rotated sorted array containing distinct values, find its minimum element in O(log n).",
    "Line 1: n\\nLine 2: n integers", "The minimum element.",
    [
        ("5\\n3 4 5 1 2", "1"),
        ("7\\n4 5 6 7 0 1 2", "0"),
        ("4\\n11 13 15 17", "11"),
        ("1\\n5", "5"),
        ("6\\n2 3 4 5 6 1", "1"),
        ("5\\n5 1 2 3 4", "1"),
        ("2\\n2 1", "1")
    ], ("The array is sorted but rotated. Find the pivot point.", "If the middle element is greater than the rightmost element, the minimum is to the right.")),

 _p("SE08", "Median of Two Sorted Arrays", "searching", "hard",
    "Given two sorted arrays, return the median of their combined values.\\n\\nUse deterministic numeric formatting so Judge0 output validation is reliable. Output to exactly 1 decimal place.",
    "Line 1: n m\\nLine 2: n integers\\nLine 3: m integers", "Median value to 1 decimal place.",
    [
        ("2 1\\n1 3\\n2", "2.0"),
        ("2 2\\n1 2\\n3 4", "2.5"),
        ("0 1\\n\\n1", "1.0"),
        ("2 0\\n1 2\\n", "1.5"),
        ("3 3\\n1 2 3\\n4 5 6", "3.5"),
        ("1 1\\n10\\n20", "15.0"),
        ("4 2\\n1 3 5 7\\n2 4", "3.5")
    ], ("You can merge the arrays and find the median, but try to do it in logarithmic time.", "Binary search on the smaller array to partition both arrays such that left elements are smaller than right elements.")),

 _p("SO06", "Merge Intervals", "sorting", "easy",
    "Given intervals, merge all overlapping intervals and output the resulting non-overlapping intervals, one per line.",
    "Line 1: n\\nNext n lines: start end", "Merged intervals.",
    [
        ("4\\n1 3\\n2 6\\n8 10\\n15 18", "1 6\\n8 10\\n15 18"),
        ("2\\n1 4\\n4 5", "1 5"),
        ("1\\n1 2", "1 2"),
        ("3\\n1 4\\n0 2\\n3 5", "0 5"),
        ("2\\n1 1\\n2 2", "1 1\\n2 2"),
        ("4\\n1 10\\n2 3\\n4 5\\n6 7", "1 10"),
        ("3\\n1 2\\n3 4\\n2 3", "1 4")
    ], ("Sort the intervals by their start times first.", "If the current interval's start is less than or equal to the previous interval's end, they overlap.")),

 _p("SO07", "Kth Largest Element", "sorting", "medium",
    "Given an unsorted integer array and k, find the kth largest element.",
    "Line 1: n k\\nLine 2: n integers", "The kth largest element.",
    [
        ("6 2\\n3 2 1 5 6 4", "5"),
        ("9 4\\n3 2 3 1 2 4 5 5 6", "4"),
        ("1 1\\n1", "1"),
        ("3 3\\n1 2 3", "1"),
        ("4 1\\n4 4 4 4", "4"),
        ("5 2\\n-1 -2 -3 -4 -5", "-2"),
        ("6 5\\n10 20 30 40 50 60", "20")
    ], ("You can sort the array and pick the element.", "For a faster solution, use a min-heap of size k or quickselect.")),

 _p("SO08", "Sort a Nearly Sorted Array", "sorting", "medium",
    "Given an array where every element is at most k positions away from its sorted position, output the fully sorted array.",
    "Line 1: n k\\nLine 2: n integers", "The fully sorted array.",
    [
        ("6 3\\n2 6 3 12 56 8", "2 3 6 8 12 56"),
        ("4 1\\n2 1 4 3", "1 2 3 4"),
        ("1 0\\n5", "5"),
        ("5 2\\n3 2 1 5 4", "1 2 3 4 5"),
        ("6 2\\n10 20 30 40 50 60", "10 20 30 40 50 60"),
        ("5 4\\n5 4 3 2 1", "1 2 3 4 5"),
        ("4 2\\n3 4 1 2", "1 2 3 4")
    ], ("You can just use standard sort, but there's a more efficient way.", "A min-heap of size k+1 can sort the array in O(n log k) time.")),

 _p("SO09", "Count Smaller Numbers After Self", "sorting", "hard",
    "For every array position, return the number of elements to its right that are smaller than it.",
    "Line 1: n\\nLine 2: n integers", "Space-separated counts.",
    [
        ("4\\n5 2 6 1", "2 1 1 0"),
        ("1\\n-1", "0"),
        ("2\\n-1 -1", "0 0"),
        ("5\\n1 2 3 4 5", "0 0 0 0 0"),
        ("5\\n5 4 3 2 1", "4 3 2 1 0"),
        ("4\\n2 2 2 2", "0 0 0 0"),
        ("6\\n3 1 4 1 5 9", "2 0 1 0 0 0")
    ], ("A brute force solution takes O(n^2) which might be too slow.", "Modify merge sort to count smaller elements jumping from the right half to the left half."))
"""

import re
# We just need to replace the `]\n\nBY_ID` with `,\n` + new_problems + `]\n\nBY_ID`
if "]\n\nBY_ID" in content:
    content = content.replace("]\n\nBY_ID", ",\n" + new_problems + "\n]\n\nBY_ID")
else:
    # try regex again
    content = re.sub(r'\]\s*BY_ID', ',\n' + new_problems + '\n]\n\nBY_ID', content)
    
with open("app/services/problem_catalog.py", "w") as f:
    f.write(content)
print("done")
