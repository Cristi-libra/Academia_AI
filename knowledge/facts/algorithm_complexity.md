# Algorithm Complexity (Big-O)

## What Big-O Means

Big-O notation describes how the running time or memory of an algorithm grows with the input size n. It ignores constant factors: O(2n) is written O(n). Typical classes from fastest to slowest growth: O(1), O(log n), O(n), O(n log n), O(n²), O(2ⁿ).

## Python Data Structure Operations

- **list**: index access O(1), append O(1) amortized, insert or delete at the front O(n), membership test `x in list` O(n), sort O(n log n)
- **dict**: lookup, insert, delete O(1) average, O(n) worst case (hash collisions)
- **set**: membership test, add, remove O(1) average — use a set instead of a list when you only need membership tests
- **deque** (collections): append and pop at BOTH ends O(1) — use it for queues instead of `list.pop(0)`, which is O(n)

## Searching

- **Linear search**: O(n), works on any iterable, no ordering required
- **Binary search**: O(log n), requires a SORTED sequence; in Python use the bisect module
- **Hash lookup** (dict/set): O(1) average — the fastest membership test when you can afford building the structure

## Sorting

- Python's built-in `sorted()` and `list.sort()` use Timsort: O(n log n) worst case, O(n) on already-sorted data, and it is stable (equal elements keep their relative order)
- Comparison-based sorting cannot do better than O(n log n) in the general case
- Bubble sort and insertion sort are O(n²) — fine for teaching, wrong for production

## Common Patterns and Their Cost

- Nested loop over the same data: O(n²) — a frequent hidden cost in student code; often replaceable by one pass with a dict or set
- Building a string with `+=` in a loop: O(n²) total — use `"".join()` for O(n)
- Checking `if x in some_list` inside a loop: O(n²) total — convert the list to a set first

## Space Complexity

The same notation applies to memory. A comprehension that builds a new list is O(n) space; a generator expression (`sum(x*x for x in nums)`) is O(1) space because it produces values one at a time.
