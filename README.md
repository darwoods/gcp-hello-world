# gcp-hello-world

## Overview

`gcp-hello-world` is a small Python demo designed to demonstrate a modern, container-friendly application deployed to Google Cloud Run. It provides a simple command-line entry point that prints a welcome message.

## Requirements

- Python 3.15 or newer
- [uv](https://docs.astral.sh/uv/) for dependency management

## Getting Started

### Option 1: Using uv

Clone the repository, then synchronize the project environment:

```powershell
git clone <repository-url>
cd gcp-hello-world
uv sync
```

Run the application:

```powershell
uv run gcp-hello-world
```

### Option 2: Using pip

Create and activate a virtual environment, then install the project in editable mode:

```powershell
git clone <repository-url>
cd gcp-hello-world
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Run the application:

```powershell
gcp-hello-world
```

## Usage

You can also run the application through `uv` directly:

```powershell
uv run gcp-hello-world
```

For direct development execution:

```powershell
uv run python src/gcp_hello_world/main.py
```

## Project Structure

```text
gcp-hello-world/
|-- src/gcp_hello_world/
|   |-- __init__.py
|   `-- main.py
|-- pyproject.toml
|-- uv.lock
`-- README.md
```