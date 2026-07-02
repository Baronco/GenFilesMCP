from io import BytesIO
from json import dumps

from utils.config.logger import get_logger
from utils.http.authorization import _get_bearer_token
from utils.http.download_file import download_file
from utils.http.get_user_id import get_user_id
from utils.http.knowledge import create_knowledge
from utils.http.upload_file import upload_file

logger = get_logger(__name__)

def generate_pdf(python_script, file_name, images_list, request, URL, ENABLE_CREATE_KNOWLEDGE, knowledge_name):
    """
    Generate a PDF file using an AI-generated Python script.

    Returns:
        dict: Contains 'file_path_download' with a markdown hyperlink for downloading the generated PDF file.
    """
    try:
        images = []

        if len(images_list) > 0:
            logger.info(f"Received {len(images_list)} images for PDF generation.")

        for image in images_list:
            image_file = download_file(URL, _get_bearer_token(request), image)
            if isinstance(image_file, dict) and "error" in image_file:
                return {"error": {"message": f"Error downloading image with ID {image}: {image_file['error']['message']}"}}
            images.append(image_file)

        buffer = BytesIO()
        buffer.name = f'{file_name}.pdf'
        context = {"pdf_buffer": buffer, "images": images}
        try:
            exec(python_script, context)
        except Exception as exec_e:
            return {"error": {"message": f"Error executing script: {str(exec_e)}"}}

        buffer.seek(0)

        try:
            bearer_token = _get_bearer_token(request)
            logger.info("=> Received authorization header!")
        except:
            logger.error("=> Error retrieving authorization header")

        # resolve user_id from token
        user_id = get_user_id(URL, bearer_token)
        if not user_id:
            logger.error("=> Error obtaining user id from token")
            return dumps({"error": {"message": "Error obtaining user id from token"}}, indent=4, ensure_ascii=False)

        response, request_data = upload_file(
            url=URL,
            token=bearer_token,
            file_data=buffer,
            filename=file_name,
            file_type="pdf"
        )

        if "file_path_download" in response and ENABLE_CREATE_KNOWLEDGE:
            create_knowledge_status = create_knowledge(
                url=URL,
                token=bearer_token,
                file_id=request_data['id'],
                user_id=user_id,
                knowledge_name=knowledge_name
            )
            if create_knowledge_status:
                logger.info("=> Knowledge base updated successfully.")
            else:
                logger.error("=> Error creating or updating knowledge base")
        elif "error" in response:
            logger.error("=> Error uploading the file.")
        else:
            logger.info("=> Skipping knowledge creation because ENABLE_CREATE_KNOWLEDGE is false")

        return response

    except Exception as e:
        logger.error("=> An unknown error occurred during .PDF document generation.")
        return dumps(
            {
                "error": {
                    "message": str(e)
                }
            },
            indent=4,
            ensure_ascii=False
        )
