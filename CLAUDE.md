# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

- **Run the application**:
  ```bash
  uv run python -m nevis
  ```
  The server starts at `http://127.0.0.1:8000`.

- **Run the full test suite**:
  ```bash
  uv run pytest
  ```

- **Run a single test** (replace `<path>` and `<test_name>` with the desired test file and function):
  ```bash
  uv run pytest <path>::<test_name>
  ```
  Example:
  ```bash
  uv run pytest tests/nevis_test/test_api.py::TestAddClient::test_valid_client_data_success
  ```

- **Build the Docker image**:
  ```bash
  podman build -t nevis_test:latest --load --pull .
  ```

- **Run the container**:
  ```bash
  podman run -p 8000:8000 nevis_test:latest
  ```

- **Start the full stack (API + Qdrant) with Compose**:
  ```bash
  podman-compose -f compose.yaml up
  ```

- **Linting / Formatting**: (not explicitly configured, but standard tools such as `ruff` or `black` can be added as needed).

## High‑Level Architecture Overview

- **FastAPI (`api.py`)** – Exposes REST endpoints for client and document management and a search endpoint.
- **Core Layer (`core.py`)** – Implements `ClientDocCore` which delegates business logic to a `DataStore` implementation.
- **Data Store Interface (`models.py`)** – Abstract base classes defining required CRUD and search operations.
- **Qdrant Store (`store.py`)** – Concrete `DataStore` using Qdrant vector database for storage, ID generation, and ANN search. Payloads store the full Pydantic model data.
- **Pydantic Models (`models.py`)** – Typed schemas for clients, documents, creation DTOs, and search responses.
- **Utilities (`utils.py`)** – ID generator and custom exception types.
- **Entry point (`__main__.py`)** – Starts the FastAPI app with Uvicorn.
- **Containerisation** – Dockerfile builds a minimal runtime image; `compose.yaml` defines services for the API and Qdrant.

The system follows a simple layered design: API → Core → DataStore → Vector DB. The vector store also serves as the metadata store via payloads, eliminating a separate relational database.
