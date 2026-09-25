from src.core.infrastructure.mongo import mongo


class FolderRepository:
    @staticmethod
    async def find_one(*args, **kwargs):
        return await mongo.find_one("workspace_folders", *args, **kwargs)

    @staticmethod
    async def insert_one(*args, **kwargs):
        return await mongo.insert_one("workspace_folders", *args, **kwargs)

    @staticmethod
    async def delete_one(*args, **kwargs):
        return await mongo.delete_one("workspace_folders", *args, **kwargs)

    @staticmethod
    def query(*args, **kwargs):
        return mongo.query("workspace_folders", *args, **kwargs)
