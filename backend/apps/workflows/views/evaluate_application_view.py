"""
Evaluate Application View.

POST /api/workflows/evaluate-application/<application_id>/

Response: scores + verdict + matched/missing skills
"""

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.workflows.utils.evaluate_application import evaluate_application_workflow
from utils.response import success_response, error_response


@csrf_exempt
@require_http_methods(["POST"])
def evaluate_application_view(request, application_id):
    """
    Trigger CV vs Job matching for a given application.

    Called by HR from dashboard "Evaluate" button.
    """

    try:
        result = evaluate_application_workflow(application_id=int(application_id))
    except ValueError as e:
        # Validation / not-found / file-missing errors → 400
        return error_response(str(e), status=400)
    except FileNotFoundError as e:
        # Resume file physically missing on disk
        return error_response(f"Resume file not found: {e}", status=404)
    except Exception as e:
        # Unexpected error (parser crash, etc.)
        return error_response(f"Evaluation failed: {str(e)}", status=500)

    return success_response(
        result,
        message="Application evaluated successfully",
    )