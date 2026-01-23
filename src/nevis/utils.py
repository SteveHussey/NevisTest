import string
from collections.abc import Generator
from random import Random

from nevis.models import ClientId, DocumentId


def id_generator(length: int, seed=None) -> Generator[str, None, None]:
    """Generate sequential alphanumeric IDs of a fixed length.

    Uses characters 0-9, A-Z, a-z as the base-62 alphabet.
    """
    if length <= 0:
        raise ValueError("Length must be a positive integer")

    population = string.digits + string.ascii_uppercase + string.ascii_lowercase
    rand = Random(seed)
    while True:
        yield "".join(rand.choices(population, k=length))


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


if __name__ == '__main__':
    gen = id_generator(8)
    for _ in range(10):
        print(next(gen))
