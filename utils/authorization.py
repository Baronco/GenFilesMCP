from utils.logger import get_logger

logger = get_logger(__name__)

def _get_bearer_token(request, chat_headers=False):
    """Safely retrieve the Authorization header from the request.

    Returns the header value as a string, or None if not present.
    """
    try:
        headers = request.get("headers")

        if isinstance(headers, str):
            return headers.strip() or None

        if isinstance(headers, dict):
            auth_header = headers.get("authorization") or headers.get("Authorization")
            if isinstance(auth_header, str) and not chat_headers:
                return auth_header.strip() or None
            
            if chat_headers:
                # For chat headers, we might want to return the entire headers dict
                return headers
    except Exception:
        # Log unexpected errors with stack trace for debugging.
        logger.exception("=> Unexpected error retrieving authorization header")

    return None 