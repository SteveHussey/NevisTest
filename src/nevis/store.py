import logging
from collections.abc import Generator
from typing import Collection, Sequence
from uuid import uuid4, UUID

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.models import UpdateStatus, PayloadSchemaType

from nevis.models import DataStore, ClientId, Document, Client, DocumentId, NewDocumentData, NewClientData
from nevis.utils import id_generator, InvalidClientError, InvalidDocumentError

LOGGER = logging.getLogger(__name__)


class QdrantStore(DataStore):
    CLIENT_COLLECTION = "clients"
    DOCUMENT_COLLECTION = "documents"

    CLIENT_ID_GEN = id_generator(4)
    DOC_ID_GEN = id_generator(6)

    CLIENT_ID_FIELD = "id"
    DOC_ID_FIELD = "id"
    COLL_ID_FIELDS = {
        CLIENT_COLLECTION: CLIENT_ID_FIELD,
        DOCUMENT_COLLECTION: DOC_ID_FIELD,
    }
    DOC_CLIENT_ID_FIELD = "client_id"
    CLIENT_EMBED_FIELDS = frozenset(['first_name', 'last_name', 'email', 'description', 'social_links'])
    DOC_EMBED_FIELDS = frozenset(['title', 'content'])

    def __init__(self, qdrant_client: AsyncQdrantClient, embedding_model: str):
        self.client = qdrant_client
        self.embed_model = embedding_model

    async def setup_qdrant(self):
        if not await self.client.collection_exists(self.CLIENT_COLLECTION):
            await self.client.create_collection(
                collection_name=self.CLIENT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=self.client.get_embedding_size(self.embed_model),
                    distance=models.Distance.COSINE
                ),  # size and distance are model dependent
            )

            await self.client.create_payload_index(
                collection_name=self.CLIENT_COLLECTION,
                field_name=self.CLIENT_ID_FIELD,
                field_schema=PayloadSchemaType.KEYWORD,
            )
            LOGGER.info('Created Qdrant collection: %s', self.CLIENT_COLLECTION)

        if not await self.client.collection_exists(self.DOCUMENT_COLLECTION):
            await self.client.create_collection(
                collection_name=self.DOCUMENT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=self.client.get_embedding_size(self.embed_model),
                    distance=models.Distance.COSINE
                ),  # size and distance are model dependent
            )

            await self.client.create_payload_index(
                collection_name=self.DOCUMENT_COLLECTION,
                field_name=self.DOC_ID_FIELD,
                field_schema=PayloadSchemaType.KEYWORD,
            )
            await self.client.create_payload_index(
                collection_name=self.DOCUMENT_COLLECTION,
                field_name=self.DOC_CLIENT_ID_FIELD,
                field_schema=PayloadSchemaType.KEYWORD,
            )
            LOGGER.info('Created Qdrant collection: %s', self.DOCUMENT_COLLECTION)

    async def _get_new_object_id(self, id_gen: Generator[str], coll_name: str) -> str:
        while True:
            new_id = next(id_gen)
            if not await self._id_exists(new_id, coll_name):
                return new_id

    async def _id_exists(self, id_str: str, coll_name: str) -> bool:
        id_field = self.COLL_ID_FIELDS[coll_name]
        points, _ = await self.client.scroll(
            collection_name=coll_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key=id_field,
                        match=models.MatchValue(value=id_str),
                    ),
                ]
            ),
            with_payload=False,
            with_vectors=False,
        )
        return True if points else False

    async def _get_new_point_id(self, coll_name: str) -> UUID:
        while True:
            new_uuid = uuid4()
            points = await self.client.retrieve(
                collection_name=coll_name,
                ids=[new_uuid],
                with_payload=False,
                with_vectors=False,
            )

            if not points:
                return new_uuid

    async def add_client(self, new_client: NewClientData) -> Client:
        new_id = ClientId(await self._get_new_object_id(self.CLIENT_ID_GEN, self.CLIENT_COLLECTION))
        client = Client(id=new_id, **new_client.model_dump())
        new_uuid = await self._get_new_point_id(self.CLIENT_COLLECTION)

        # noinspection PyTypeChecker
        result = await self.client.upsert(
            collection_name=self.CLIENT_COLLECTION,
            points=[
                models.PointStruct(
                    id=new_uuid,
                    payload=client.model_dump(),
                    vector=models.Document(text=client.model_dump_json(include=self.CLIENT_EMBED_FIELDS),
                                           model=self.embed_model),
                )],
        )
        if result.status is not UpdateStatus.COMPLETED:
            raise Exception('Failed to write client to Qdrant: ')
        return client

    async def get_clients(self, client_ids: Sequence[ClientId]) -> list[Client]:
        points, _ = await self.client.scroll(
            collection_name=self.CLIENT_COLLECTION,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key=self.CLIENT_ID_FIELD,
                        match=models.MatchAny(any=list(client_ids)),
                    ),
                ]
            ),
            with_payload=True,
            with_vectors=False,
        )
        client_map = {p.payload[self.CLIENT_ID_FIELD]: Client(**p.payload) for p in points}
        clients = []
        for client_id in client_ids:
            try:
                clients.append(client_map[client_id])
            except KeyError:
                 raise InvalidClientError(client_id)
        return clients

    async def add_document(self, client_id: ClientId, new_document: NewDocumentData) -> Document:
        if not await self._id_exists(client_id, self.CLIENT_COLLECTION):
            raise InvalidClientError(client_id)

        new_id = DocumentId(await self._get_new_object_id(self.DOC_ID_GEN, self.DOCUMENT_COLLECTION))
        doc = Document(id=new_id, client_id=client_id, **new_document.model_dump())

        new_uuid = await self._get_new_point_id(self.DOCUMENT_COLLECTION)
        # noinspection PyTypeChecker
        result = await self.client.upsert(
            collection_name=self.DOCUMENT_COLLECTION,
            points=[
                models.PointStruct(
                    id=new_uuid,
                    payload=doc.model_dump(),
                    vector=models.Document(text=doc.model_dump_json(include=self.DOC_EMBED_FIELDS),
                                           model=self.embed_model),
                )],
        )
        if result.status is not UpdateStatus.COMPLETED:
            raise Exception('Failed to write document to Qdrant: ')
        return doc

    async def get_client_documents(self, client_id: ClientId, doc_ids: Sequence[DocumentId]) -> list[Document]:
        points, _ = await self.client.scroll(
            collection_name=self.DOCUMENT_COLLECTION,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key=self.DOC_CLIENT_ID_FIELD,
                        match=models.MatchValue(value=client_id),
                    ),
                    models.FieldCondition(
                        key=self.CLIENT_ID_FIELD,
                        match=models.MatchAny(any=list(doc_ids)),
                    ),
                ]
            ),
            with_payload=True,
            with_vectors=False,
        )
        doc_map = {p.payload[self.DOC_ID_FIELD]: Document(**p.payload) for p in points}
        docs = []
        for doc_id in doc_ids:
            try:
                docs.append(doc_map[doc_id])
            except KeyError:
                 raise InvalidDocumentError(client_id, doc_id)
        return docs

    async def search_client_data(self, query: str, *, limit: int = 10) -> list[Client]:
        result = await self.client.query_points(
            collection_name=self.CLIENT_COLLECTION,
            query=models.Document(text=query, model=self.embed_model),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return [Client(**p.payload) for p in result.points]

    async def search_document_data(self, query: str, *,
                                   client_ids: Collection[ClientId] | None = None,
                                   limit: int = 10) -> list[Document]:
        if client_ids:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(key=self.DOC_CLIENT_ID_FIELD, match=models.MatchAny(any=list(client_ids))),
                ]
            )
        else:
            query_filter = None

        result = await self.client.query_points(
            collection_name=self.DOCUMENT_COLLECTION,
            query=models.Document(text=query, model=self.embed_model),
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return [Document(**p.payload) for p in result.points]
