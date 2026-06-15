from datetime import datetime, timezone

from core.database import db_client
from core.repositories.base_repository import RepositoryFactory
from fastapi import HTTPException
from loguru import logger


class PublicationService:

    @staticmethod
    async def update_seo_metadata(
        document_id: str, seo_data: dict, current_user, db=None
    ):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": str(document_id), "creator_id": user_id}
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        await RepositoryFactory.get("documents").update_one(
            {"_id": str(document_id)},
            {
                "$set": {
                    "seo_tags": seo_data.get("tags", []),
                    "seo_keywords": seo_data.get("keywords", []),
                    "seo_slug": seo_data.get("slug", ""),
                    "meta_description": seo_data.get("description", ""),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info(
            "The search engine optimization metadata for the specified document has been successfully modified"
        )
        return {"message": "The descriptive metadata and optimization tags have been successfully updated and applied"}

    @staticmethod
    async def get_readability_score(document_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": str(document_id)}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="The requested digital document could not be located within the primary storage repository")
        content = doc.get("content")
        if not content:
            return {"score": 0, "level": "No content available", "words": 0}
        try:
            import textstat

            score = textstat.flesch_reading_ease(content)
            grade = textstat.flesch_kincaid_grade(content)
            words = textstat.lexicon_count(content, removepunct=True)
            target = (
                "University / Expert"
                if grade > 12
                else "High School" if grade > 8 else "General Public"
            )
            return {
                "ease_score": score,
                "complexity_grade": grade,
                "target_audience": target,
                "total_words": words,
                "analysis": "Readable structure" if score > 60 else "Complex structure",
            }
        except ImportError:
            logger.error("The linguistic analysis module is currently unavailable due to a missing internal software dependency")
            return {"error": "The automated readability evaluation system is currently undergoing maintenance and is inaccessible"}
        except Exception as e:
            logger.error("The linguistic analysis engine encountered an unexpected error while processing the document structure")
            return {"error": "The system was unable to complete the linguistic analysis due to an unrecognizable content format"}

    @staticmethod
    async def schedule_publish(
        document_id: str, publish_at: str, current_user, db=None
    ):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id, "creator_id": user_id},
            {"$set": {"scheduled_publish_at": datetime.fromisoformat(publish_at)}},
        )
        logger.info(
            "An automated publication schedule has been successfully configured for the digital document"
        )
        return {"message": "The designated publication schedule has been successfully recorded and queued in the system"}

    @staticmethod
    async def publish_document(document_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        docs_collection = RepositoryFactory.get("documents")
        user_id = str(current_user.id)
        document = await docs_collection.find_one(
            {"_id": document_id, "creator_id": user_id}
        )
        if not document:
            raise HTTPException(status_code=404, detail="The requested digital document could not be located within the primary storage repository")
        from src.core.publication import trigger_document_publish_job

        await trigger_document_publish_job(document_id, user_id)
        await docs_collection.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "status": "processing_publish",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("The automated publication sequence has been initiated for the specified digital document")
        return await docs_collection.find_one({"_id": document_id})