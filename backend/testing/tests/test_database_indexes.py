import pytest

from src.core.database import ensure_partial_unique_index


class Cursor:
    def __init__(self, values):
        self.values = values

    async def to_list(self, length):
        return self.values[:length]


class Collection:
    name = "bulk_operations"

    def __init__(self, indexes, duplicates=None):
        self.indexes = indexes
        self.duplicates = duplicates or []
        self.pipeline = None
        self.dropped = []
        self.created = []

    def list_indexes(self):
        return Cursor(self.indexes)

    def aggregate(self, pipeline):
        self.pipeline = pipeline
        return Cursor(self.duplicates)

    async def drop_index(self, name):
        self.dropped.append(name)

    async def create_index(self, keys, **options):
        self.created.append((keys, options))
        return "partial_unique"


@pytest.mark.asyncio
async def test_partial_unique_index_replaces_sparse_compound_index():
    keys = [("project_id", 1), ("idempotency_key", 1)]
    partial_filter = {"idempotency_key": {"$type": "string"}}
    collection = Collection(
        [
            {
                "name": "project_id_1_idempotency_key_1",
                "key": dict(keys),
                "unique": True,
                "sparse": True,
            }
        ]
    )

    name = await ensure_partial_unique_index(collection, keys, partial_filter)

    assert name == "partial_unique"
    assert collection.dropped == ["project_id_1_idempotency_key_1"]
    assert collection.pipeline[0] == {"$match": partial_filter}
    assert collection.created == [
        (
            keys,
            {
                "unique": True,
                "partialFilterExpression": partial_filter,
            },
        )
    ]


@pytest.mark.asyncio
async def test_partial_unique_index_keeps_matching_index():
    keys = [("project_id", 1), ("idempotency_key", 1)]
    partial_filter = {"idempotency_key": {"$type": "string"}}
    collection = Collection(
        [
            {
                "name": "partial_unique",
                "key": dict(keys),
                "unique": True,
                "partialFilterExpression": partial_filter,
            }
        ]
    )

    name = await ensure_partial_unique_index(collection, keys, partial_filter)

    assert name == "partial_unique"
    assert collection.dropped == []
    assert collection.created == []


@pytest.mark.asyncio
async def test_partial_unique_index_rejects_matching_duplicates_before_drop():
    keys = [("project_id", 1), ("idempotency_key", 1)]
    partial_filter = {"idempotency_key": {"$type": "string"}}
    collection = Collection(
        [{"name": "legacy", "key": dict(keys)}],
        duplicates=[{"_id": {"project_id": "PRJ-1", "idempotency_key": "same"}, "count": 2}],
    )

    with pytest.raises(RuntimeError):
        await ensure_partial_unique_index(collection, keys, partial_filter)

    assert collection.dropped == []
    assert collection.created == []
