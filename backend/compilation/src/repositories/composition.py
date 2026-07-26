from src.core.infrastructure.mongo import mongo

class CompositionRepository:
    @classmethod
    async def update_suggestion(cls, *args, **kwargs):
        return await mongo.update_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def insert_suggestion(cls, *args, **kwargs):
        return await mongo.insert_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def find_suggestion(cls, *args, **kwargs):
        return await mongo.find_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def update_comment(cls, *args, **kwargs):
        return await mongo.update_one("editor_comments", *args, **kwargs)

    @classmethod
    async def insert_comment(cls, *args, **kwargs):
        return await mongo.insert_one("editor_comments", *args, **kwargs)

    @classmethod
    async def find_comment(cls, *args, **kwargs):
        return await mongo.find_one("editor_comments", *args, **kwargs)

    @classmethod
    def find_comments(cls, *args, **kwargs):
        return mongo.query("editor_comments").filter(*args, **kwargs)
