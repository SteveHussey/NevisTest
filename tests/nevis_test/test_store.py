from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from qdrant_client import AsyncQdrantClient

from nevis.models import NewClientData, NewDocumentData, Client, Document, DocumentId, ClientId
from nevis.store import QdrantStore
from nevis.utils import InvalidDocumentError, InvalidClientError


@pytest_asyncio.fixture(autouse=True)
async def qdrant_client() -> AsyncGenerator[AsyncQdrantClient, None]:
    qdrant = None
    try:
        qdrant = AsyncQdrantClient(":memory:")
        yield qdrant
    finally:
        if qdrant:
            await qdrant.close()


@pytest_asyncio.fixture()
async def ds(qdrant_client):
    store = QdrantStore(qdrant_client, "BAAI/bge-small-en")
    await store.setup_qdrant()
    return store


CLIENT1 = NewClientData(
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    description="Test client",
    social_links=["https://example.com"]
)
CLIENT2 = NewClientData(
    first_name="Alice",
    last_name="Smith",
    email="alice@example.com",
    description=None,
    social_links=[]
)


@pytest.mark.asyncio
async def test_add_and_get_client(ds: QdrantStore):
    client_obj: Client = await ds.add_client(CLIENT1)
    assert isinstance(client_obj, Client)
    for field in ["first_name", "last_name", "email", "description", "social_links"]:
        assert getattr(client_obj, field) == getattr(CLIENT1, field)
    fetched = await ds.get_clients([client_obj.id])
    assert len(fetched) == 1
    fetched_client = fetched[0]
    assert fetched_client.id == client_obj.id
    assert fetched_client.first_name == "John"

    with pytest.raises(InvalidClientError):
        await ds.get_clients([ClientId("a")])

    with pytest.raises(InvalidClientError):
        await ds.get_clients([client_obj.id, ClientId("a")])


@pytest.mark.asyncio
async def test_add_and_get_document(ds: QdrantStore):
    new_doc = NewDocumentData(title="Doc Title", content="Some content")

    client_obj = await ds.add_client(CLIENT2)
    doc_obj: Document = await ds.add_document(client_obj.id, new_doc)
    assert isinstance(doc_obj, Document)
    assert doc_obj.title == "Doc Title"

    fetched_docs = await ds.get_client_documents(client_obj.id, [doc_obj.id])
    assert len(fetched_docs) == 1
    fetched_doc = fetched_docs[0]
    assert fetched_doc.id == doc_obj.id
    assert fetched_doc.client_id == client_obj.id
    assert fetched_doc.title == "Doc Title"

    with pytest.raises(InvalidDocumentError):
        await ds.get_client_documents(client_obj.id, [DocumentId("a")])

    with pytest.raises(InvalidDocumentError):
        await ds.get_client_documents(client_obj.id, [doc_obj.id, DocumentId("a")])


@pytest.mark.asyncio
async def test_add_and_search_clients(ds: QdrantStore):
    client_obj1: Client = await ds.add_client(CLIENT1)
    assert isinstance(client_obj1, Client)
    client_obj2: Client = await ds.add_client(CLIENT2)
    assert isinstance(client_obj2, Client)

    fetched = await ds.search_client_data("Clients called John", limit=1)
    assert len(fetched) == 1
    assert all(isinstance(c, Client) for c in fetched)
    assert fetched[0].first_name == "John"

    fetched = await ds.search_client_data("Clients called Alice", limit=2)
    assert len(fetched) == 2
    assert all(isinstance(c, Client) for c in fetched)
    assert fetched[0].first_name == "Alice"
    assert fetched[1].first_name == "John"


@pytest.mark.asyncio
async def test_add_and_search_documents(ds: QdrantStore):
    # Add clients
    client_obj1: Client = await ds.add_client(CLIENT1)
    assert isinstance(client_obj1, Client)
    client_obj2: Client = await ds.add_client(CLIENT2)
    assert isinstance(client_obj2, Client)

    # Add documents
    new_doc1 = NewDocumentData(title="Investment Portfolio Overview", content="John's investment portfolio includes diversified assets across equities, bonds, and alternatives. Detailed performance metrics are provided for each asset class.")
    doc_obj1_1: Document = await ds.add_document(client_obj1.id, new_doc1)
    assert isinstance(doc_obj1_1, Document)
    new_doc2 = NewDocumentData(title="Retirement Plan Summary", content="Blah retirement plan outlines contributions, projected growth, and withdrawal strategies for the client.")
    doc_obj1_2: Document = await ds.add_document(client_obj1.id, new_doc2)
    assert isinstance(doc_obj1_2, Document)
    new_doc3 = NewDocumentData(title="Tax Optimization Report", content="Foo tax optimization report details deductions, credits, and investment structures to minimize liability.")
    doc_obj1_3: Document = await ds.add_document(client_obj1.id, new_doc3)
    assert isinstance(doc_obj1_3, Document)
    new_doc4 = NewDocumentData(title="Estate Planning Overview", content="Comprehensive estate planning document covering wills, trusts, power of attorney, and tax implications for high net-worth individuals.")
    doc_obj2_1: Document = await ds.add_document(client_obj2.id, new_doc4)
    assert isinstance(doc_obj2_1, Document)
    new_doc5 = NewDocumentData(title="Wealth Management Strategy", content="Detailed wealth management strategy including asset allocation, risk assessment, portfolio rebalancing guidelines, and performance benchmarks.")
    doc_obj2_2: Document = await ds.add_document(client_obj2.id, new_doc5)
    assert isinstance(doc_obj2_2, Document)
    new_doc6 = NewDocumentData(title="Retirement Income Planning", content="Retirement income planning document outlining withdrawal strategies, annuity options, tax-efficient distributions, and longevity risk management.")
    doc_obj2_3: Document = await ds.add_document(client_obj2.id, new_doc6)
    assert isinstance(doc_obj2_3, Document)

    fetched = await ds.search_document_data("overview documents", limit=3)
    assert len(fetched) == 3
    assert all(isinstance(d, Document) for d in fetched)
    assert fetched[0].content.startswith("Comprehensive estate planning")
    assert fetched[1].content.startswith("Foo tax optimization")
    assert fetched[2].content.startswith("Retirement income planning")

    fetched = await ds.search_document_data("retirement planning documents", client_ids=[client_obj2.id], limit=2)
    assert len(fetched) == 2
    assert all(isinstance(d, Document) for d in fetched)
    assert all(d.client_id == client_obj2.id for d in fetched)
    assert fetched[0].content.startswith("Retirement income planning")
    assert fetched[1].content.startswith("Comprehensive estate planning")
