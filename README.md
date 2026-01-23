# Nevis Backend Home Task
### Implementation by Steven Hussey

## Running the Application

Start the FastAPI application with UV:

```bash
uv run python -m nevis
```

The server will be available at `http://127.0.0.1:8000`.

## Testing

Run the test suite with pytest:

```bash
uv run pytest
```

All tests are located in the `tests/` directory.

## Architecture

The implementation is based on **Option 2** (vector store) from [Initial Architecture Options.md](Initial%20Architecture%20Options.md).

Qdrant is being used for the vector database along with the embedding model `BAAI/bge-small-en`, which is enough to 
support the requested queries.

**Key Components**

| Component | Role                                                                                                          | Main File(s) |
|-----------|---------------------------------------------------------------------------------------------------------------|--------------|
| FastAPI Application | HTTP server exposing REST endpoints for client and document management, plus a search endpoint.               | `api.py` |
| Core Layer (`CoreApp`) | Business‑logic façade used by the API; delegates to data store implementation.                                | `core.py` |
| Data Store Interface | Abstract interface for data operations.                                                                       | `models.py` |
| Qdrant Store | Concrete store using Qdrant vector DB; handles ID generation, upserts, scroll queries and ANN searches. | `store.py` |
| Pydantic Models | Typed request/response schemas (Client, Document, NewClientData, NewDocumentData, SearchResponse).            | `models.py` |
| Utilities | ID generators, custom exception types.                                                                        | `utils.py` |

The current code implements **Option 2** (vector store) using . The relational metadata layer is effectively stored inside Qdrant payloads, keeping the architecture simple while providing semantic search capabilities.

## Deploying

Build a container version of the application with one of the following commands:

```bash
docker build -t nevis_test:latest --load --pull .
podman build -t nevis_test:latest --load --pull .
```

Run the container with a derivative of the following commands:

```bash
docker run -p 8000:8000 nevis_test:latest
podman run -p 8000:8000 localhost/nevis_test:latest
```

To run the full deployment including Qdrant, you can use the compose file provided:

```bash
docker-compose up
podman-compose up
```

Containers have been tested using Podman.

## Available Endpoints Summary

- **POST /clients** – Add new client data.
- **GET /clients** – Retrieve client data.
- **POST /clients/{client_id}/documents** – Add documents for a client.
- **GET /clients/{client_id}/documents** – Get documents for a client.
- **POST /search** – Search for client or document data.

For full API documentation and schema details, refer to the OpenAPI specification file:

[`api_spec.yaml`](api_spec.yaml)

## Future Improvements

- Implement CI checks. 
- Write a utility to bulk insert data via the API and generate some sample data to accompany it.
- Add an LLM agent to the search method of ClientDocCore, using CrewAI or equivalent.
- Query vetting/guarding via LLM agent.
- Add authentication and access control to the API.
- Result interpretation via agent.
