import os

files = []
for root, dirs, f in os.walk("backend"):
    if "api_client.py" in f:
        files.append(os.path.join(root, "api_client.py"))

for fpath in files:
    with open(fpath, "r") as f:
        content = f.read()

    # Remove `db: str, ` from method signatures
    content = content.replace("def find_one(self, db: str, collection: str,", "def find_one(self, collection: str,")
    content = content.replace("def find(self, db: str, collection: str,", "def find(self, collection: str,")
    content = content.replace("def insert_one(self, db: str, collection: str,", "def insert_one(self, collection: str,")
    content = content.replace("def update_one(self, db: str, collection: str,", "def update_one(self, collection: str,")
    content = content.replace("def update_many(self, db: str, collection: str,", "def update_many(self, collection: str,")
    content = content.replace("def delete_one(self, db: str, collection: str,", "def delete_one(self, collection: str,")
    content = content.replace("def delete_many(self, db: str, collection: str,", "def delete_many(self, collection: str,")
    content = content.replace("def count_documents(self, db: str, collection: str,", "def count_documents(self, collection: str,")
    content = content.replace("def aggregate(self, db: str, collection: str,", "def aggregate(self, collection: str,")

    # Hardcode "db": "doclib" in payloads
    content = content.replace('"db": db,', '"db": "doclib",')

    # Add query builder class
    qb_class = """
class QueryBuilder:
    def __init__(self, client, collection: str):
        self.client = client
        self.collection = collection
        self._query = {}
        self._sort = None
        self._skip = 0
        self._limit = 0

    def filter(self, query: dict):
        self._query = query
        return self

    def sort(self, *args):
        if len(args) == 2 and isinstance(args[0], str):
            self._sort = [args]
        else:
            self._sort = args[0]
        return self

    def skip(self, s: int):
        self._skip = s
        return self

    def limit(self, l: int):
        self._limit = l
        return self

    async def execute(self):
        return await self.client.find(self.collection, self._query, sort=self._sort, skip=self._skip, limit=self._limit)
"""
    if "class QueryBuilder" not in content:
        content = content.replace("db_client = DatabaseAPIClient()", qb_class + "\n    def query(self, collection: str):\n        return QueryBuilder(self, collection)\n\ndb_client = DatabaseAPIClient()")

    with open(fpath, "w") as f:
        f.write(content)
