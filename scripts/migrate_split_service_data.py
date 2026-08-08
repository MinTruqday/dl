import os

from pymongo import MongoClient, UpdateOne


COLLECTIONS = {
    "COLLABORATION_DB_NAME": (
        "collaboration_access_requests",
        "collaboration_activities",
        "collaboration_drafts",
        "collaboration_invite_codes",
        "collaboration_invites",
        "collaboration_locks",
        "collaboration_memos",
        "collaboration_share_links",
        "collaboration_status",
        "collaboration_task_comments",
        "collaboration_tasks",
    ),
    "ENGAGEMENT_DB_NAME": (
        "bookmark_folders",
        "highlights",
        "reading_history",
        "reading_lists",
        "user_content_profiles",
        "user_pins",
    ),
}


def main():
    client = MongoClient(os.environ["MONGODB_URI"])
    source = client[os.environ["CONTENT_DB_NAME"]]
    migrated = 0
    for target_key, collections in COLLECTIONS.items():
        target = client[os.environ[target_key]]
        for collection_name in collections:
            batch = []
            for document in source[collection_name].find({}):
                document_id = document.pop("_id")
                batch.append(
                    UpdateOne(
                        {"_id": document_id},
                        {"$setOnInsert": document},
                        upsert=True,
                    )
                )
                if len(batch) == 500:
                    result = target[collection_name].bulk_write(batch, ordered=False)
                    migrated += result.upserted_count
                    batch = []
            if batch:
                result = target[collection_name].bulk_write(batch, ordered=False)
                migrated += result.upserted_count
    client.close()
    print(f"migrated_records={migrated}")


if __name__ == "__main__":
    main()
