import re

text = """
await db["users"].find(query).sort("created_at", -1).to_list(length=100)
await db.documents.find({"status": "published"}).sort("views", -1).limit(limit).to_list(length=10)
"""

# We want to match: db["X"] or db.X
# Then .find(Y)
# Then optionally .sort(Z), .skip(S), .limit(L)
# Then .to_list(length=W)

pattern = re.compile(r'db(?:\["(.*?)"\]|\.(.*?))\.find\((.*?)\)(?:\.sort\((.*?)\))?(?:\.skip\((.*?)\))?(?:\.limit\((.*?)\))?\.to_list\((?:length=)?(.*?)\)')

for match in pattern.finditer(text):
    col1, col2, query, sort, skip, limit, length = match.groups()
    col = col1 or col2
    print(f"Collection: {col}")
    print(f"Query: {query}")
    print(f"Sort: {sort}")
    print(f"Skip: {skip}")
    print(f"Limit: {limit or length}")
