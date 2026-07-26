import asyncio
import os

import aioboto3
from motor.motor_asyncio import AsyncIOMotorClient


MAPPINGS = {
    "books/ctan/": "system/collection/ctan/packages/",
    "documents/ctan/": "system/collection/ctan/documents/",
    "documents/anna_archive/": "system/collection/anna_archive/",
    "documents/nxbst/": "system/collection/nxbst/",
    "documents/nxbgd/": "system/collection/nxbgd/",
}


async def main():
    source_bucket = os.environ["MINIO_PUBLIC_BUCKET"]
    target_bucket = os.environ["MINIO_PRIVATE_BUCKET"]
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    documents = mongo[os.getenv("CONTENT_DB_NAME", "doclib_content")].documents
    moved = []
    updated = 0
    try:
        async with aioboto3.Session().client(
            "s3",
            endpoint_url=os.environ["MINIO_ENDPOINT"],
            aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
            aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
        ) as storage:
            continuation = None
            while True:
                params = {"Bucket": source_bucket}
                if continuation:
                    params["ContinuationToken"] = continuation
                result = await storage.list_objects_v2(**params)
                for entry in result.get("Contents", []):
                    old_key = entry["Key"]
                    prefix = next((value for value in MAPPINGS if old_key.startswith(value)), None)
                    if not prefix:
                        continue
                    new_key = MAPPINGS[prefix] + old_key[len(prefix):]
                    await storage.copy_object(
                        Bucket=target_bucket,
                        Key=new_key,
                        CopySource={"Bucket": source_bucket, "Key": old_key},
                    )
                    metadata = await storage.head_object(Bucket=target_bucket, Key=new_key)
                    if metadata["ContentLength"] != entry["Size"]:
                        raise RuntimeError(f"Size verification failed for {old_key}")
                    moved.append((old_key, new_key, entry["Size"]))
                if not result.get("IsTruncated"):
                    break
                continuation = result["NextContinuationToken"]
            public_url = os.getenv("MINIO_PUBLIC_URL", "").rstrip("/")
            endpoint = os.environ["MINIO_ENDPOINT"].rstrip("/")
            for old_key, new_key, _ in moved:
                old_values = [
                    old_key,
                    f"{public_url}/{source_bucket}/{old_key}",
                    f"{endpoint}/{source_bucket}/{old_key}",
                ]
                for field in ["file_url", "pdf_url", "markdown_url"]:
                    result = await documents.update_many(
                        {field: {"$in": old_values}},
                        {"$set": {field: new_key}},
                    )
                    updated += result.modified_count
            for old_key, _, _ in moved:
                await storage.delete_object(Bucket=source_bucket, Key=old_key)
        print(
            {
                "migrated_objects": len(moved),
                "migrated_bytes": sum(entry[2] for entry in moved),
                "updated_metadata_fields": updated,
            }
        )
    finally:
        mongo.close()


asyncio.run(main())
