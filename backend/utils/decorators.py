from functools import wraps
from utils.response import error_response


def login_required_json(view_func):
    """
    Check karta hai ke user logged-in hai.
    Nahi hai to 401 JSON response.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error_response(
                "Authentication required. Please login.",
                status=401,
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required_json(view_func):
    """
    Check karta hai ke user logged-in hai AUR admin hai.
    - Login nahi → 401
    - Login hai but admin nahi → 403
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error_response(
                "Authentication required. Please login.",
                status=401,
            )

        user = request.user
        is_admin = (
            user.role == "admin"
            or user.is_superuser
            or user.is_staff
        )
        if not is_admin:
            return error_response(
                "Admin access required. You don't have permission.",
                status=403,
            )

        return view_func(request, *args, **kwargs)
    return wrapper