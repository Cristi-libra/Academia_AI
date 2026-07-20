# Python Best Practices

The style rules Professor Gem expects in student code. These are the reference criteria used during code reviews.

## Naming (PEP 8)

- Functions, variables, modules: `snake_case` — `load_documents`, `chunk_size`
- Classes: `PascalCase` — `EmbeddingsClient`, `ConversationContext`
- Constants: `UPPER_SNAKE_CASE` — `CHUNK_SIZE`, `API_KEY`
- Names must say what the thing IS or DOES: `user_count`, not `uc` or `data2`

## Functions

- One function, one responsibility. If you describe it with "and", split it.
- Keep functions short — if it does not fit on one screen, it is doing too much.
- Public functions get a docstring: what it does, parameters, return value.
- Prefer returning values over mutating arguments or globals.

## Error Handling

- Catch SPECIFIC exceptions: `except FileNotFoundError:`, never a bare `except:`.
- A bare except hides real bugs, including KeyboardInterrupt and typos.
- Only catch an exception if you can do something meaningful with it; otherwise let it propagate.
- Error messages must tell the user what failed AND what to do about it.

## Resources and Files

- Always use context managers: `with open(path, encoding="utf-8") as f:` — the file closes even if an exception occurs.
- Always pass an explicit `encoding` when opening text files; the platform default differs between Windows and Linux.

## Structure and Configuration

- No magic values in the code: sizes, thresholds, paths and model names belong in a configuration module as named constants.
- No secrets in the code: API keys come from environment variables, never from hardcoded strings committed to git.
- Avoid deep nesting: return early (`if not items: return []`) instead of wrapping the whole body in an if.

## Idiomatic Python

- `enumerate(items)` instead of `range(len(items))`
- Comprehensions for simple transformations, loops for complex ones
- f-strings for formatting, `"".join()` for building strings from parts
- Truthiness: `if items:` instead of `if len(items) > 0:`
- Type hints on function signatures: `def get_embedding(self, text: str) -> list[float]:`

## Comments

- Comments explain WHY, code explains WHAT. A comment that repeats the line below it is noise.
- If the code needs a comment to be understood, first try renaming and restructuring it.
