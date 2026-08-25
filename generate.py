import json
import random

# We will define functions to generate test cases for each problem.

problems = []

def add_p(pid, title, topic, diff, stmt, inp, out, hints, tests, constraints=("1 ≤ n ≤ 100000",)):
    problems.append({
        "id": pid, "title": title, "topic": topic, "difficulty": diff,
        "statement": stmt, "inp": inp, "out": out, "hints": hints, "tests": tests, "constraints": constraints
    })

# --- ARRAYS ---
# A01: Insert at Position
def tests_a01():
    t = [
        ("4\n1 2 4 5\n3 2", "1 2 3 4 5"),
        ("1\n10\n20 0", "20 10"),
        ("3\n1 2 3\n4 3", "1 2 3 4"),
        ("5\n0 0 0 0 0\n1 2", "0 0 1 0 0 0"),
        ("2\n-1 -2\n-3 1", "-1 -3 -2"),
        ("6\n1 2 3 4 5 6\n0 0", "0 1 2 3 4 5 6"),
        ("4\n9 9 9 9\n8 2", "9 9 8 9 9")
    ]
    return t

add_p("A01", "Insert at Position", "arrays", "easy",
      "Given an array of n integers, a value x, and a zero-based position p, insert x at position p and print the resulting array.",
      "Line 1: n\nLine 2: n integers\nLine 3: x p",
      "The updated array, space-separated.",
      ("Move elements after the insertion position one index to the right.", "Shift from the end toward position p before inserting x."),
      tests_a01())

# A02: Second Distinct Largest
def tests_a02():
    return [
        ("5\n8 4 8 2 6", "6"),
        ("3\n5 5 5", "NONE"),
        ("4\n-1 -2 -3 -4", "-2"),
        ("2\n10 10", "NONE"),
        ("6\n1 1 2 2 3 3", "2"),
        ("4\n10 20 30 40", "30"),
        ("1\n100", "NONE"),
        ("5\n-10 -10 -10 -10 -10", "NONE")
    ]

add_p("A02", "Second Distinct Largest", "arrays", "medium",
      "Given an integer array, print the second largest distinct value. If no second distinct value exists, print NONE.",
      "Line 1: n\nLine 2: n integers", "Second largest distinct value or NONE.",
      ("The largest value and second largest value must be different.", "You can track two distinct maximum values while traversing the array."),
      tests_a02())

# A03: Rotate Array Right
def tests_a03():
    return [
        ("5\n1 2 3 4 5\n2", "4 5 1 2 3"),
        ("1\n10\n100", "10"),
        ("3\n1 2 3\n3", "1 2 3"),
        ("4\n1 2 3 4\n5", "4 1 2 3"),
        ("5\n-1 -2 -3 -4 -5\n0", "-1 -2 -3 -4 -5"),
        ("6\n10 20 30 40 50 60\n4", "30 40 50 60 10 20"),
        ("2\n1 2\n1", "2 1")
    ]
add_p("A03", "Rotate Array Right", "arrays", "medium",
      "Given an array of n integers and an integer k, rotate the array to the right by k positions.",
      "Line 1: n\nLine 2: n integers\nLine 3: k", "The rotated array, space-separated.",
      ("k may be larger than n.", "Think about where each element's index moves after k rotations."),
      tests_a03())

# A04: Maximum Subarray Sum
def tests_a04():
    return [
        ("8\n-2 -3 4 -1 -2 1 5 -3", "7"),
        ("1\n-5", "-5"),
        ("5\n1 2 3 4 5", "15"),
        ("4\n-1 -2 -3 -4", "-1"),
        ("6\n2 -1 2 3 4 -5", "10"),
        ("7\n-2 1 -3 4 -1 2 1", "6"),
        ("3\n0 0 0", "0")
    ]
add_p("A04", "Maximum Subarray Sum", "arrays", "hard",
      "Given an integer array, find the maximum possible sum of a non-empty contiguous subarray.",
      "Line 1: n\nLine 2: n integers", "Maximum contiguous subarray sum.",
      ("At each index decide whether to extend the current subarray or start a new one.", "Keep both the best sum ending at the current position and the best sum seen overall."),
      tests_a04())

# A05: Product Except Self
def tests_a05():
    return [
        ("4\n1 2 3 4", "24 12 8 6"),
        ("5\n-1 1 0 -3 3", "0 0 9 0 0"),
        ("2\n0 0", "0 0"),
        ("3\n2 3 4", "12 8 6"),
        ("4\n-1 -1 -1 -1", "-1 -1 -1 -1"),
        ("5\n1 2 0 4 5", "0 0 40 0 0"),
        ("3\n-2 -2 -2", "4 4 4")
    ]
