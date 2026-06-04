# AGENTS.md

This repository currently contains a minimal IBM i analysis project.

## What to know

- `requirements.txt` is the primary dependency manifest.
- `.gitignore.txt` already excludes `.env`, `venv/`, `__pycache__/`, `*.pyc`, and generated analysis artifacts.
- The repository uses environment configuration through `.env` (example values are shown in `.env.txt`).
- Top-level folders are intended for:
  - `ibmi_side/` – IBM i integration, analysis, or platform-specific code
  - `python_side/` – Python-side processing, tooling, or orchestration

## Environment

Do not commit secrets. Keep the actual `.env` file out of source control.

Expected environment variables:
- `OPENAI_API_KEY`
- `IBMI_HOST`
- `IBMI_USER`
- `IBMI_PASS`
- `IBMI_LIBRARY`
- `IFS_PATH`
- `LOCAL_PATH`

## Agent behavior

- Prioritize working with the files under `python_side/` and `ibmi_side/`.
- If the workspace has no code in those directories, ask the user for the intended project structure before generating large scaffolding.
- Use `pip install -r requirements.txt` for dependency installation.
- Preserve `.gitignore.txt` rules and avoid introducing committed secrets or credentials.
- When creating documentation or instructions, keep content concise and link to repository files rather than duplicating them.

## Notes for future updates

- If a `.github/copilot-instructions.md` file is later added, follow existing instructions there instead of this file.
- If the repository acquires a README or docs, link to them rather than copying their contents.