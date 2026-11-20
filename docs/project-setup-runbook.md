# Master New Python Project Runbook (Production-Style Solo Workflow)

A repeatable, end-to-end guide for setting up and maintaining Python repositories using `uv`, VS Code, Ruff, Pytest, GitHub Actions CI, Release Drafter, and Docker.

---

## 0. One-Time Local Machine Configuration

Run these commands once on your computer (they apply globally to all repositories):

```bash
# Automatically remove stale 'origin/<branch>' references on every git pull/fetch
git config --global fetch.prune true

# Optional alias: safely delete all local branches already merged into main
git config --global alias.cleanup '!git fetch -p && git branch --merged main | grep -v "^\*\|main" | xargs -r git branch -d'
```

---

## Phase 1: Local Project Initialization & Tooling (VS Code Terminal)

### 1. Initialize the project with `uv`
```bash
mkdir my-project && cd my-project
uv init --package
```
> **Why `--package`?** Unlike plain `uv init` (which creates a flat script folder), `--package` creates a proper installable `src/my_project/` package layout with a `[build-system]` in `pyproject.toml`. This ensures `pytest` and Docker test your actual installed package cleanly without `sys.path` workarounds.

### 2. Install development tools (`ruff` and `pytest`)
```bash
uv add --dev ruff pytest
```
> **Why both the VS Code Ruff extension and the `uv` package?** The VS Code extension provides real-time red squiggles and format-on-save while you type, while the `uv` dev package pins the exact Ruff version in `uv.lock` so your terminal and headless GitHub Actions CI run the identical rules.

### 3. Configure VS Code Workspace Settings (`.vscode/settings.json`)
Install these recommended VS Code extensions:
- **Python** (`ms-python.python`)
- **Pylance** (`ms-python.vscode-pylance`) — IntelliSense and static type checking *(installed in VS Code, not via `uv`)*
- **Ruff** (`charliermarsh.ruff`) — Linting, formatting, and import sorting
- **GitHub Pull Requests** (`GitHub.vscode-pull-request-github`) — *(Optional)* Manage PRs and local branch cleanup in VS Code

Create `.vscode/settings.json` in your project root (commit this to Git so settings travel with the repo):

```json
{
  "editor.rulers": [80, 100],
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "python.analysis.typeCheckingMode": "standard"
}
```
> **Settings rationale:**
> - `"editor.rulers": [80, 100]` adds vertical guides at 80 characters (PEP 8 docstring/comment width) and 100 characters (hard line ceiling).
> - `"python.analysis.typeCheckingMode": "standard"` catches type mismatches and missing annotations without the noise of `strict` mode.
> - VS Code automatically detects `uv`'s `.venv` on Windows, macOS, and Linux without hardcoding an OS-specific interpreter path.

### 4. Set up a multi-file production package layout (`src/my_project/`)
Keep `__init__.py` free of startup side effects, isolate logging in its own module, and use `main.py` as your entry point:

- **`src/my_project/__init__.py`** *(dynamic version synced from `pyproject.toml`)*:
  ```python
  """My Project package."""

  from importlib.metadata import PackageNotFoundError, version

  try:
      __version__ = version("my-project")
  except PackageNotFoundError:
      __version__ = "0.0.0-dev"
  ```

- **`src/my_project/logging_config.py`** *(rotating file logs + console `stdout` for Docker)*:
  ```python
  import logging
  import os
  from logging.handlers import RotatingFileHandler
  from pathlib import Path


  def setup_logging() -> logging.Logger:
      Path("logs").mkdir(exist_ok=True)
      log_level = os.getenv("LOG_LEVEL", "INFO").upper()

      formatter = logging.Formatter(
          "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
      )

      file_handler = RotatingFileHandler(
          "logs/app.log",
          maxBytes=5_000_000,  # 5 MB per file
          backupCount=3,       # Keep 3 rotated backups
          encoding="utf-8",
      )
      file_handler.setFormatter(formatter)

      console_handler = logging.StreamHandler()
      console_handler.setFormatter(formatter)

      logging.basicConfig(
          level=getattr(logging, log_level, logging.INFO),
          handlers=[file_handler, console_handler],
      )
      return logging.getLogger("my_project")
  ```

- **`src/my_project/main.py`** *(application entry point)*:
  ```python
  from my_project.logging_config import setup_logging


  def add(a: int, b: int) -> int:
      return a + b


  def main() -> None:
      logger = setup_logging()
      logger.info("Application started.")


  if __name__ == "__main__":
      main()
  ```

