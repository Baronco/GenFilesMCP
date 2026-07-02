from utils.config.logger import get_logger

logger = get_logger(__name__)

def _get_bearer_token(request, chat_headers=False):
    """Safely retrieve the Authorization header from the request.

    Args:
        request: Dict with a 'headers' key containing the HTTP headers.
        chat_headers: If True, return the full headers dict instead of just the auth value.

    Returns:
        The Authorization header string, the full headers dict (when chat_headers=True),
        or None if not present.
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
                return headers
    except Exception:
        logger.exception("=> Unexpected error retrieving authorization header")

    return None
