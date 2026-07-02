"""Utility for retrieving the current user ID from Open WebUI."""

from requests import get

from utils.config.logger import get_logger

logger = get_logger(__name__)


def get_user_id(url: str, token: str) -> str | None:
    """Retrieve the current session user ID from Open WebUI.

    Args:
        url: Base URL of the Open WebUI instance.
        token: Bearer token string for the Authorization header.

    Returns:
        The user ID string on success, or None on any error.
    """
    endpoint = f"{url.rstrip('/')}/api/v1/auths/"
    headers = {
        'Authorization': token,
        'Accept': 'application/json'
    }

    try:
        resp = get(endpoint, headers=headers, timeout=10)
    except Exception:
        logger.error("=> Error retrieving user id.")
        return None

    if resp.status_code != 200:
        logger.error(f"=> Error retrieving user id. Status code: {resp.status_code}")
        return None

    try:
        data = resp.json()
    except Exception:
        logger.error("=> Error retrieving user id json decoding.")
        return None

    return data.get('id') if isinstance(data, dict) else None
