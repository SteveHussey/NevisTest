"""Pydantic models and in‑memory storage for the Nevis API."""
from abc import ABC, abstractmethod
from collections.abc import Collection
from datetime import datetime, UTC
from typing import Sequence, NewType, NamedTuple

from pydantic import BaseModel, Field, EmailStr


ClientId = NewType("ClientId", str)
DocumentId = NewType("DocumentId", str)


class Client(BaseModel):
    """Client representation."""
    id: ClientId = Field(..., description="Unique client identifier")
    first_name: str
    last_name: str
    email: EmailStr
    description: str | None = Field(default=None)
    social_links: list[str] = Field(default_factory=lambda: [], description="List of social links")


class Document(BaseModel):
    """Document representation belonging to a client."""
    id: DocumentId = Field(..., description="Unique document identifier")
    client_id: ClientId = Field(..., description="Identifier of the owning client")
    title: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class NewClientData(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    description: str | None = None
    social_links: list[str] = Field(default_factory=lambda: [], description="List of social links")


class NewDocumentData(BaseModel):
    title: str
    content: str


class SearchResponse(BaseModel):
    data: list[Client | Document] = Field(default_factory=lambda: [])
    text: str | None =  None


class CoreApp(ABC):
    @abstractmethod
    async def add_client(self, client: NewClientData) -> Client:
        """Store a new client and return it."""
        ...

    @abstractmethod
    async def get_clients(self, client_ids: Sequence[ClientId]) -> list[Client]:
        """Retrieve client data from IDs."""
        ...

    @abstractmethod
    async def add_document(self, client_id: ClientId, document: NewDocumentData) -> Document:
        """Store a new document and return it."""
        ...

    @abstractmethod
    async def get_client_documents(self, client_id: ClientId, doc_ids: Sequence[DocumentId]) -> list[Document]:
        """Return documents belonging to a client."""
        ...

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> SearchResponse:
        ...


class DataStore(ABC):
    @abstractmethod
    async def add_client(self, new_client: NewClientData) -> Client:
        """Store a new client and return it."""
        ...

    @abstractmethod
    async def get_clients(self, client_ids: Sequence[ClientId]) -> list[Client]:
        """Retrieve client data for IDs."""
        ...

    @abstractmethod
    async def add_document(self, client_id: ClientId, new_document: NewDocumentData) -> Document:
        """Store a new document and return it."""
        ...

    @abstractmethod
    async def get_client_documents(self, client_id: ClientId, doc_ids: Sequence[DocumentId]) -> list[Document]:
        """Return documents belonging to a client."""
        ...

    @abstractmethod
    async def search_client_data(self, query: str, *, limit: int = 10) -> list[Client]:
        """Search for client data with a query."""
        ...

    @abstractmethod
    async def search_document_data(self,
                                   query: str,
                                   *,
                                   client_ids: Collection[ClientId] | None = None,
                                   limit: int = 10) -> list[Document]:
        """Search for document data with a query."""
        ...


def new_client_id() -> ClientId:
    raise NotImplementedError


def new_doc_id() -> DocumentId:
    raise NotImplementedError


class ClientDocs(NamedTuple):
    client: Client
    docs: dict[DocumentId, Document] = dict()
