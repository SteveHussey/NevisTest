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

## Available Endpoints (brief)

- **GET /clients** – Retrieve a list of clients.
- **GET /clients/{id}/documents** – Get documents for a specific client.
- **POST /search** – Search across client data.

For full API documentation and schema details, refer to the OpenAPI specification file:

[`api_spec.yaml`](api_spec.yaml)
