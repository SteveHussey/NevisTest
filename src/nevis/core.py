from collections.abc import Sequence

from nevis.models import CoreApp, NewClientData, Client, ClientId, NewDocumentData, Document, DocumentId, \
    SearchResponse, DataStore


class ClientDocCore(CoreApp):

    def __init__(self, data_store: DataStore):
        self.data_store = data_store

    async def add_client(self, client: NewClientData) -> Client:
        return await self.data_store.add_client(client)

    async def get_clients(self, client_ids: Sequence[ClientId]) -> list[Client]:
        return await self.data_store.get_clients(client_ids)

    async def add_document(self, client_id: ClientId, document: NewDocumentData) -> Document:
        return await self.data_store.add_document(client_id, document)

    async def get_client_documents(self, client_id: ClientId, doc_ids: Sequence[DocumentId]) -> list[Document]:
        return await self.data_store.get_client_documents(client_id, doc_ids)

    async def search(self, query: str, limit: int = 10) -> SearchResponse:
        # TODO: use an actual LLM to parse the query and decide whether to fetch client and/or document data and how that is presented ack to the user
        q_comp = query.lower()
        if "document" in q_comp:
            return SearchResponse(data=await self.data_store.search_document_data(query, limit=limit))
        elif "client" in q_comp:
            return SearchResponse(data=await self.data_store.search_client_data(query, limit=limit))
        else:
            return SearchResponse(text=f"Unable to handle query of this form: {query}")