from nevis.models import ClientId, DocumentId


class NevisException(Exception):
    """ Base exception for any Nevis exceptions """
    ...


class InvalidClientError(NevisException):
    """ Exception raised when trying to access a non-existent client """

    def __init__(self, client_id: ClientId):
        self.client_id = client_id


class InvalidDocumentError(NevisException):
    """ Exception raised when trying to access a non-existent document """

    def __init__(self, client_id: ClientId, document_id: DocumentId):
        self.client_id = client_id
        self.document_id = document_id
