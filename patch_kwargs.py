import glob
for filepath in glob.glob('backend/*/src/core/infrastructure/mongo.py'):
    with open(filepath, 'r') as f:
        content = f.read()
    
    content = content.replace('async def find_one(self, collection: str, query: dict, projection: dict = None):', 'async def find_one(self, collection: str, query: dict, projection: dict = None, **kwargs):')
    content = content.replace('return await self.get_db()[collection].find_one(query, projection)', 'return await self.get_db()[collection].find_one(query, projection, **kwargs)')
    
    content = content.replace('async def insert_one(self, collection: str, document: dict):', 'async def insert_one(self, collection: str, document: dict, **kwargs):')
    content = content.replace('return await self.get_db()[collection].insert_one(document)', 'return await self.get_db()[collection].insert_one(document, **kwargs)')
    
    content = content.replace('async def update_one(self, collection: str, query: dict, update: dict):', 'async def update_one(self, collection: str, query: dict, update: dict, **kwargs):')
    content = content.replace('return await self.get_db()[collection].update_one(query, update)', 'return await self.get_db()[collection].update_one(query, update, **kwargs)')
    
    with open(filepath, 'w') as f:
        f.write(content)
