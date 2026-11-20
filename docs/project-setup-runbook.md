# Master New Python Project Runbook (Production-Style Solo Workflow)

A repeatable, end-to-end guide for bootstrapping a Python repository with `uv`, multi-file package structure, VS Code + Ruff + Pylance, `pytest`, GitHub Actions CI, Release Drafter, PR decision templates, and a hardened production `Dockerfile`.

---

## 0. One-Time Local Machine Setup (Run Once per Computer)

These global Git settings apply to every repository on your machine:

```bash
# Automatically remove stale 'origin/<branch>' bookmarks on every git pull/fetch
git config --global fetch.prune true

# Optional alias: safely delete all local branches already merged into main
git config --global alias.cleanup '!git fetch -p && git branch --merged main | grep -v "^\*\|main" | xargs -r git branch -d'
```

### Recommended VS Code Extensions
Install these official extensions once in VS Code:
- **Python** (`ms-python.python`)
- **Pylance** (`ms-python.vscode-pylance`) — IntelliSense and static type checking
- **Ruff** (`charliermarsh.ruff`) — Linting, formatting, and import sorting
- **GitHub Pull Requests** (`GitHub.vscode-pull-request-github`) — *(Optional)* Manage PRs and delete local branches inside VS Code

---

## Phase 1: Local Initialization & Multi-File Project Structure

### 1. Initialize Project with `uv` (`--package` creates a clean `src/` layout)
```bash
mkdir my-project && cd my-project
uv init --package
```

### 2. Install Development Dependencies
```bash
uv add --dev ruff pytest
```
> **Why both the Ruff extension and `uv` package?** The VS Code extension formats and highlights issues live as you type, while `uv add --dev ruff` pins the exact Ruff version in `uv.lock` so your terminal and headless GitHub Actions CI run identical rules. Pylance is an IDE-only extension, so it is installed in VS Code rather than via `uv`.

