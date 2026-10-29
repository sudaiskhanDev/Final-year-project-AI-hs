from django.http import JsonResponse


def success_response(data=None, message="Success", status=200):
    """
    Standard success JSON response.
    Shape: { success: True, message: str, data: any }
    """
    return JsonResponse(
        {
            "success": True,
            "message": message,
            "data": data,
        },
        status=status,
        safe=False,
    )


def error_response(message="Something went wrong", status=400, errors=None):
    """
    Standard error JSON response.
    Shape: { success: False, message: str, errors: any }
    """
    return JsonResponse(
        {
            "success": False,
            "message": message,
            "errors": errors,
        },
        status=status,
    )