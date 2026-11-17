# gcp-hello-world

## Overview

`gcp-hello-world` is a small Python demo designed to demonstrate a modern, container-friendly application deployed to Google Cloud Run. It provides a simple command-line entry point that prints a welcome message.

## Requirements

- Python 3.15 or newer
- [uv](https://docs.astral.sh/uv/) for dependency management

## Getting Started

Clone the repository and install the project dependencies:

```powershell
git clone <repository-url>
cd gcp-hello-world
uv sync
```

## Usage

Run the application through the project entry point:

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