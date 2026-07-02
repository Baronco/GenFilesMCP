"""Utility for uploading generated files to the Open WebUI server."""

import time
from io import BytesIO
from typing import Any

from requests import get, post

from utils.config.logger import get_logger

logger = get_logger(__name__)


def upload_file(url: str, token: str, file_data: BytesIO, filename: str, file_type: str) -> tuple[dict, Any]:
    """Upload a file to Open WebUI and wait for it to be processed.

    Args:
        url: Base URL of the Open WebUI instance.
        token: Bearer token for authentication.
        file_data: File content as a seekable BytesIO buffer with a `.name` attribute.
        filename: Desired base filename without extension.
        file_type: File extension without leading dot ('docx', 'pptx', 'xlsx', 'md', 'pdf').

    Returns:
        Tuple of (response_dict, request_data_dict). On success, response_dict contains
        'file_path_download', 'download_url', 'file_id', 'file_name', and 'file_type'.
        On error, response_dict contains an 'error' key.
    """
    mime_types = {
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'md': 'text/markdown',
        'pdf': 'application/pdf'
    }

    mime_type = mime_types.get(file_type, 'application/octet-stream')
    url = f'{url}/api/v1/files/'
    headers = {
        'Authorization': token,
        'Accept': 'application/json'
    }
    files = {'file': (f"{filename}.{file_type}", file_data, mime_type)}
    params = {"process": "true", "process_in_background": "false"}

    response = post(url, headers=headers, files=files, params=params, timeout=60)

    if response.status_code != 200:
        logger.error(f"=> Error uploading generated file: {response.status_code}, {response.text}")
        return {"error": {"message": f'Error uploading file: {response.status_code}, {response.text}'}}, response

    file_data = response.json()
    file_id = file_data['id']
    logger.info(f"=> File uploaded with ID: {file_id}")
    logger.info("=> Waiting for file processing...")
    start_time = time.time()
    timeout = 300

    while time.time() - start_time < timeout:
        status_response = get(f'{url}{file_id}/process/status', headers=headers)
        status_data = status_response.json()
        status = status_data.get('status')
        logger.info(f"=> Current file processing status: {status} file id: {file_id}")
        if status == 'completed':
            logger.info(f"=> File processing completed! file id: {file_id}")
            break
        elif status == 'failed':
            raise Exception(f"Processing failed: {status_data.get('error')}")
        time.sleep(2)
    else:
        logger.error(f"=> File processing timed out. file id: {file_id}")
        raise TimeoutError("File processing timed out")

    logger.info(f"=> Generated file uploaded successfully. file id: {file_id}")
    return {
        "file_path_download": f'[Download {filename}.{file_type}](/api/v1/files/{file_id}/content)',
        "download_url": f"/api/v1/files/{file_id}/content",
        "file_id": file_id,
        "file_name": filename,
        "file_type": file_type,
    }, response.json()