- **Update `pyproject.toml`** to configure Ruff and point your CLI script to `main.py`:
  ```toml
  [project.scripts]
  my-project = "my_project.main:main"

  [tool.ruff]
  line-length = 100

  [tool.ruff.lint]
  select = ["E", "F", "I", "UP", "B"]
  ```

### 5. Create a starter test in `tests/test_main.py`
*(Do not put `__init__.py` inside `tests/`.)*

```bash
mkdir -p tests
```

```python
# tests/test_main.py
from my_project.main import add


def test_add() -> None:
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
```

### 6. Create `.env.example` and update `.gitignore`
- **`.env.example`** *(committed to Git as a safe blueprint; note there is no `.txt` extension)*:
  ```env
  # Illustrative example variables — keep only variables your app actually reads
  LOG_LEVEL=INFO
  API_KEY=your_api_key_here
  ```
  > **Local usage:** Copy `.env.example` to `.env` (`cp .env.example .env`), fill in real secrets, and run locally via `uv run --env-file .env my-project`. Never commit `.env`.

- **`.gitignore`** *(append these blocks to the `.gitignore` generated by `uv init`)*:
  ```gitignore
  # Secrets
  .env

  # Local runtime logs
  logs/
  *.log
  ```

### 7. Create `.github/` CI, Release Drafter, and PR templates
```bash
mkdir -p .github/workflows
```

- **`.github/workflows/ci.yml`** *(runs Ruff and Pytest on every Pull Request)*:
  ```yaml
  name: CI

  on:
    pull_request:
      branches:
        - main

  jobs:
    test-and-lint:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v5
        - name: Install dependencies
          run: uv sync --frozen
        - name: Lint and check formatting
          run: uv run ruff check . && uv run ruff format --check .
        - name: Run tests
          run: uv run pytest
  ```

- **`.github/release-drafter.yml`** *(categorizes merged PRs and computes `MAJOR.MINOR.PATCH`)*:
  ```yaml
  name-template: 'v$RESOLVED_VERSION'
  tag-template: 'v$RESOLVED_VERSION'

  categories:
    - title: '💥 Breaking Changes'
      labels:
        - 'breaking'
    - title: '🚀 Features'
      labels:
        - 'feature'
        - 'enhancement'
    - title: '🐛 Bug Fixes'
      labels:
        - 'fix'
        - 'bug'
    - title: '🧰 Maintenance'
      labels:
        - 'chore'
        - 'dependencies'
        - 'docs'

  change-template: '- $TITLE (#$NUMBER)'

  version-resolver:
    major:
      labels:
        - 'breaking'
    minor:
      labels:
        - 'feature'
        - 'enhancement'
    patch:
      labels:
        - 'fix'
        - 'bug'
        - 'chore'
        - 'dependencies'
        - 'docs'
    default: patch

  template: |
    ## Changes

    $CHANGES
  ```

- **`.github/workflows/release-drafter.yml`** *(updates your Draft Release on merge to `main`)*:
  ```yaml
  name: Release Drafter

  on:
    push:
      branches:
        - main

  permissions:
    contents: write
    pull-requests: read

  jobs:
    update_release_draft:
      runs-on: ubuntu-latest
      steps:
        - uses: release-drafter/release-drafter@v6
          env:
            GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  ```

- **`.github/pull_request_template.md`** *(captures your engineering decision log on every PR)*:
  ```markdown
  ## What Changed
  <!-- Briefly summarize the code changes in 1–2 sentences. -->


  ## Why / Decision Log
  <!-- Record the reasoning behind this change:
       - What problem were you solving?
       - What alternatives did you consider and reject?
       - Are there any trade-offs or caveats to remember later? -->


  ## Type of Change (Remember to add the matching GitHub label!)
  - [ ] 💥 `breaking` — Incompatible API or behavior change (bumps MAJOR)
  - [ ] 🚀 `feature` / `enhancement` — New backward-compatible feature (bumps MINOR)
  - [ ] 🐛 `fix` / `bug` — Bug fix (bumps PATCH)
  - [ ] 🧰 `chore` / `docs` / `dependencies` — Maintenance or docs (bumps PATCH)
  ```

### 8. Verify locally and make your initial commit on `main`
```bash
uv run ruff check . && uv run ruff format . && uv run pytest
git add .
git commit -m "Initial project setup with uv, CI, logging, and GitHub templates"
```

