# gcp-hello-world

## Overview

`gcp-hello-world` is a containerized Python web application built with **FastAPI** and **Gradio**, designed for deployment to Google Cloud Run. It serves both a JSON REST API and an interactive Gradio web UI from a single Uvicorn server.

The repository also retains the original `hello_world` Rich-based terminal demo under `src/hello_world/`.

## Requirements

- **Python 3.12+** (`requires-python = ">=3.12"`)
- **[uv](https://docs.astral.sh/uv/)** (recommended) or `pip`
- **Docker** (optional, for container builds)

## Getting Started

### Option 1: Using `uv` (Recommended)

Clone the repository and synchronize the virtual environment and dependencies:

```powershell
git clone <repository-url>
cd gcp-hello-world
uv sync
```

Start the local development server:

```powershell
uv run uvicorn gcp_hello_world.main:app --reload --port 8080
```

### Option 2: Using `pip`

Create and activate a virtual environment, then install the project in editable mode:

```powershell
git clone <repository-url>
cd gcp-hello-world
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Start the local development server:

```powershell
uvicorn gcp_hello_world.main:app --reload --port 8080
```

## What Runs in Your Browser

Once Uvicorn starts (`Uvicorn running on http://127.0.0.1:8080`), open the following URLs in your browser:

| URL | What You'll See |
| :--- | :--- |
| `http://127.0.0.1:8080/` | **Status JSON** — Returns `{"status": "running", ...}` with paths to the API, docs, and UI. |
| `http://127.0.0.1:8080/ui` | **Gradio Web UI** — Interactive `"Cloud Run Gradio Test"` page with a **Name** input, **Generate Greeting** button, and **Server Response** output showing the greeting and UTC server time. |
| `http://127.0.0.1:8080/api/greet?name=Developer` | **Greeting API** — Returns a JSON object with a greeting `message` and UTC `timestamp` (`name` defaults to `"World"` if omitted). |
| `http://127.0.0.1:8080/docs` | **Swagger UI** — Interactive FastAPI documentation for exploring and testing API endpoints. |

## Running the CLI Demo

To run the standalone Rich terminal demo in `src/hello_world/`:

```powershell
uv run python src/hello_world/main.py
```

## Docker

Build and run the container locally (exposing port `8080`, matching Cloud Run's default `$PORT`):

```powershell
docker build -t gcp-hello-world .
docker run --rm -p 8080:8080 gcp-hello-world
```

Then open `http://127.0.0.1:8080/ui` (or any of the endpoints above) in your browser.

## Project Structure

```text
gcp-hello-world/
|-- src/
|   |-- gcp_hello_world/
|   |   |-- __init__.py
|   |   |-- logic.py        # Greeting generation logic
|   |   |-- main.py         # FastAPI app + mounted Gradio UI
|   |   `-- ui.py           # Gradio Blocks interface
|   `-- hello_world/
|       |-- __init__.py
|       `-- main.py         # Standalone Rich CLI demo
|-- .dockerignore
|-- .python-version
|-- Dockerfile
|-- pyproject.toml
|-- uv.lock
`-- README.md
```
