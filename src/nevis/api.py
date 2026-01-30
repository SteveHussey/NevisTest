"""FastAPI application, routers, and endpoint implementations for Nevis."""
from contextlib import asynccontextmanager

from fastapi import APIRouter, status, Depends, FastAPI, HTTPException, Query, Request
from qdrant_client import AsyncQdrantClient

from .core import ClientDocCore
from .models import Document, CoreApp, Client, NewClientData, NewDocumentData, ClientId, DocumentId, SearchResponse
from .store import QdrantStore
from .utils import InvalidClientError, InvalidDocumentError

router = APIRouter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ Create once - shared across requests
    qdrant_client = AsyncQdrantClient(url="http://localhost:6333")
    store = QdrantStore(qdrant_client, "BAAI/bge-small-en")
    await store.setup_qdrant()
    app.state.core = ClientDocCore(store)
    yield
    # ✅ Cleanup on shutdown
    await qdrant_client.close()


def get_core(request: Request) -> CoreApp:
    return request.app.state.core


CoreDep = Depends(get_core)


@router.post(
    "/clients",
    status_code=status.HTTP_201_CREATED,
    response_model=Client,
    summary="Create a new client",
)
async def add_client(clients: NewClientData, core: CoreApp = CoreDep) -> Client:
    """Create and store a new client.
    Accepts either separate first_name/last_name fields or a combined 'name' field.
    Returns the created Client model.
    """
    return await core.add_client(clients)


@router.get(
    "/clients",
    response_model=list[Client],
    status_code=status.HTTP_200_OK,
    summary="Retrieve clients",
)
async def get_clients(ids: list[ClientId] = Query(alias='id'), core: CoreApp = CoreDep):
    """Retrieves client data for the requested Client IDs."""
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Client ids sent")
    try:
        return await core.get_clients(ids)
    except InvalidClientError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Could not find client ID: {ex.client_id}")


@router.post(
    "/clients/{client_id}/documents",
    response_model=Document,
    status_code=status.HTTP_201_CREATED,
    summary="Add a document to a client",
)
async def add_document(client_id: ClientId, payload: NewDocumentData, core: CoreApp = CoreDep) -> Document:
    """Create and store a new document for the specified client."""
    try:
        return await core.add_document(client_id, payload)
    except InvalidClientError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not find client ID: {ex.client_id}")

@router.get(
    "/clients/{client_id}/documents",
    response_model=list[Document],
    status_code=status.HTTP_200_OK,
    summary="Retrieve client documents",
)
async def get_client_documents(client_id: ClientId, ids: list[DocumentId] = Query(alias='id'), core: CoreApp = CoreDep) -> list[Document]:
    """Retrieves client documents for the requested Document IDs."""
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No Document ids sent")

    try:
        return await core.get_client_documents(client_id, ids)
    except InvalidClientError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Could not find client ID: {ex.client_id}")
    except InvalidDocumentError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Could not find document ID for client [{ex.client_id}]: {ex.document_id}")

@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search clients and documents",
)
async def search_endpoint(q: str, limit: int = Query(default=10), core: CoreApp = CoreDep) -> SearchResponse:
    """Perform a simple substring search across clients and documents."""
    return await core.search(query=q, limit=limit)


app = FastAPI(title="Nevis API", lifespan=lifespan)
app.include_router(router)