add_p("A05", "Product Except Self", "arrays", "hard",
      "Given an array of n integers, output an array where the value at each index is the product of all elements except the element at that index.\n\nDo not use division.",
      "Line 1: n\nLine 2: n integers", "n space-separated integers.",
      ("For every index you need the product of everything on its left and everything on its right.", "Build prefix and suffix products."),
      tests_a05())

# --- STRINGS ---
# S01: Palindrome Check
def tests_s01():
    return [
        ("Level", "YES"),
        ("hello", "NO"),
        ("A", "YES"),
        ("RaceCar", "YES"),
        ("ab", "NO"),
        ("Aba", "YES"),
        ("abcba", "YES")
    ]
add_p("S01", "Palindrome Check", "strings", "easy",
      "Given a string, determine whether it is a palindrome. Comparison should be case-insensitive.",
      "One string.", "YES if it is a palindrome, otherwise NO.",
      ("Compare characters from opposite ends.", "Convert characters to a common case before comparing."),
      tests_s01())

# S02: First Non-Repeating Character
def tests_s02():
    return [
        ("swiss", "w"),
        ("aabb", "NONE"),
        ("z", "z"),
        ("abcabc", "NONE"),
        ("abacabad", "c"),
        ("xxyyzzw", "w"),
        ("lovelive", "o")
    ]
add_p("S02", "First Non-Repeating Character", "strings", "medium",
      "Given a string, print the first character that occurs exactly once. If no such character exists, print NONE.",
      "One string.", "First non-repeating character or NONE.",
      ("Count how often every character occurs.", "After counting frequencies, traverse the original string again."),
      tests_s02())

# S03: Reverse Words
def tests_s03():
    return [
        ("coding makes practice better", "better practice makes coding"),
        ("hello", "hello"),
        ("one two three", "three two one"),
        ("a b c", "c b a"),
        ("the quick brown fox", "fox brown quick the"),
        ("a", "a"),
        ("word", "word")
    ]
add_p("S03", "Reverse Words", "strings", "medium",
      "Given a sentence containing words separated by spaces, reverse the order of the words while preserving the characters inside each word.",
      "One line containing the sentence.", "Words in reverse order separated by single spaces.",
      ("Split the sentence into words.", "Reverse the word sequence, not the characters inside each word."),
      tests_s03())

# S04: Longest Unique Substring
def tests_s04():
    return [
        ("abcabcbb", "3"),
        ("bbbbb", "1"),
        ("pwwkew", "3"),
        ("a", "1"),
        ("abcdef", "6"),
        ("aab", "2"),
        ("dvdf", "3")
    ]
add_p("S04", "Longest Unique Substring", "strings", "hard",
      "Given a string, find the length of the longest contiguous substring containing no repeated characters.",
      "One string.", "Length of the longest substring without repeated characters.",
      ("Maintain a window containing only unique characters.", "When a duplicate appears, move the left boundary past its previous occurrence."),
      tests_s04())

# S05: Minimum Window Containing Pattern
def tests_s05():
    return [
        ("ADOBECODEBANC\nABC", "BANC"),
        ("a\na", "a"),
        ("a\naa", "NONE"),
        ("aa\naa", "aa"),
        ("bba\nab", "ba"),
        ("abcde\nace", "abcde"),
        ("xyz\nzy", "yz")
    ]
add_p("S05", "Minimum Window Containing Pattern", "strings", "hard",
      "Given strings s and p, find the shortest substring of s containing every character of p with at least the required frequency.\n\nIf no such substring exists, print NONE.",
      "Line 1: s\nLine 2: p", "The minimum valid substring or NONE.",
      ("Track the character frequencies required by p.", "Expand the right side of a window until it is valid, then shrink the left side while validity remains."),
      tests_s05())

# --- SEARCHING ---
# SE01: Linear Search
def tests_se01():
    return [
        ("5\n10 20 30 40 50\n30", "2"),
        ("4\n1 2 3 4\n5", "-1"),
        ("1\n5\n5", "0"),
        ("6\n1 2 1 2 1 2\n2", "1"),
        ("3\n-1 -2 -3\n-3", "2"),
        ("5\n0 0 0 0 0\n0", "0"),
        ("4\n9 8 7 6\n9", "0")
    ]
add_p("SE01", "Linear Search", "searching", "easy",
      "Given an array and a target value, print the first zero-based index where the target occurs. Print -1 if the target is absent.",
      "Line 1: n\nLine 2: n integers\nLine 3: target", "Index of the first occurrence or -1.",
      ("Check elements from left to right.", "Stop as soon as the target is found."),
      tests_se01())

