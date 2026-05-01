import time

from utils.logger import get_logger
from requests import post, get
from json import dumps
from io import BytesIO
from typing import Any

logger = get_logger(__name__)

def upload_file(url: str, token: str, file_data: BytesIO, filename:str, file_type:str) -> tuple[dict, Any]:
    """ 
    Upload a file to the specified URL with the provided token.
    Args:
        url (str): The URL to which the file will be uploaded.
        token (str): The authorization token for the request.
        file_data (BytesIO):  with .name attribute set to the full filename.
        filename (str): The desired filename for the uploaded file (without extension).
        file_type (str): The file extension/type (e.g., 'pptx', 'xlsx', 'docx', 'md').
    Returns:
        tuple: On success, returns a dict with the following keys:
            - file_path_download: markdown download hyperlink
            - download_url: direct download URL
            - file_id: file ID assigned by the server
            - file_name: base filename without extension
            - file_type: file extension/type
        On error, returns a dict with the 'error' key.
    """
    # MIME type mapping
    mime_types = {
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'md': 'text/markdown',
        'pdf': 'application/pdf'
    }
    
    mime_type = mime_types.get(file_type, 'application/octet-stream')

    # Ensure the URL ends with '/api/v1/files/'
    url = f'{url}/api/v1/files/'

    # Prepare headers and files for the request
    headers = {
        'Authorization': token,
        'Accept': 'application/json'
    }
 
    # Handle file_like: assume it's a file-like object (e.g., BytesIO) with .name attribute set
    files = {'file': (f"{filename}.{file_type}", file_data, mime_type)}
    # files = {'file': file_data}

    # params for the request
    params={"process": "true", "process_in_background": "false"}

    # Make the POST request to upload the file
    response = post(url, headers=headers, files=files, params=params, timeout=60)
    # response = post(url, headers=headers, files=files, timeout=30)

    if response.status_code != 200:
       logger.error(f"=> Error uploading generated file: {response.status_code}, {response.text}")
       return {"error":{"message": f'Error uploading file: {response.status_code}, {response.text}'}}, response
    elif response.status_code == 200:

        file_data = response.json()
        file_id = file_data['id']
        logger.info(f"=> File uploaded with ID: {file_id}")

        logger.info("=> Waiting for file processing...")
        start_time = time.time()
        timeout=300  # 5 minutes timeout for processing

        while time.time() - start_time < timeout:
                status_response = get(
                    f'{url}{file_id}/process/status',
                    headers=headers
                )
                status_data = status_response.json()
                status = status_data.get('status')

                logger.info(f"=> Current file processing status: {status} file id: {file_id}")
                
                if status == 'completed':
                    logger.info(f"=> File processing completed! file id: {file_id}")
                    break
                elif status == 'failed':
                    raise Exception(f"Processing failed: {status_data.get('error')}")
                
                time.sleep(2)  # Poll every 2 seconds
        else:
            logger.error(f"=> File processing timed out. file id: {file_id}")
            raise TimeoutError("File processing timed out")

        logger.info(f"=> Generated file uploaded successfully. file id: {file_id}")
        response_path_download = f'[Download {filename}.{file_type}](/api/v1/files/{file_id}/content)'
        return {
            "file_path_download": response_path_download,
            "download_url": f"/api/v1/files/{file_id}/content",
            "file_id": file_id,
            "file_name": filename,
            "file_type": file_type,
        }, response.json()  