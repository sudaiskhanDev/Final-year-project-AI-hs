import json


def parse_json(request):
    """
    request.body ko Python dict mein convert karta hai.
    Success: (dict, None)
    Failure: (None, error_message)
    """
    try:
        raw = request.body or b"{}"
        return json.loads(raw), None
    except json.JSONDecodeError:
        return None, "Invalid JSON body"


def require_fields(data, fields):
    """
    Check karta hai ke given fields data mein present hain aur khaali nahi.
    Missing fields: error message return
    All present:    None return
    """
    if not isinstance(data, dict):
        return "Request body must be a JSON object"

    missing = [f for f in fields if not data.get(f)]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"

    return None