# SE02: Binary Search
def tests_se02():
    return [
        ("6\n2 5 8 12 16 23\n12", "3"),
        ("4\n1 2 3 4\n5", "-1"),
        ("1\n10\n10", "0"),
        ("5\n-10 -5 0 5 10\n-5", "1"),
        ("7\n1 3 5 7 9 11 13\n13", "6"),
        ("2\n1 2\n1", "0"),
        ("6\n2 4 6 8 10 12\n3", "-1")
    ]
add_p("SE02", "Binary Search", "searching", "medium",
      "Given a sorted array of distinct integers and a target, find the target using binary search.",
      "Line 1: n\nLine 2: n sorted integers\nLine 3: target", "Zero-based target index or -1.",
      ("Compare the target with the middle element.", "After each comparison, discard the half that cannot contain the target."),
      tests_se02())

# SE03: First and Last Position
def tests_se03():
    return [
        ("7\n1 2 2 2 3 4 5\n2", "1 3"),
        ("4\n1 2 3 4\n5", "-1 -1"),
        ("1\n5\n5", "0 0"),
        ("6\n1 1 1 1 1 1\n1", "0 5"),
        ("5\n1 2 3 3 3\n3", "2 4"),
        ("4\n2 2 4 4\n2", "0 1"),
        ("8\n1 2 3 4 5 6 7 8\n4", "3 3")
    ]
add_p("SE03", "First and Last Position", "searching", "medium",
      "Given a sorted array and a target, print the first and last index where the target occurs.\n\nIf the target does not exist, print:\n-1 -1",
      "Line 1: n\nLine 2: n sorted integers\nLine 3: target", "First index and last index.",
      ("One binary search can locate the left boundary.", "Perform another modified binary search for the right boundary."),
      tests_se03())

# SE04: Search Rotated Sorted Array
def tests_se04():
    return [
        ("7\n4 5 6 7 0 1 2\n0", "4"),
        ("6\n4 5 6 0 1 2\n3", "-1"),
        ("1\n8\n8", "0"),
        ("5\n3 4 5 1 2\n5", "2"),
        ("5\n3 4 5 1 2\n1", "3"),
        ("6\n5 1 2 3 4\n1", "1"),
        ("4\n2 3 4 1\n2", "0")
    ]
add_p("SE04", "Search Rotated Sorted Array", "searching", "hard",
      "A sorted array of distinct integers has been rotated at an unknown position. Find the target index in O(log n) time.",
      "Line 1: n\nLine 2: n integers\nLine 3: target", "Target index or -1.",
      ("At least one half around the middle element is still sorted.", "Determine which half is sorted and whether the target lies inside it."),
      tests_se04())

# SE05: Find Peak Element
def tests_se05():
    # Only need to provide input, output will be validated by custom validator
    # but we supply a sample output just in case (e.g. for visible examples)
    return [
        ("6\n1 3 5 4 2 1", "2"),
        ("1\n5", "0"),
        ("2\n1 2", "1"),
        ("2\n2 1", "0"),
        ("4\n1 2 3 1", "2"),
        ("7\n1 2 1 3 5 6 4", "5"),
        ("5\n5 4 3 2 1", "0")
    ]
add_p("SE05", "Find Peak Element", "searching", "hard",
      "Given an array where adjacent elements are different, find an index i whose value is greater than its adjacent elements.\n\nFor boundaries, treat the missing neighbour as negative infinity.\n\nIf multiple peaks exist, any valid peak index is acceptable.",
      "Line 1: n\nLine 2: n integers", "A valid peak index.",
      ("Compare the middle element with its neighbours.", "If the right neighbour is larger, a peak must exist toward the right; otherwise search left."),
      tests_se05())

# --- SORTING ---
# SO01: Sort Three Values
def tests_so01():
    return [
        ("6\n2 0 2 1 1 0", "0 0 1 1 2 2"),
        ("3\n1 0 2", "0 1 2"),
        ("4\n0 0 0 0", "0 0 0 0"),
        ("5\n2 2 2 2 2", "2 2 2 2 2"),
        ("7\n1 2 0 1 2 0 1", "0 0 1 1 1 2 2"),
        ("2\n2 0", "0 2"),
        ("4\n1 1 0 0", "0 0 1 1")
    ]
add_p("SO01", "Sort Three Values", "sorting", "easy",
      "Given an array containing only 0, 1 and 2, sort it in ascending order.",
      "Line 1: n\nLine 2: n integers containing only 0, 1 and 2", "Sorted array, space-separated.",
      ("There are only three possible values.", "You can count each value or maintain three regions."),
      tests_so01())

