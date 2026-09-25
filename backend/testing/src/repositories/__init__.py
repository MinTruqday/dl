from src.repositories.analysis import analysis_repository
from src.repositories.analytics import analytics_repository
from src.repositories.api_artifact import api_artifact_repository
from src.repositories.bulk_operation import bulk_operation_repository
from src.repositories.cicd import cicd_repository
from src.repositories.causal_analysis import causal_analysis_repository
from src.repositories.collaboration import collaboration_repository
from src.repositories.common import common_repository
from src.repositories.defect import defect_repository
from src.repositories.execution_context import execution_context_repository
from src.repositories.execution_policy import execution_policy_repository
from src.repositories.maintenance_proposal import maintenance_proposal_repository
from src.repositories.measurement import measurement_repository
from src.repositories.execution_asset import execution_asset_repository
from src.repositories.environment_incident import environment_incident_repository
from src.repositories.internal_admin import internal_admin_repository
from src.repositories.impact_analysis import impact_analysis_repository
from src.repositories.project import project_repository
from src.repositories.project_connector import project_connector_repository
from src.repositories.project_notification import project_notification_repository
from src.repositories.process_improvement import process_improvement_repository
from src.repositories.proposal_application import proposal_application_repository
from src.repositories.quality import quality_repository
from src.repositories.non_functional_test import non_functional_test_repository
from src.repositories.operations import operations_repository
from src.repositories.review import review_repository
from src.repositories.statistical_quality import statistical_quality_repository
from src.repositories.requirement_document import requirement_document_repository
from src.repositories.requirement import requirement_repository
from src.repositories.requirement_import import requirement_import_repository
from src.repositories.regression_recommendation import regression_recommendation_repository
from src.repositories.requirement_analysis import requirement_analysis_repository
from src.repositories.requirement_ai import requirement_ai_repository
from src.repositories.test_design import test_design_repository
from src.repositories.test_analysis import test_analysis_repository
from src.repositories.test_monitoring import test_monitoring_repository
from src.repositories.test_plan import test_plan_repository
from src.repositories.test_run import test_run_repository
from src.repositories.traceability import traceability_repository
from src.repositories.webhook import webhook_repository

__all__ = [
    "analysis_repository",
    "analytics_repository",
    "api_artifact_repository",
    "bulk_operation_repository",
    "cicd_repository",
    "causal_analysis_repository",
    "collaboration_repository",
    "common_repository",
    "defect_repository",
    "execution_context_repository",
    "execution_policy_repository",
    "maintenance_proposal_repository",
    "measurement_repository",
    "execution_asset_repository",
    "environment_incident_repository",
    "internal_admin_repository",
    "impact_analysis_repository",
    "project_connector_repository",
    "project_notification_repository",
    "process_improvement_repository",
    "proposal_application_repository",
    "project_repository",
    "quality_repository",
    "non_functional_test_repository",
    "operations_repository",
    "review_repository",
    "statistical_quality_repository",
    "requirement_document_repository",
    "requirement_repository",
    "requirement_import_repository",
    "regression_recommendation_repository",
    "requirement_analysis_repository",
    "requirement_ai_repository",
    "test_design_repository",
    "test_analysis_repository",
    "test_monitoring_repository",
    "test_plan_repository",
    "test_run_repository",
    "traceability_repository",
    "webhook_repository",
]
