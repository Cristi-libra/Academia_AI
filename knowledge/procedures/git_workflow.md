# Git Workflow

The git practices Professor Gem teaches and expects in student projects.

## Commits

- Commit small and often: one logical change per commit, not "everything from today".
- Write the message as what the commit DOES: "Add chunk overlap to document chunker", not "changes" or "fix".
- Commit only after the code runs — a commit is a checkpoint you can return to.

## Branches

- `main` (or `master`) stays working at all times.
- New features and experiments go on a separate branch: `git checkout -b feature/chunk-overlap`.
- Merge back when the feature works; delete the branch after merging.
- To rename the default local branch to the GitHub convention: `git branch -M main`.

## What NEVER Goes into a Repository

- **Secrets**: API keys, passwords, tokens. Use environment variables and read them with `os.environ.get`. A key that was ever committed must be considered leaked and regenerated — deleting it in a later commit does not remove it from history.
- **Virtual environments**: `venv/` is recreated from `requirements.txt`, never committed.
- **Generated files**: caches (`__pycache__/`, `*.pyc`), build outputs, generated data files (for example an embeddings file) — they are reproducible.
- **Personal data**: local records about real people.

## .gitignore

Create the `.gitignore` file BEFORE the first commit. Minimum for a Python project:

- `venv/`
- `__pycache__/`
- `*.pyc`
- `.env`
- generated data files specific to the project

If a file was already committed before being ignored, remove it from tracking with `git rm --cached <file>` — the ignore rule alone does not untrack it.

## Everyday Commands

- `git status` — always check before committing what will actually go in
- `git add <file>` — prefer adding specific files over `git add .`
- `git diff` — review your own changes before committing them
- `git log --oneline` — the history at a glance
- `git push -u origin main` — first push sets the upstream; afterwards plain `git push` suffices

## Common Errors

- "src refspec main does not match any" — the local branch has a different name (often `master`); rename it with `git branch -M main` or push the actual name.
- Merge conflicts are normal: open the conflicted file, choose the correct version between the `<<<<<<<` and `>>>>>>>` markers, then add and commit.
