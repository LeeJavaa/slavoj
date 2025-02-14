from typing import Optional

import pypdf
from pypdf.errors import PdfReadError

from slavoj.core.logging import LoggerFactory

logger = LoggerFactory.create_logger("PDFUtils")


def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extract text content from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text content or None if extraction fails
    """
    try:
        with open(file_path, 'rb') as file:
            # Create PDF reader object
            reader = pypdf.PdfReader(file)

            # Extract text from all pages
            text = []
            for page in reader.pages:
                text.append(page.extract_text())

            return '\n'.join(text)

    except PdfReadError as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing PDF {file_path}: {e}")
        return None