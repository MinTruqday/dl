import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient


async def main():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://mongodb:27017"))
    db = client[os.getenv("TESTING_DB_NAME", "testing")]
    expected = {
        "requirements": {"project_id_1_requirement_key_1"},
        "requirement_versions": {"requirement_id_1_version_1"},
        "test_cases": {"project_id_1_test_case_key_1"},
        "test_case_versions": {"test_case_id_1_version_1"},
        "data_sets": {"project_id_1_name_1"},
        "data_set_versions": {"data_set_id_1_version_1"},
        "trace_links": {"project_id_1_source_type_1_source_id_1", "project_id_1_target_type_1_target_id_1"},
        "defects": {"project_id_1_defect_key_1"},
        "test_results": {"test_run_id_1_test_case_version_id_1"},
        "maintenance_proposals": {"project_id_1_status_1"},
        "bulk_operations": {"project_id_1_created_at_-1"},
    }
    collections = set(await db.list_collection_names())
    forbidden = {"psychometrics", "difficulty_calibrations", "learner_profiles", "curricula", "student_attempts"}
    assert not collections & forbidden
    for collection, names in expected.items():
        indexes = await db[collection].index_information()
        assert names <= set(indexes), f"Missing indexes for {collection}: {names - set(indexes)}"
    client.close()
    print("qa migration audit passed")


asyncio.run(main())
