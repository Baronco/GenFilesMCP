from PIL import Image
from utils.config.logger import get_logger

logger = get_logger(__name__)

def img_dimensions(img, body_columns = 1) -> tuple:
    """
    Calculate image dimensions (width, height) in inches based on the image's aspect ratio
    and the number of columns in the document body.

    Args:
        img (str or file-like object): Path to the image file or a file-like object.
        body_columns (int): Number of columns in the document body (1 or 2). Default is 1.

    Returns:
        tuple: A tuple containing the width and height in inches.
    """
    img = Image.open(img)
    img_width, img_height = img.size
    aspect_ratio = img_width / img_height

    if aspect_ratio >= 1:
        logger.info("=> DOCX: The image is landscape")
    else:
        logger.info("=> DOCX: The image is portrait")

    if body_columns == 1:
        width = 4.0
        height = width / aspect_ratio
    elif body_columns == 2:
        width = 2.5
        height = width / aspect_ratio

    logger.info(f"=> DOCX: Image dimensions set to width={round(width, 2)} inches, height={round(height, 2)} inches for {body_columns} column(s)")

    return width, height