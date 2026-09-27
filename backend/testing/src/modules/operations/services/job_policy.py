


JOB_EVENT_PERMISSIONS = {
    event: tuple(permissions) for event, permissions in {'document.parse.requested': ['requirement_document.extract'],
 'requirement.extract.requested': ['requirement_document.extract'],
 'requirement.semantic_diff.requested': ['changeset.create'],
 'test.generate.requested': ['ai.generate_testcase', 'testcase.create'],
 'duplicate.scan.requested': ['testcase.duplicate_check', 'ai.run_duplicate_check'],
 'impact.analysis.requested': ['impact.execute', 'ai.run_impact'],
 'knowledge.index.requested': ['knowledge.manage']}.items()
}
ALLOWED_JOB_EVENTS = set(JOB_EVENT_PERMISSIONS)
