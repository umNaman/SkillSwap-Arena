"""Curated Coding Arena catalog. Hidden tests never leave this server module."""
from dataclasses import dataclass, asdict
from hashlib import sha256


@dataclass(frozen=True)
class Problem:
    id: str
    title: str
    topic: str
    difficulty: str
    statement: str
    input_description: str
    output_description: str
    examples: list[dict[str, str]]
    constraints: list[str]
    starter_code: dict[str, str]
    visible_tests: list[dict[str, str]]
    hidden_tests: list[dict[str, str]]
    hints: list[str]
    seeded_attempts: int
    seeded_solves: int
    seeded_average_seconds: int
    seeded_fastest_seconds: int

    def public(self, language: str | None = None) -> dict:
        value = asdict(self)
        value.pop("hidden_tests", None)
        value.pop("hints", None)
        value["hint_count"] = len(self.hints)
        value.pop("seeded_average_seconds", None)
        value.pop("seeded_fastest_seconds", None)
        value.pop("seeded_attempts", None)
        value.pop("seeded_solves", None)
        if language:
            value["starter_code"] = self.starter_code[language]
            value["filename"] = {"python": "main.py", "cpp": "main.cpp", "java": "Main.java"}[language]
        return value


def _starter(py: str, cpp: str, java: str) -> dict[str, str]:
    return {"python": py.strip()+"\n", "cpp": cpp.strip()+"\n", "java": java.strip()+"\n"}


STD = _starter(
    """import sys

def solve(data: str) -> str:
    # Write your solution here
    return ""

print(solve(sys.stdin.read().strip()))""",
    """#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    // Write your solution here
    return 0;
}""",
    """import java.io.*;
import java.util.*;
public class Main {
    public static void main(String[] args) throws Exception {
        Scanner sc = new Scanner(System.in);
        // Write your solution here
    }
}""",
)


def _p(id, title, topic, difficulty, statement, inp, out, tests, hints,
       constraints=("1 ≤ n ≤ 100000",)):
    visible = [{"input": a, "output": b} for a, b in tests[:2]]
    hidden = [{"input": a, "output": b} for a, b in tests[2:]] or visible
    # Keep seeded stats as 0
    return Problem(id, title, topic, difficulty, statement, inp, out,
        [{"input": a, "output": b, "explanation": "The output follows from the required operation."} for a,b in tests[:2]],
        list(constraints), STD, visible, hidden, list(hints), 0, 0, 0, 0)

