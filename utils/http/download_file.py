"""Utility for downloading files from the Open WebUI server."""

from io import BytesIO

from requests import get

from utils.config.logger import get_logger

logger = get_logger(__name__)


def download_file(url: str, token: str, file_id: str) -> BytesIO:
    """Download a file from Open WebUI by file ID.

    Args:
        url: Base URL of the Open WebUI instance.
        token: Bearer token for authentication.
        file_id: ID of the file to download.

    Returns:
        BytesIO buffer containing the file content, or a dict with an 'error' key on failure.
    """
    url = f'{url}/api/v1/files/{file_id}/content'
    headers = {
        'Authorization': token,
        'Accept': 'application/json'
    }
    try:
        response = get(url, headers=headers)
    except Exception:
        logger.error("=> Error downloading file.")
        return {"error": {"message": "Error downloading the file."}}

    if response.status_code != 200:
        logger.error("=> Error downloading file.")
        return {"error": {"message": f'Error downloading the file: {response.status_code}'}}
    else:
        return BytesIO(response._content)
