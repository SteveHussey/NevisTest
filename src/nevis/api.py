"""FastAPI application, routers, and endpoint implementations for Nevis."""

from typing import Sequence

from fastapi import APIRouter, status, Depends, FastAPI, HTTPException, Query

from .models import Document, CoreApp, Client, NewClientData, NewDocumentData, ClientId, DocumentId, SearchResponse
from .utils import InvalidClientError, InvalidDocumentError

router = APIRouter()


class InstanceHolder[T]:
    def __init__(self, instance: T):
        self.instance = instance

    def __call__(self) -> T:
        return self.instance


class ClientDocCore(CoreApp):
    def add_client(self, client: NewClientData) -> Client:
        raise NotImplementedError

    def get_clients(self, client_ids: Sequence[ClientId]) -> list[Client]:
        raise NotImplementedError

    def add_document(self, client_id: ClientId, document: NewDocumentData) -> Document:
        raise NotImplementedError

    def get_client_documents(self, client_id: ClientId, doc_ids: Sequence[DocumentId]) -> list[Document]:
        raise NotImplementedError

    def search(self, query: str, limit: int = 10) -> SearchResponse:
        raise NotImplementedError


holder = InstanceHolder[CoreApp](ClientDocCore())
CoreDep = Depends(holder)


@router.post(
    "/clients",
    status_code=status.HTTP_201_CREATED,
    response_model=Client,
    summary="Create a new client",
)
def add_client(clients: NewClientData, core: CoreApp = CoreDep) -> Client:
    """Create and store a new client.
    Accepts either separate first_name/last_name fields or a combined 'name' field.
    Returns the created Client model.
    """
    return core.add_client(clients)


@router.get(
    "/clients",
    response_model=list[Client],
    status_code=status.HTTP_200_OK,
    summary="Retrieve clients",
)
def get_clients(ids: list[ClientId] = Query(alias='id'), core: CoreApp = CoreDep):
    """Retrieves client data for the requested Client IDs."""
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Client ids sent")
    try:
        return core.get_clients(ids)
    except InvalidClientError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Could not find client ID: {ex.client_id}")


@router.post(
    "/clients/{client_id}/documents",
    response_model=Document,
    status_code=status.HTTP_201_CREATED,
    summary="Add a document to a client",
)
def add_document(client_id: ClientId, payload: NewDocumentData, core: CoreApp = CoreDep) -> Document:
    """Create and store a new document for the specified client."""
    try:
        return core.add_document(client_id, payload)
    except InvalidClientError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not find client ID: {ex.client_id}")

@router.get(
    "/clients/{client_id}/documents",
    response_model=list[Document],
    status_code=status.HTTP_200_OK,
    summary="Retrieve client documents",
)
def get_client_documents(client_id: ClientId, ids: list[DocumentId] = Query(alias='id'), core: CoreApp = CoreDep) -> list[Document]:
    """Retrieves client documents for the requested Document IDs."""
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No Document ids sent")

    try:
        return core.get_client_documents(client_id, ids)
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
def search_endpoint(q: str, limit: int = Query(default=10), core: CoreApp = CoreDep) -> SearchResponse:
    """Perform a simple substring search across clients and documents."""
    return core.search(query=q, limit=limit)


app = FastAPI(title="Nevis API")
app.include_router(router)