PROBLEMS = [
_p("A01", "Insert at Position", "arrays", "easy", 'Given an array of n integers, a value x, and a zero-based position p, insert x at position p and print the resulting array.', 'Line 1: n\nLine 2: n integers\nLine 3: x p', 'The updated array, space-separated.', [
        ('4\n1 2 4 5\n3 2', '1 2 3 4 5'),
        ('1\n10\n20 0', '20 10'),
        ('3\n1 2 3\n4 3', '1 2 3 4'),
        ('5\n0 0 0 0 0\n1 2', '0 0 1 0 0 0'),
        ('2\n-1 -2\n-3 1', '-1 -3 -2'),
        ('6\n1 2 3 4 5 6\n0 0', '0 1 2 3 4 5 6'),
        ('4\n9 9 9 9\n8 2', '9 9 8 9 9'),
    ], ('Move elements after the insertion position one index to the right.', 'Shift from the end toward position p before inserting x.')),
_p("A02", "Second Distinct Largest", "arrays", "medium", 'Given an integer array, print the second largest distinct value. If no second distinct value exists, print NONE.', 'Line 1: n\nLine 2: n integers', 'Second largest distinct value or NONE.', [
        ('5\n8 4 8 2 6', '6'),
        ('3\n5 5 5', 'NONE'),
        ('4\n-1 -2 -3 -4', '-2'),
        ('2\n10 10', 'NONE'),
        ('6\n1 1 2 2 3 3', '2'),
        ('4\n10 20 30 40', '30'),
        ('1\n100', 'NONE'),
        ('5\n-10 -10 -10 -10 -10', 'NONE'),
    ], ('The largest value and second largest value must be different.', 'You can track two distinct maximum values while traversing the array.')),
_p("A03", "Rotate Array Right", "arrays", "medium", 'Given an array of n integers and an integer k, rotate the array to the right by k positions.', 'Line 1: n\nLine 2: n integers\nLine 3: k', 'The rotated array, space-separated.', [
        ('5\n1 2 3 4 5\n2', '4 5 1 2 3'),
        ('1\n10\n100', '10'),
        ('3\n1 2 3\n3', '1 2 3'),
        ('4\n1 2 3 4\n5', '4 1 2 3'),
        ('5\n-1 -2 -3 -4 -5\n0', '-1 -2 -3 -4 -5'),
        ('6\n10 20 30 40 50 60\n4', '30 40 50 60 10 20'),
        ('2\n1 2\n1', '2 1'),
    ], ('k may be larger than n.', "Think about where each element's index moves after k rotations.")),
_p("A04", "Maximum Subarray Sum", "arrays", "hard", 'Given an integer array, find the maximum possible sum of a non-empty contiguous subarray.', 'Line 1: n\nLine 2: n integers', 'Maximum contiguous subarray sum.', [
        ('8\n-2 -3 4 -1 -2 1 5 -3', '7'),
        ('1\n-5', '-5'),
        ('5\n1 2 3 4 5', '15'),
        ('4\n-1 -2 -3 -4', '-1'),
        ('6\n2 -1 2 3 4 -5', '10'),
        ('7\n-2 1 -3 4 -1 2 1', '6'),
        ('3\n0 0 0', '0'),
    ], ('At each index decide whether to extend the current subarray or start a new one.', 'Keep both the best sum ending at the current position and the best sum seen overall.')),
_p("A05", "Product Except Self", "arrays", "hard", 'Given an array of n integers, output an array where the value at each index is the product of all elements except the element at that index.\n\nDo not use division.', 'Line 1: n\nLine 2: n integers', 'n space-separated integers.', [
        ('4\n1 2 3 4', '24 12 8 6'),
        ('5\n-1 1 0 -3 3', '0 0 9 0 0'),
        ('2\n0 0', '0 0'),
        ('3\n2 3 4', '12 8 6'),
        ('4\n-1 -1 -1 -1', '-1 -1 -1 -1'),
        ('5\n1 2 0 4 5', '0 0 40 0 0'),
        ('3\n-2 -2 -2', '4 4 4'),
    ], ('For every index you need the product of everything on its left and everything on its right.', 'Build prefix and suffix products.')),
_p("S01", "Palindrome Check", "strings", "easy", 'Given a string, determine whether it is a palindrome. Comparison should be case-insensitive.', 'One string.', 'YES if it is a palindrome, otherwise NO.', [
        ('Level', 'YES'),
        ('hello', 'NO'),
        ('A', 'YES'),
        ('RaceCar', 'YES'),
        ('ab', 'NO'),
        ('Aba', 'YES'),
        ('abcba', 'YES'),
    ], ('Compare characters from opposite ends.', 'Convert characters to a common case before comparing.')),
_p("S02", "First Non-Repeating Character", "strings", "medium", 'Given a string, print the first character that occurs exactly once. If no such character exists, print NONE.', 'One string.', 'First non-repeating character or NONE.', [
        ('swiss', 'w'),
        ('aabb', 'NONE'),
        ('z', 'z'),
        ('abcabc', 'NONE'),
        ('abacabad', 'c'),
        ('xxyyzzw', 'w'),
        ('lovelive', 'o'),
    ], ('Count how often every character occurs.', 'After counting frequencies, traverse the original string again.')),
_p("S03", "Reverse Words", "strings", "medium", 'Given a sentence containing words separated by spaces, reverse the order of the words while preserving the characters inside each word.', 'One line containing the sentence.', 'Words in reverse order separated by single spaces.', [
        ('coding makes practice better', 'better practice makes coding'),
        ('hello', 'hello'),
        ('one two three', 'three two one'),
        ('a b c', 'c b a'),
        ('the quick brown fox', 'fox brown quick the'),
        ('a', 'a'),
        ('word', 'word'),
    ], ('Split the sentence into words.', 'Reverse the word sequence, not the characters inside each word.')),
_p("S04", "Longest Unique Substring", "strings", "hard", 'Given a string, find the length of the longest contiguous substring containing no repeated characters.', 'One string.', 'Length of the longest substring without repeated characters.', [
        ('abcabcbb', '3'),
        ('bbbbb', '1'),
        ('pwwkew', '3'),
        ('a', '1'),
        ('abcdef', '6'),
        ('aab', '2'),
        ('dvdf', '3'),
    ], ('Maintain a window containing only unique characters.', 'When a duplicate appears, move the left boundary past its previous occurrence.')),
_p("S05", "Minimum Window Containing Pattern", "strings", "hard", 'Given strings s and p, find the shortest substring of s containing every character of p with at least the required frequency.\n\nIf no such substring exists, print NONE.', 'Line 1: s\nLine 2: p', 'The minimum valid substring or NONE.', [
        ('ADOBECODEBANC\nABC', 'BANC'),
        ('a\na', 'a'),
        ('a\naa', 'NONE'),
        ('aa\naa', 'aa'),
        ('bba\nab', 'ba'),
        ('abcde\nace', 'abcde'),
        ('xyz\nzy', 'yz'),
    ], ('Track the character frequencies required by p.', 'Expand the right side of a window until it is valid, then shrink the left side while validity remains.')),
_p("SE01", "Linear Search", "searching", "easy", 'Given an array and a target value, print the first zero-based index where the target occurs. Print -1 if the target is absent.', 'Line 1: n\nLine 2: n integers\nLine 3: target', 'Index of the first occurrence or -1.', [
        ('5\n10 20 30 40 50\n30', '2'),
        ('4\n1 2 3 4\n5', '-1'),
        ('1\n5\n5', '0'),
        ('6\n1 2 1 2 1 2\n2', '1'),
        ('3\n-1 -2 -3\n-3', '2'),
        ('5\n0 0 0 0 0\n0', '0'),
        ('4\n9 8 7 6\n9', '0'),
    ], ('Check elements from left to right.', 'Stop as soon as the target is found.')),
_p("SE02", "Binary Search", "searching", "medium", 'Given a sorted array of distinct integers and a target, find the target using binary search.', 'Line 1: n\nLine 2: n sorted integers\nLine 3: target', 'Zero-based target index or -1.', [
        ('6\n2 5 8 12 16 23\n12', '3'),
        ('4\n1 2 3 4\n5', '-1'),
        ('1\n10\n10', '0'),
        ('5\n-10 -5 0 5 10\n-5', '1'),
        ('7\n1 3 5 7 9 11 13\n13', '6'),
        ('2\n1 2\n1', '0'),
        ('6\n2 4 6 8 10 12\n3', '-1'),
    ], ('Compare the target with the middle element.', 'After each comparison, discard the half that cannot contain the target.')),
_p("SE03", "First and Last Position", "searching", "medium", 'Given a sorted array and a target, print the first and last index where the target occurs.\n\nIf the target does not exist, print:\n-1 -1', 'Line 1: n\nLine 2: n sorted integers\nLine 3: target', 'First index and last index.', [
        ('7\n1 2 2 2 3 4 5\n2', '1 3'),
        ('4\n1 2 3 4\n5', '-1 -1'),
        ('1\n5\n5', '0 0'),
        ('6\n1 1 1 1 1 1\n1', '0 5'),
        ('5\n1 2 3 3 3\n3', '2 4'),
        ('4\n2 2 4 4\n2', '0 1'),
        ('8\n1 2 3 4 5 6 7 8\n4', '3 3'),
    ], ('One binary search can locate the left boundary.', 'Perform another modified binary search for the right boundary.')),
_p("SE04", "Search Rotated Sorted Array", "searching", "hard", 'A sorted array of distinct integers has been rotated at an unknown position. Find the target index in O(log n) time.', 'Line 1: n\nLine 2: n integers\nLine 3: target', 'Target index or -1.', [
        ('7\n4 5 6 7 0 1 2\n0', '4'),
        ('6\n4 5 6 0 1 2\n3', '-1'),
        ('1\n8\n8', '0'),
        ('5\n3 4 5 1 2\n5', '2'),
        ('5\n3 4 5 1 2\n1', '3'),
        ('6\n5 1 2 3 4\n1', '1'),
        ('4\n2 3 4 1\n2', '0'),
    ], ('At least one half around the middle element is still sorted.', 'Determine which half is sorted and whether the target lies inside it.')),
_p("SE05", "Find Peak Element", "searching", "hard", 'Given an array where adjacent elements are different, find an index i whose value is greater than its adjacent elements.\n\nFor boundaries, treat the missing neighbour as negative infinity.\n\nIf multiple peaks exist, any valid peak index is acceptable.', 'Line 1: n\nLine 2: n integers', 'A valid peak index.', [
        ('6\n1 3 5 4 2 1', '2'),
        ('1\n5', '0'),
        ('2\n1 2', '1'),
        ('2\n2 1', '0'),
        ('4\n1 2 3 1', '2'),
        ('7\n1 2 1 3 5 6 4', '5'),
        ('5\n5 4 3 2 1', '0'),
    ], ('Compare the middle element with its neighbours.', 'If the right neighbour is larger, a peak must exist toward the right; otherwise search left.')),
_p("SO01", "Sort Three Values", "sorting", "easy", 'Given an array containing only 0, 1 and 2, sort it in ascending order.', 'Line 1: n\nLine 2: n integers containing only 0, 1 and 2', 'Sorted array, space-separated.', [
        ('6\n2 0 2 1 1 0', '0 0 1 1 2 2'),
        ('3\n1 0 2', '0 1 2'),
        ('4\n0 0 0 0', '0 0 0 0'),
        ('5\n2 2 2 2 2', '2 2 2 2 2'),
        ('7\n1 2 0 1 2 0 1', '0 0 1 1 1 2 2'),
        ('2\n2 0', '0 2'),
        ('4\n1 1 0 0', '0 0 1 1'),
    ], ('There are only three possible values.', 'You can count each value or maintain three regions.')),
_p("SO02", "Merge Two Sorted Arrays", "sorting", "medium", 'Given two sorted arrays, merge them into one sorted array.', 'Line 1: n\nLine 2: n sorted integers\nLine 3: m\nLine 4: m sorted integers', 'Merged sorted array.', [
        ('3\n1 4 7\n4\n2 3 6 8', '1 2 3 4 6 7 8'),
        ('2\n1 2\n2\n3 4', '1 2 3 4'),
        ('0\n\n3\n1 2 3', '1 2 3'),
        ('3\n1 2 3\n0\n', '1 2 3'),
        ('4\n1 1 1 1\n3\n1 1 1', '1 1 1 1 1 1 1'),
        ('2\n-5 5\n2\n-10 10', '-10 -5 5 10'),
        ('3\n1 3 5\n3\n2 4 6', '1 2 3 4 5 6'),
    ], ('Keep one pointer for each array.', 'Repeatedly choose the smaller current element.')),
_p("SO03", "Sort by Frequency", "sorting", "medium", 'Sort array elements by decreasing frequency.\n\nIf two values have the same frequency, the smaller numeric value must appear first.', 'Line 1: n\nLine 2: n integers', 'The reordered array.', [
        ('8\n4 4 1 2 2 2 3 3', '2 2 2 3 3 4 4 1'),
        ('5\n3 1 3 2 1', '1 1 3 3 2'),
        ('3\n5 5 5', '5 5 5'),
        ('4\n4 3 2 1', '1 2 3 4'),
        ('6\n1 1 2 2 3 3', '1 1 2 2 3 3'),
        ('7\n9 9 9 8 8 8 7', '8 8 8 9 9 9 7'),
        ('5\n-1 -1 2 2 3', '-1 -1 2 2 3'),
    ], ('Count the frequency of every distinct value.', 'Sort distinct values using frequency descending and value ascending.')),
_p("SO04", "Count Inversions", "sorting", "hard", 'Count pairs (i, j) such that:\n\ni < j\nand\narr[i] > arr[j]', 'Line 1: n\nLine 2: n integers', 'Number of inversions.', [
        ('5\n2 4 1 3 5', '3'),
        ('4\n1 2 3 4', '0'),
        ('4\n4 3 2 1', '6'),
        ('5\n1 1 1 1 1', '0'),
        ('6\n3 1 2 4 6 5', '3'),
        ('3\n10 20 5', '2'),
        ('7\n7 6 5 4 3 2 1', '21'),
    ], ('A direct comparison of every pair is possible but slow.', 'During merge sort, when a right-side value is placed before remaining left-side values, multiple inversions can be counted at once.')),
_p("SO05", "Minimum Swaps to Sort", "sorting", "hard", 'Given an array of distinct integers, find the minimum number of swaps required to sort the array in ascending order.', 'Line 1: n\nLine 2: n distinct integers', 'Minimum number of swaps.', [
        ('4\n4 3 2 1', '2'),
        ('5\n1 5 4 3 2', '2'),
        ('4\n1 2 3 4', '0'),
        ('6\n6 5 4 3 2 1', '3'),
        ('5\n2 4 5 1 3', '3'),
        ('3\n3 1 2', '2'),
        ('4\n2 1 4 3', '2'),
    ], ('After sorting a copy, determine where every original element belongs.', 'Treat the mapping of current positions to sorted positions as permutation cycles.')),

 _p("A06", "Pair Sum Check", "arrays", "easy",
    "Given an integer array and target, determine whether any two distinct elements sum to the target.",
    "Line 1: n\nLine 2: n integers\nLine 3: target", "YES or NO.",
    [
        ("5\n1 2 3 4 5\n9", "YES"),
        ("5\n1 2 3 4 5\n10", "NO"),
        ("2\n2 2\n4", "YES"),
        ("3\n1 5 9\n6", "YES"),
        ("4\n-1 -2 -3 -4\n-7", "YES"),
        ("4\n1 2 3 4\n8", "NO"),
        ("1\n5\n5", "NO")
    ], ("Use a hash set to track visited elements.", "Check if target - current exists in the set.")),

 _p("A07", "Maximum Subarray Sum of Fixed Size K", "arrays", "easy",
    "Given an integer array and k, find the maximum sum of any contiguous subarray containing exactly k elements.",
    "Line 1: n k\nLine 2: n integers", "Maximum sum.",
    [
        ("5 2\n1 2 3 4 5", "9"),
        ("4 1\n1 2 3 4", "4"),
        ("6 3\n1 -1 5 -2 3 4", "6"),
        ("3 3\n10 20 30", "60"),
        ("5 2\n-1 -2 -3 -4 -5", "-3"),
        ("4 2\n10 2 3 10", "13"),
        ("5 4\n10 10 10 10 10", "40")
    ], ("Calculate the sum of the first k elements.", "Slide the window by adding the next element and removing the first element of the window.")),

 _p("A08", "Trapping Rain Water", "arrays", "hard",
    "Given non-negative bar heights where each bar has width 1, calculate the total trapped rain water.",
    "Line 1: n\nLine 2: n integers", "Total trapped water.",
    [
        ("12\n0 1 0 2 1 0 1 3 2 1 2 1", "6"),
        ("6\n4 2 0 3 2 5", "9"),
        ("3\n1 0 1", "1"),
        ("5\n5 4 3 2 1", "0"),
        ("5\n1 2 3 4 5", "0"),
        ("7\n1 0 2 0 3 0 4", "6"),
        ("1\n5", "0")
    ], ("Water trapped at index i depends on the maximum heights to its left and right.", "Use two pointers from both ends to optimize space.")),

 _p("S06", "Valid Anagram", "strings", "easy",
    "Given strings s and t, determine whether they contain exactly the same characters with the same frequencies.",
    "Line 1: s\nLine 2: t", "YES or NO.",
    [
        ("listen\nsilent", "YES"),
        ("hello\nworld", "NO"),
        ("rat\ncar", "NO"),
        ("a\na", "YES"),
        ("ab\na", "NO"),
        ("aacc\nccac", "NO"),
        ("anagram\nnagaram", "YES")
    ], ("Count the frequency of each character in both strings.", "If the counts match perfectly, they are anagrams.")),

 _p("S07", "Longest Common Prefix", "strings", "easy",
    "Given an array of strings, output their longest common prefix. If none exists, output an empty string.",
    "Line 1: n\nNext n lines: one string per line", "Longest common prefix.",
    [
        ("3\nflower\nflow\nflight", "fl"),
        ("3\ndog\nracecar\ncar", ""),
        ("1\nhello", "hello"),
        ("2\nabc\nab", "ab"),
        ("2\nflower\nflower", "flower"),
        ("3\na\nb\nc", ""),
        ("2\nskill\nswap", "s")
    ], ("Compare the first and last strings after sorting them.", "Alternatively, check characters column by column.")),

 _p("S08", "Group Anagrams", "strings", "medium",
    "Given multiple strings, group strings that are anagrams of one another. Output each group on a new line, sorted lexicographically inside the group, and sort the groups by their first string.",
    "Line 1: n\nNext n lines: strings", "Groups of anagrams.",
    [
        ("6\neat\ntea\ntan\nate\nnat\nbat", "ate eat tea\nbat\nnat tan"),
        ("1\nhello", "hello"),
        ("3\na\nb\nc", "a\nb\nc"),
        ("4\nzz\nzz\nzz\nzz", "zz zz zz zz"),
        ("5\nabc\nbca\ncab\ndef\nfed", "abc bca cab\ndef fed"),
        ("4\nxy\nyx\nza\naz", "az za\nxy yx"),
        ("2\nxyz\nzyx", "xyz zyx")
    ], ("Use the sorted string as a key in a hash map.", "Format the output exactly as requested, handling sorting appropriately.")),

 _p("SE06", "First Bad Version", "searching", "easy",
    "Given n versions where every version from some first bad version onward is bad, identify the first bad version using binary-search logic.\n\nFor this platform, you will receive n and the first bad version b directly in the input.",
    "Line 1: n\nLine 2: b", "The first bad version.",
    [
        ("5\n4", "4"),
        ("1\n1", "1"),
        ("10\n1", "1"),
        ("10\n10", "10"),
        ("100\n50", "50"),
        ("1000\n999", "999"),
        ("2\n2", "2")
    ], ("Binary search over the range of versions.", "Since you are given b in the input, you could theoretically just print b, but practicing the search logic is encouraged.")),

 _p("SE07", "Find Minimum in Rotated Sorted Array", "searching", "medium",
    "Given a rotated sorted array containing distinct values, find its minimum element in O(log n).",
    "Line 1: n\nLine 2: n integers", "The minimum element.",
    [
        ("5\n3 4 5 1 2", "1"),
        ("7\n4 5 6 7 0 1 2", "0"),
        ("4\n11 13 15 17", "11"),
        ("1\n5", "5"),
        ("6\n2 3 4 5 6 1", "1"),
        ("5\n5 1 2 3 4", "1"),
        ("2\n2 1", "1")
    ], ("The array is sorted but rotated. Find the pivot point.", "If the middle element is greater than the rightmost element, the minimum is to the right.")),

 _p("SE08", "Median of Two Sorted Arrays", "searching", "hard",
    "Given two sorted arrays, return the median of their combined values.\n\nUse deterministic numeric formatting so Judge0 output validation is reliable. Output to exactly 1 decimal place.",
    "Line 1: n m\nLine 2: n integers\nLine 3: m integers", "Median value to 1 decimal place.",
    [
        ("2 1\n1 3\n2", "2.0"),
        ("2 2\n1 2\n3 4", "2.5"),
        ("0 1\n\n1", "1.0"),
        ("2 0\n1 2\n", "1.5"),
        ("3 3\n1 2 3\n4 5 6", "3.5"),
        ("1 1\n10\n20", "15.0"),
        ("4 2\n1 3 5 7\n2 4", "3.5")
    ], ("You can merge the arrays and find the median, but try to do it in logarithmic time.", "Binary search on the smaller array to partition both arrays such that left elements are smaller than right elements.")),

 _p("SO06", "Merge Intervals", "sorting", "easy",
    "Given intervals, merge all overlapping intervals and output the resulting non-overlapping intervals, one per line.",
    "Line 1: n\nNext n lines: start end", "Merged intervals.",
    [
        ("4\n1 3\n2 6\n8 10\n15 18", "1 6\n8 10\n15 18"),
        ("2\n1 4\n4 5", "1 5"),
        ("1\n1 2", "1 2"),
        ("3\n1 4\n0 2\n3 5", "0 5"),
        ("2\n1 1\n2 2", "1 1\n2 2"),
        ("4\n1 10\n2 3\n4 5\n6 7", "1 10"),
        ("3\n1 2\n3 4\n2 3", "1 4")
    ], ("Sort the intervals by their start times first.", "If the current interval's start is less than or equal to the previous interval's end, they overlap.")),

 _p("SO07", "Kth Largest Element", "sorting", "medium",
    "Given an unsorted integer array and k, find the kth largest element.",
    "Line 1: n k\nLine 2: n integers", "The kth largest element.",
    [
        ("6 2\n3 2 1 5 6 4", "5"),
        ("9 4\n3 2 3 1 2 4 5 5 6", "4"),
        ("1 1\n1", "1"),
        ("3 3\n1 2 3", "1"),
        ("4 1\n4 4 4 4", "4"),
        ("5 2\n-1 -2 -3 -4 -5", "-2"),
        ("6 5\n10 20 30 40 50 60", "20")
    ], ("You can sort the array and pick the element.", "For a faster solution, use a min-heap of size k or quickselect.")),

 _p("SO08", "Sort a Nearly Sorted Array", "sorting", "medium",
    "Given an array where every element is at most k positions away from its sorted position, output the fully sorted array.",
    "Line 1: n k\nLine 2: n integers", "The fully sorted array.",
    [
        ("6 3\n2 6 3 12 56 8", "2 3 6 8 12 56"),
        ("4 1\n2 1 4 3", "1 2 3 4"),
        ("1 0\n5", "5"),
        ("5 2\n3 2 1 5 4", "1 2 3 4 5"),
        ("6 2\n10 20 30 40 50 60", "10 20 30 40 50 60"),
        ("5 4\n5 4 3 2 1", "1 2 3 4 5"),
        ("4 2\n3 4 1 2", "1 2 3 4")
    ], ("You can just use standard sort, but there's a more efficient way.", "A min-heap of size k+1 can sort the array in O(n log k) time.")),

 _p("SO09", "Count Smaller Numbers After Self", "sorting", "hard",
    "For every array position, return the number of elements to its right that are smaller than it.",
    "Line 1: n\nLine 2: n integers", "Space-separated counts.",
    [
        ("4\n5 2 6 1", "2 1 1 0"),
        ("1\n-1", "0"),
        ("2\n-1 -1", "0 0"),
        ("5\n1 2 3 4 5", "0 0 0 0 0"),
        ("5\n5 4 3 2 1", "4 3 2 1 0"),
        ("4\n2 2 2 2", "0 0 0 0"),
        ("6\n3 1 4 1 5 9", "2 0 1 0 0 0")
    ], ("A brute force solution takes O(n^2) which might be too slow.", "Modify merge sort to count smaller elements jumping from the right half to the left half."))

]

BY_ID = {problem.id: problem for problem in PROBLEMS}

def select_problem(language: str, difficulty: str, topic: str, salt: str = "") -> Problem:
    matches = [p for p in PROBLEMS if p.topic == topic and p.difficulty == difficulty]
    if not matches:
        matches = [p for p in PROBLEMS if p.topic == topic]
    digest = sha256(f"{language}:{difficulty}:{topic}:{salt}".encode()).digest()
    return matches[int.from_bytes(digest[:4], "big") % len(matches)]

def validate_se05(actual: str, test: dict) -> bool:
    try:
        ans_idx = int(actual.strip())
        lines = test["input"].strip().split("\n")
        n = int(lines[0])
        arr = list(map(int, lines[1].split()))
        if ans_idx < 0 or ans_idx >= n:
            return False
        left = arr[ans_idx - 1] if ans_idx > 0 else float("-inf")
        right = arr[ans_idx + 1] if ans_idx < n - 1 else float("-inf")
        return arr[ans_idx] > left and arr[ans_idx] > right
    except Exception:
        return False

VALIDATORS = {
    "SE05": validate_se05
}
