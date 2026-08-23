from motor.motor_asyncio import AsyncIOMotorClient

from src.core.configuration import settings


class Database:
    client: AsyncIOMotorClient | None = None

    @property
    def value(self):
        if self.client is None:
            raise RuntimeError("Cơ sở dữ liệu chưa sẵn sàng")
        return self.client[settings.ASSESSMENT_DB_NAME]


database = Database()


async def connect_database():
    database.client = AsyncIOMotorClient(settings.MONGODB_URI)
    await database.client.admin.command("ping")
    await create_indexes()


async def close_database():
    if database.client is not None:
        database.client.close()
        database.client = None


async def create_indexes():
    db = database.value
    await db.assessment_drafts.create_index([("owner_id", 1), ("updated_at", -1)])
    await db.question_drafts.create_index([("assessment_draft_id", 1), ("owner_id", 1)])
    await db.questions.create_index([("owner_id", 1), ("status", 1), ("updated_at", -1)])
    await db.question_versions.create_index([("question_id", 1), ("version", 1)], unique=True)
    await db.assessments.create_index([("owner_id", 1), ("assessment_draft_id", 1), ("status", 1)])
    await db.assessments.create_index([("owner_id", 1), ("updated_at", -1)])
    await db.assessment_versions.create_index([("assessment_id", 1), ("version", 1)], unique=True)
    await db.assessment_versions.create_index(
        [("assessment_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.assignments.create_index(
        [("assessment_version_id", 1), ("student_id", 1)], unique=True
    )
    await db.assignments.create_index([("student_id", 1), ("created_at", -1)])
    await db.assignment_batches.create_index([("owner_id", 1), ("idempotency_key", 1)], unique=True)
    await db.attempts.create_index(
        [("assignment_id", 1), ("student_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.attempts.create_index(
        [("student_id", 1), ("assessment_version_id", 1), ("updated_at", -1)]
    )
    await db.responses.create_index([("attempt_id", 1), ("question_version_id", 1)], unique=True)
    await db.responses.create_index([("question_version_id", 1), ("is_first_exposure", 1)])
    await db.responses.create_index([("participant_id", 1), ("question_version_id", 1)])
    await db.calibrations.create_index(
        [("question_version_id", 1), ("method", 1), ("created_at", -1)]
    )
    await db.calibration_runs.create_index(
        [("owner_id", 1), ("idempotency_key", 1)],
        unique=True,
        partialFilterExpression={"idempotency_key": {"$type": "string"}},
    )
    await db.import_jobs.create_index([("owner_id", 1), ("idempotency_key", 1)], unique=True)
    await db.generation_runs.create_index([("owner_id", 1), ("idempotency_key", 1)], unique=True)
    await db.assessment_rebalance_proposals.create_index(
        [("owner_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.assessment_rebalance_proposals.create_index(
        [("assessment_draft_id", 1), ("created_at", -1)]
    )
    await db.difficulty_estimates.create_index([("question_version_id", 1), ("created_at", -1)])
    await db.difficulty_targets.create_index([("question_version_id", 1), ("created_at", -1)])
    await db.teacher_judgments.create_index(
        [("question_version_id", 1), ("teacher_id", 1), ("created_at", -1)]
    )
    await db.audit_events.create_index([("actor_id", 1), ("created_at", -1)])
    await db.audit_events.create_index([("entity_type", 1), ("entity_id", 1), ("created_at", -1)])
    await db.education_profiles.create_index("user_id", unique=True)
    await db.teacher_profiles.create_index("user_id", unique=True)
    await db.teacher_profile_events.create_index(
        [("teacher_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.curriculum_nodes.create_index(
        [("canonical_code", 1), ("curriculum_version", 1)], unique=True
    )
    await db.source_mappings.create_index([("document_id", 1), ("chunk_id", 1)], unique=True)
    await db.source_mappings.create_index([("creator_id", 1), ("source_type", 1)])
