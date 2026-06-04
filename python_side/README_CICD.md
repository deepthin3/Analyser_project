CI/CD for python_side
=====================

Short guide to run the pipeline and add CI for continuous analysis.

Purpose
- Run the analysis pipeline automatically on pushes and pull requests.
- Ensure dependencies install and quick smoke tests run.

Quick local steps
1. Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1    # PowerShell
# or
venv\Scripts\activate        # cmd
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run a quick smoke test (skips slow sync):

```powershell
python test_pipeline.py
```

GitHub Actions (minimal) example
Create `.github/workflows/ci.yml` in your repo with this content:

```yaml
name: CI
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: python -m pip install -r requirements.txt
      - name: Run quick pipeline test
        run: python test_pipeline.py
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

Secrets and environment
- Store sensitive values in repository secrets (`OPENAI_API_KEY`, `IBMI_*`).
- The CI run should not contain real IBM i credentials unless running in a secure environment; prefer using cached sources or mock data for public CI.

Caching dependencies
- Use `actions/cache` to cache pip downloads for faster builds.

Notes
- For production runs, consider restricting analysis to changed files or providing a manifest to avoid sending large contexts to the AI.
- See the project root for additional docs and the `test_pipeline.py` helper.