---

## Phase 2: Create & Configure the GitHub Repository

1. **Create a new Public repository on GitHub** *(leave README, `.gitignore`, and license unchecked)*.
2. **Push `main` to GitHub:**
   ```bash
   git remote add origin https://github.com/<your-username>/my-project.git
   git branch -M main
   git push -u origin main
   ```
3. **Configure GitHub Repository Settings:**
   - **General → Pull Requests:** Check **Automatically delete head branches**.
   - **Issues → Labels:** Keep `enhancement`, `bug`, `dependencies`; rename `documentation` → `docs`; create `breaking` (red) and `chore` (gray).
   - **Rules → Rulesets → New branch ruleset:** Target **Default branch (`main`)**, set to **Active**, and check:
     - **Restrict deletions**
     - **Require a pull request before merging** *(keep Required approvals = `0`)*
     - **Block force pushes**
     - *(After your first PR runs CI, return here and check **Require status checks to pass before merging** → select **`test-and-lint`**.)*

---

## Phase 3: Day-to-Day Feature & Bug-Fix Cycle

*From this point on, `main` is protected—all work happens on branches.*

1. **Create a branch & add runtime dependencies:**
   ```bash
   git checkout -b feat/your-feature
   uv add <package-name>
   ```
2. **Write code & tests, then run checks locally:**
   ```bash
   uv run ruff check . && uv run ruff format . && uv run pytest
   ```
3. **Commit, push, and open a Pull Request:**
   ```bash
   git add .
   git commit -m "Describe your change"
   git push -u origin feat/your-feature
   ```
   - Fill in **What Changed** and **Why / Decision Log** in the auto-loaded PR template.
   - Select the matching label (`breaking`, `enhancement`, `bug`, `chore`, `docs`, or `dependencies`).
   - Wait for **`test-and-lint`** to turn green (`✓`), then click **Merge pull request**.
4. **Sync `main` locally and remove merged local branches:**
   ```bash
   git checkout main && git pull && git cleanup
   ```

---

## Phase 4: Production Containerization & Publishing Releases

### 1. Add Docker support via a branch + PR *(once core modules and `uv.lock` are stable)*

- **`.dockerignore`** *(keeps build context small and prevents leaking secrets, logs, or editor files into the image)*:
  ```dockerignore
  .git
  .github
  .vscode
  .venv
  .env
  __pycache__
  *.pyc
  logs/
  *.log
  tests/
  .pytest_cache
  .ruff_cache
  ```

- **`Dockerfile`** *(hardened non-root multi-stage build using `uv.lock`)*:
  ```dockerfile
  # Stage 1: Build dependencies in an isolated layer
  FROM python:3.12-slim AS builder
  COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
  WORKDIR /app

  COPY pyproject.toml uv.lock ./
  RUN uv sync --frozen --no-install-project --no-dev

  COPY . .
  RUN uv sync --frozen --no-dev

  # Stage 2: Minimal non-root production runtime image
  FROM python:3.12-slim
  RUN useradd --create-home appuser
  WORKDIR /app

  COPY --from=builder /app/.venv /app/.venv
  COPY --from=builder /app/src /app/src

  USER appuser
  ENV PATH="/app/.venv/bin:$PATH"
  CMD ["python", "-m", "my_project.main"]
  ```

### 2. Publishing Releases (Draft vs. Published)
- **Draft Releases Stay Private Until Published:** Release Drafter continuously collects merged PRs into a single unpublished **Draft** under **Releases**, automatically updating the bullet list and bumping `MAJOR.MINOR.PATCH` until you are ready to cut a release.
- **Publish All Release Levels:** Teams publish `MAJOR`, `MINOR`, and `PATCH` releases—not just major versions. Bundle related PRs into a meaningful milestone (or publish immediately for an urgent bug fix).
- **How to Publish:** Go to **Releases** → click **Edit (pencil)** on the Draft → optionally add a summary note at the top → click **Publish release**. This creates a permanent Git tag on `main`, displays the release as `Latest` on the main **Code** page, and resets Release Drafter to start a fresh draft for the next PR.
- **Leave "Set as a pre-release" Unchecked:** Pre-releases are only for `alpha`/`beta`/`rc` builds of mature `v1.0.0+` libraries and hide the release from the main **Code** page's `Latest` badge. Using `v0.x.y` versions already signals early-stage development.
