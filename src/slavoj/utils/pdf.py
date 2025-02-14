from pathlib import Path
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
            total_pages = len(reader.pages)
            logger.info(
                f"Beginning extraction of {total_pages} pages from {file_path}")

            for i, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    text.append(page_text)

                    # Log progress
                    if i % 10 == 0 or i == total_pages:  # Log every 10 pages and the final page
                        logger.info(
                            f"Processed page {i}/{total_pages} ({(i / total_pages) * 100:.1f}%) of {Path(file_path).name}")

                    # Log warning if page text is suspiciously short
                    if len(page_text.strip()) < 100:
                        logger.warning(
                            f"Page {i} in {Path(file_path).name} has unusually short content ({len(page_text)} chars)")

                except Exception as e:
                    logger.error(
                        f"Error extracting text from page {i} in {Path(file_path).name}: {e}")
                    # Continue with next page rather than failing entirely
                    continue

            total_chars = sum(len(t) for t in text)
            logger.info(
                f"Completed extraction of {file_path}: {total_pages} pages, {total_chars} characters")

            return '\n'.join(text)

    except PdfReadError as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing PDF {file_path}: {e}")
        return None