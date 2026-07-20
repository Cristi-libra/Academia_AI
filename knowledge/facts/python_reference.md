# Python Reference

## Core Data Structures

- **list** — ordered, mutable sequence. Use for ordered collections that change. Append is O(1) amortized, membership test `x in list` is O(n).
- **tuple** — ordered, immutable sequence. Use for fixed records and as dictionary keys. Cheaper than a list.
- **set** — unordered collection of unique elements. Membership test is O(1) on average. Use to deduplicate and to test membership fast.
- **dict** — key-value mapping, insertion-ordered since Python 3.7. Lookup, insert and delete are O(1) on average.

## Mutability

Mutable objects (list, dict, set) can be changed in place; immutable objects (int, float, str, tuple, frozenset) cannot. A common beginner mistake is using a mutable default argument: `def f(items=[])` shares the same list between calls. Use `def f(items=None)` and create the list inside the function.

## Comprehensions

List, set and dict comprehensions replace simple accumulation loops:

- `[x * 2 for x in numbers if x > 0]` builds a list
- `{word: len(word) for word in words}` builds a dict

Use a comprehension when the whole expression fits on one readable line. If it needs nesting or multiple conditions, prefer a normal for loop.

## The GIL in Short

CPython has a Global Interpreter Lock: only one thread executes Python bytecode at a time. Threads still help for I/O-bound work (network, files) because the lock is released while waiting. For CPU-bound work, use the multiprocessing module or native extensions instead of threads.

## Strings

Strings are immutable. Building a string in a loop with `+=` creates a new string each time; collect parts in a list and use `"".join(parts)` instead. Use f-strings (`f"{name}: {value}"`) for formatting.

## Iteration Idioms

- `enumerate(items)` when you need the index and the value
- `zip(a, b)` to iterate two sequences in parallel
- `items.items()` to iterate keys and values of a dict
- `sorted(data, key=lambda x: x.field, reverse=True)` for custom ordering

## Files and JSON

Always open files with a context manager and an explicit encoding: `with open(path, "r", encoding="utf-8") as f`. For JSON, `json.load(f)` reads from a file object, `json.loads(text)` from a string; `json.dump(data, f, ensure_ascii=False, indent=4)` writes readable UTF-8 output.
