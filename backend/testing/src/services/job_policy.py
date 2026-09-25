from src.services.domain_policy import domain_policy


JOB_POLICY = domain_policy("delegated_jobs")
JOB_EVENT_PERMISSIONS = {
    event: tuple(permissions) for event, permissions in JOB_POLICY["events"].items()
}
ALLOWED_JOB_EVENTS = set(JOB_EVENT_PERMISSIONS)
