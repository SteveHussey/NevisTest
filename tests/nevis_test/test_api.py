"""Pytest async tests for the Nevis FastAPI application."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from nevis.api import app, holder, InstanceHolder
from nevis.models import CoreApp, NewClientData, Client, ClientId, NewDocumentData, Document, DocumentId, SearchResponse
from nevis.utils import InvalidClientError, InvalidDocumentError


class ClientDocTestCore(CoreApp):
    VALID_CLIENT_ID = ClientId("ABCD")
    # noinspection PyTypeChecker
    VALID_CLIENT = Client(id=VALID_CLIENT_ID, first_name="Alice", last_name="Cooper", email="alice@example.com")
    VALID_DOC_ID = DocumentId("EFGH")
    VALID_DOCUMENT = Document(id=VALID_DOC_ID,
                              client_id=VALID_CLIENT_ID,
                              title="Sample document",
                              content="Sample content",
                              created_at=datetime.fromisoformat("2026-01-21 12:32:47.562483Z"))
    EXPECTED_VALID_DOCUMENT = dict(id=VALID_DOC_ID,
                                   client_id=VALID_CLIENT_ID,
                                   title="Sample document",
                                   content="Sample content",
                                   created_at="2026-01-21T12:32:47.562483Z")
    TEXT_ONLY_SEARCH_RESPONSE = SearchResponse(text="Sample text")
    DATA_ONLY_SEARCH_RESPONSE = SearchResponse(data=[VALID_CLIENT, VALID_DOCUMENT])
    FULL_SEARCH_RESPONSE = SearchResponse(text="Full Sample text", data=[VALID_CLIENT, VALID_DOCUMENT])
    SEARCH_RESPONSES = {
        "Test result with text only": TEXT_ONLY_SEARCH_RESPONSE,
        "Test result with data only": DATA_ONLY_SEARCH_RESPONSE,
        "Test result with text and data": FULL_SEARCH_RESPONSE,
    }

    def add_client(self, client: NewClientData) -> Client:
        return self.VALID_CLIENT

    def get_clients(self, client_ids: Sequence[ClientId]) -> list[Client]:
        result = []
        for client_id in client_ids:
            if client_id != self.VALID_CLIENT_ID:
                raise InvalidClientError(client_id)
            result.append(self.VALID_CLIENT)
        return result

    def add_document(self, client_id: ClientId, document: NewDocumentData) -> Document:
        if client_id != self.VALID_CLIENT_ID:
            raise InvalidClientError(client_id)
        return self.VALID_DOCUMENT

    def get_client_documents(self, client_id: ClientId, doc_ids: Sequence[DocumentId]) -> list[Document]:
        if client_id != self.VALID_CLIENT_ID:
            raise InvalidClientError(client_id)
        result = []
        for doc_id in doc_ids:
            if doc_id != self.VALID_DOC_ID:
                raise InvalidDocumentError(client_id, doc_id)
            result.append(self.VALID_DOCUMENT)
        return result

    def search(self, query: str, limit: int = 10) -> SearchResponse:
        return self.SEARCH_RESPONSES[query]


@pytest.fixture(scope="module")
def tester_holder():
    return InstanceHolder(ClientDocTestCore())


@pytest.fixture(autouse=True)
def client(tester_holder):
    app.dependency_overrides[holder] = tester_holder
    yield TestClient(app)
    app.dependency_overrides = {}


class TestAddClient:
    def test_valid_client_data_success(self, client: TestClient) -> None:
        payload = dict(first_name="Alice", last_name="Cooper", email="alice@example.com")
        response = client.post("/clients", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data == ClientDocTestCore.VALID_CLIENT.model_dump()

    def test_invalid_client_data_fails(self, client: TestClient) -> None:
        payload = {"name": "Alice", "email": "alice@example.com"}
        response = client.post("/clients", json=payload)
        assert response.status_code == 422


class TestGetClient:
    def test_valid_client_returned(self, client: TestClient) -> None:
        response = client.get("/clients", params={"id": ClientDocTestCore.VALID_CLIENT_ID})
        assert response.status_code == 200
        data = response.json()
        assert data == [ClientDocTestCore.VALID_CLIENT.model_dump()]

    def test_multi_valid_client_returned(self, client: TestClient) -> None:
        response = client.get("/clients",
                                    params={"id": [ClientDocTestCore.VALID_CLIENT_ID,
                                                   ClientDocTestCore.VALID_CLIENT_ID]})
        assert response.status_code == 200
        data = response.json()
        assert data == [ClientDocTestCore.VALID_CLIENT.model_dump(),
                        ClientDocTestCore.VALID_CLIENT.model_dump()]

    def test_invalid_client_id_fails(self, client: TestClient) -> None:
        response = client.get("/clients", params={"id": "BLAH"})
        assert response.status_code == 400


class TestAddDocument:
    def test_valid_document_added_success(self, client: TestClient) -> None:
        doc_payload = {"title": "Test Doc", "content": "Sample content"}
        doc_resp = client.post(
            f"/clients/{ClientDocTestCore.VALID_CLIENT_ID}/documents", json=doc_payload
        )
        assert doc_resp.status_code == 201
        doc_data = doc_resp.json()
        assert doc_data == ClientDocTestCore.EXPECTED_VALID_DOCUMENT

    def test_invalid_client_id_fails(self, client: TestClient) -> None:
        doc_payload = {"title": "Test Doc", "content": "Sample content"}
        doc_resp = client.post(
            f"/clients/BLAH/documents", json=doc_payload
        )
        assert doc_resp.status_code == 400

    def test_invalid_document_fails(self, client: TestClient) -> None:
        doc_payload = {"title": "Test Doc"}
        doc_resp = client.post(
            f"/clients/{ClientDocTestCore.VALID_CLIENT_ID}/documents", json=doc_payload
        )
        assert doc_resp.status_code == 422


class TestGetDocument:
    def test_valid_document_returned(self, client: TestClient) -> None:
        doc_resp = client.get(
            f"/clients/{ClientDocTestCore.VALID_CLIENT_ID}/documents", params={"id": ClientDocTestCore.VALID_DOC_ID}
        )
        assert doc_resp.status_code == 200
        doc_data = doc_resp.json()
        assert doc_data == [ClientDocTestCore.EXPECTED_VALID_DOCUMENT]

    def test_multi_valid_document_returned(self, client: TestClient) -> None:
        doc_resp = client.get(
            f"/clients/{ClientDocTestCore.VALID_CLIENT_ID}/documents",
            params={"id": [ClientDocTestCore.VALID_DOC_ID, ClientDocTestCore.VALID_DOC_ID]}
        )
        assert doc_resp.status_code == 200
        doc_data = doc_resp.json()
        assert doc_data == [ClientDocTestCore.EXPECTED_VALID_DOCUMENT, ClientDocTestCore.EXPECTED_VALID_DOCUMENT]

    def test_invalid_client_id_fails(self, client: TestClient) -> None:
        doc_resp = client.get(
            f"/clients/BLAH/documents", params={"id": ClientDocTestCore.VALID_DOC_ID}
        )
        assert doc_resp.status_code == 400

    def test_invalid_document_id_fails(self, client: TestClient) -> None:
        doc_resp = client.get(
            f"/clients/{ClientDocTestCore.VALID_CLIENT_ID}/documents", params={"id": "BLAH"}
        )
        assert doc_resp.status_code == 400


class TestSearch:
    def test_text_only_response(self, client: TestClient) -> None:
        search_resp = client.get("/search", params={"q": "Test result with text only"})
        assert search_resp.status_code == 200
        results = search_resp.json()
        expected = ClientDocTestCore.TEXT_ONLY_SEARCH_RESPONSE.model_dump()
        assert results['text'] == expected['text']
        assert results['data'] == []

    def test_data_only_response(self, client: TestClient) -> None:
        search_resp = client.get("/search", params={"q": "Test result with data only"})
        assert search_resp.status_code == 200
        results = search_resp.json()
        assert results['text'] is None
        assert results['data'] == [ClientDocTestCore.VALID_CLIENT.model_dump(),
                                   ClientDocTestCore.EXPECTED_VALID_DOCUMENT]

    def test_data_and_text_response(self, client: TestClient) -> None:
        search_resp = client.get("/search", params={"q": "Test result with text and data"})
        assert search_resp.status_code == 200
        results = search_resp.json()
        expected = ClientDocTestCore.FULL_SEARCH_RESPONSE.model_dump()
        assert results['text'] == expected['text']
        assert results['data'] == [ClientDocTestCore.VALID_CLIENT.model_dump(),
                                   ClientDocTestCore.EXPECTED_VALID_DOCUMENT]
