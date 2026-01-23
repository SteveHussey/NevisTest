import re
from itertools import islice

from nevis.utils import id_generator


def test_id_generator_length_and_charset():
    gen = id_generator(length=4)
    # Generate multiple IDs and check properties
    ids = tuple(islice(gen, 5))
    for id_val in ids:
        assert isinstance(id_val, str)
        assert len(id_val) == 4
        # alphanumeric only
        assert re.fullmatch(r"[A-Za-z0-9]{4}", id_val)
    # Ensure successive calls produce different values (very low chance of collision) 4 in 62^4 (~14.8 million)
    assert len(set(ids)) == len(ids)

    assert len(next(id_generator(length=8))) == 8