### 3. Configure Workspace VS Code Settings (`.vscode/settings.json`)
Create `.vscode/settings.json` so editor rules travel with the repository across machines (VS Code's Python extension auto-detects `.venv` across Windows, macOS, and Linux):

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

### 4. Set Up Multi-File Package Layout (`src/my_project/`)
Keep `__init__.py` free of side effects, isolate logging setup in its own module, and expose a clear `main.py` entry point:

```text
my-project/
├── pyproject.toml
├── src/
│   └── my_project/
│       ├── __init__.py          # Package metadata (auto-synced version, zero side effects)
│       ├── logging_config.py    # Rotating file + console logging setup
│       └── main.py              # Application entry point & core logic
└── tests/
    └── test_main.py             # Pytest unit tests (do NOT add __init__.py here)
```

- **`src/my_project/__init__.py`** *(dynamically reads the version from `pyproject.toml` so there is only one source of truth)*:
  ```python
  """My Project package."""

  from importlib.metadata import PackageNotFoundError, version

  try:
      __version__ = version("my-project")
  except PackageNotFoundError:
      __version__ = "0.0.0-dev"
  ```

- **`src/my_project/logging_config.py`** *(uses `RotatingFileHandler` so logs cap at 5 MB and reads `LOG_LEVEL` from environment variables)*:
  ```python
  import logging
  import os
  from logging.handlers import RotatingFileHandler
  from pathlib import Path


  def setup_logging(logger_name: str = "my_project") -> logging.Logger:
      log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
      log_level = getattr(logging, log_level_name, logging.INFO)

      Path("logs").mkdir(exist_ok=True)
      formatter = logging.Formatter(
          "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
      )

      file_handler = RotatingFileHandler(
          "logs/app.log",
          maxBytes=5_000_000,  # 5 MB per file
          backupCount=3,       # Keep 3 rotated backup files
          encoding="utf-8",
      )
      file_handler.setFormatter(formatter)

      console_handler = logging.StreamHandler()
      console_handler.setFormatter(formatter)

      root_logger = logging.getLogger()
      root_logger.setLevel(log_level)
      root_logger.handlers.clear()
      root_logger.addHandler(file_handler)
      root_logger.addHandler(console_handler)

      return logging.getLogger(logger_name)
  ```

- **`src/my_project/main.py`**:
  ```python
  from my_project import __version__
  from my_project.logging_config import setup_logging


  def add(a: int, b: int) -> int:
      return a + b


  def main() -> None:
      logger = setup_logging()
      logger.info("Application started (version=%s).", __version__)


  if __name__ == "__main__":
      main()
  ```

### 5. Configure `pyproject.toml` Entry Point & Ruff Rules
In `pyproject.toml`, point `[project.scripts]` to `my_project.main:main` and add standard Ruff lint rules:

```toml
[project.scripts]
my-project = "my_project.main:main"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

### 6. Create Starter Test (`tests/test_main.py`)
```bash
mkdir -p tests
```
```python
from my_project.main import add


def test_add() -> None:
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
```

### 7. Create `.env.example` & Update `.gitignore`
- **`.env.example`** *(committed as documentation for required environment variables)*:
  ```env
  APP_ENV=development
  LOG_LEVEL=INFO
  DATABASE_URL=sqlite:///local.db
  ```
- **`.gitignore`** *(append to the file generated by `uv init`)*:
  ```gitignore
  # Secrets & local runtime logs
  .env
  logs/
  *.log
  ```

### 8. Create `.github/` Automation & PR Templates
```bash
mkdir -p .github/workflows
```

- **`.github/workflows/ci.yml`** *(runs Ruff lint/format checks and Pytest on every PR)*:
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

- **`.github/release-drafter.yml`** *(sorts merged PRs and computes `MAJOR.MINOR.PATCH` versions)*:
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

### 9. Verify Locally & Make Initial Commit on `main`
```bash
uv run ruff check . && uv run ruff format . && uv run pytest
git add .
git commit -m "Initial project setup with uv, CI, logging, and GitHub templates"
```

---

## Phase 2: Create & Configure the GitHub Repository

10. **Create a new Public repository on GitHub** *(leave README, `.gitignore`, and license unchecked)*.
11. **Push `main` to GitHub:**
    ```bash
    git remote add origin https://github.com/<your-username>/my-project.git
    git branch -M main
    git push -u origin main
    ```
12. **Configure GitHub Repository Settings:**
    - **General → Pull Requests:** Check **Automatically delete head branches**.
    - **Issues → Labels:** Keep `enhancement`, `bug`, `dependencies`; rename `documentation` → `docs`; create `breaking` (red) and `chore` (gray).
    - **Rules → Rulesets → New branch ruleset:** Target **Default branch (`main`)**, set to **Active**, and check:
      - **Restrict deletions**
      - **Require a pull request before merging** *(keep Required approvals = `0`)*
      - **Block force pushes**
      - *(After PR #1 runs CI, return here and check **Require status checks to pass before merging** → select **`test-and-lint`**.)*

---

## Phase 3: Day-to-Day Feature & Bug-Fix Cycle

*From this point forward, `main` is protected—all changes go through branches and PRs.*

13. **Create a branch & add runtime dependencies:**
    ```bash
    git checkout -b feat/your-feature
    uv add <package-name>
    ```
14. **Write code + tests, then run local checks:**
    ```bash
    uv run ruff check . && uv run ruff format . && uv run pytest
    ```
15. **Commit, push, and open a Pull Request:**
    ```bash
    git add .
    git commit -m "Describe your change"
    git push -u origin feat/your-feature
    ```
    - Fill in **What Changed** and **Why / Decision Log** in the auto-loaded PR template.
    - Select the matching label (`breaking`, `enhancement`, `bug`, `chore`, `docs`, `dependencies`).
    - Wait for **`test-and-lint`** to turn green (`✓`), then click **Merge pull request**.
16. **Clean up locally:**
    ```bash
    git checkout main && git pull && git cleanup
    ```

---

## Phase 4: Production Containerization & Publishing Releases

17. **Add Docker files via a branch + PR** *(once core modules and `uv.lock` are stable)*:
    - **`.dockerignore`**:
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
    - **`Dockerfile`** *(multi-stage production build running as a non-root user)*:
      ```dockerfile
      # Stage 1: Build dependencies in an isolated layer
      FROM python:3.12-slim AS builder
      COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
      WORKDIR /app

      COPY pyproject.toml uv.lock ./
      RUN uv sync --frozen --no-install-project --no-dev

      COPY . .
      RUN uv sync --frozen --no-dev

      # Stage 2: Minimal hardened production runtime image
      FROM python:3.12-slim
      RUN useradd --create-home --shell /bin/bash appuser
      WORKDIR /app

      COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
      COPY --from=builder --chown=appuser:appuser /app/src /app/src

      USER appuser
      ENV PATH="/app/.venv/bin:$PATH"
      CMD ["python", "-m", "my_project.main"]
      ```
18. **Publish milestone releases:**
    - Open **Releases** → click **Edit (pencil)** on the Draft release (`v0.1.0`, `v1.0.0`, etc.) → leave **"Set as a pre-release" unchecked** → click **Publish release**.
    - This creates a permanent Git tag on `main`, displays the release as `Latest` on the main **Code** page, and resets Release Drafter to accumulate a fresh draft for the next PR.