# SO02: Merge Two Sorted Arrays
def tests_so02():
    return [
        ("3\n1 4 7\n4\n2 3 6 8", "1 2 3 4 6 7 8"),
        ("2\n1 2\n2\n3 4", "1 2 3 4"),
        ("0\n\n3\n1 2 3", "1 2 3"),
        ("3\n1 2 3\n0\n", "1 2 3"),
        ("4\n1 1 1 1\n3\n1 1 1", "1 1 1 1 1 1 1"),
        ("2\n-5 5\n2\n-10 10", "-10 -5 5 10"),
        ("3\n1 3 5\n3\n2 4 6", "1 2 3 4 5 6")
    ]
add_p("SO02", "Merge Two Sorted Arrays", "sorting", "medium",
      "Given two sorted arrays, merge them into one sorted array.",
      "Line 1: n\nLine 2: n sorted integers\nLine 3: m\nLine 4: m sorted integers", "Merged sorted array.",
      ("Keep one pointer for each array.", "Repeatedly choose the smaller current element."),
      tests_so02())

# SO03: Sort by Frequency
def tests_so03():
    return [
        ("8\n4 4 1 2 2 2 3 3", "2 2 2 3 3 4 4 1"),
        ("5\n3 1 3 2 1", "1 1 3 3 2"),
        ("3\n5 5 5", "5 5 5"),
        ("4\n4 3 2 1", "1 2 3 4"),
        ("6\n1 1 2 2 3 3", "1 1 2 2 3 3"),
        ("7\n9 9 9 8 8 8 7", "8 8 8 9 9 9 7"),
        ("5\n-1 -1 2 2 3", "-1 -1 2 2 3")
    ]
add_p("SO03", "Sort by Frequency", "sorting", "medium",
      "Sort array elements by decreasing frequency.\n\nIf two values have the same frequency, the smaller numeric value must appear first.",
      "Line 1: n\nLine 2: n integers", "The reordered array.",
      ("Count the frequency of every distinct value.", "Sort distinct values using frequency descending and value ascending."),
      tests_so03())

# SO04: Count Inversions
def tests_so04():
    return [
        ("5\n2 4 1 3 5", "3"),
        ("4\n1 2 3 4", "0"),
        ("4\n4 3 2 1", "6"),
        ("5\n1 1 1 1 1", "0"),
        ("6\n3 1 2 4 6 5", "3"),
        ("3\n10 20 5", "2"),
        ("7\n7 6 5 4 3 2 1", "21")
    ]
add_p("SO04", "Count Inversions", "sorting", "hard",
      "Count pairs (i, j) such that:\n\ni < j\nand\narr[i] > arr[j]",
      "Line 1: n\nLine 2: n integers", "Number of inversions.",
      ("A direct comparison of every pair is possible but slow.", "During merge sort, when a right-side value is placed before remaining left-side values, multiple inversions can be counted at once."),
      tests_so04())

# SO05: Minimum Swaps to Sort
def tests_so05():
    return [
        ("4\n4 3 2 1", "2"),
        ("5\n1 5 4 3 2", "2"),
        ("4\n1 2 3 4", "0"),
        ("6\n6 5 4 3 2 1", "3"),
        ("5\n2 4 5 1 3", "3"),
        ("3\n3 1 2", "2"),
        ("4\n2 1 4 3", "2")
    ]
add_p("SO05", "Minimum Swaps to Sort", "sorting", "hard",
      "Given an array of distinct integers, find the minimum number of swaps required to sort the array in ascending order.",
      "Line 1: n\nLine 2: n distinct integers", "Minimum number of swaps.",
      ("After sorting a copy, determine where every original element belongs.", "Treat the mapping of current positions to sorted positions as permutation cycles."),
      tests_so05())

output = []
for p in problems:
    diff_lower = {"Very Easy": "easy", "Medium": "medium", "Hard": "hard"}.get(p["difficulty"], p["difficulty"].lower())
    t_str = "[\n"
    for t in p["tests"]:
        t_str += f'        ({repr(t[0])}, {repr(t[1])}),\n'
    t_str += "    ]"
    h_str = f'({repr(p["hints"][0])}, {repr(p["hints"][1])})'
    
    code = f'_p("{p["id"]}", "{p["title"]}", "{p["topic"]}", "{diff_lower}", {repr(p["statement"])}, {repr(p["inp"])}, {repr(p["out"])}, {t_str}, {h_str})'
    output.append(code)

with open("problems.txt", "w") as f:
    f.write(",\n".join(output))
