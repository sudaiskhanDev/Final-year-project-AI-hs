"""
Evaluate Application Workflow.

Orchestrates:
  1. Validate application exists
  2. Delegate scoring to hiring.services.matching_service
  3. Return response dict

This is the "workflow layer" — it decides WHAT to do.
The actual scoring logic lives in hiring/services/matching_service.py.
"""

from apps.recruitment.models import Application
from apps.hiring.services.matching_service import evaluate_application as _evaluate


def evaluate_application_workflow(application_id: int) -> dict:
    """
    Full evaluate-application workflow.

    Args:
        application_id: Application PK

    Returns:
        dict with scores, verdict, matched/missing skills

    Raises:
        ValueError: for validation errors (404, 400)
    """

    # ---------- 1. Validate application exists ----------
    try:
        Application.objects.only("application_id").get(pk=application_id)
    except Application.DoesNotExist:
        raise ValueError(f"Application #{application_id} not found")

    # ---------- 2. Delegate to service ----------
    # Service handles: parse CV, compute scores, save ResumeMatching
    return _evaluate(application_id)