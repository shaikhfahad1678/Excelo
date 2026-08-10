"""
PDF Detector to check digital vs scanned status without OCR.
"""
from typing import Tuple, Dict, Any
import pypdf
from backend.utils.logger import logger

def detect_pdf_type(pdf_path: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Inspects PDF pages to check if text is selectable.
    Returns:
        (is_digital, message, metadata)
    """
    try:
        reader = pypdf.PdfReader(pdf_path)
        total_pages = len(reader.pages)
        if total_pages == 0:
            return False, "PDF file has no pages.", {"num_pages": 0}

        total_text_length = 0
        pages_with_text = 0

        # Sample up to first 10 pages for speed
        sample_pages = min(total_pages, 10)
        for i in range(sample_pages):
            page_text = reader.pages[i].extract_text() or ""
            text_len = len(page_text.strip())
            total_text_length += text_len
            if text_len > 20: # threshold for readable content
                pages_with_text += 1

        is_digital = pages_with_text > 0 or total_text_length > 50

        if is_digital:
            msg = f"Digital PDF verified ({total_pages} pages)."
            logger.info(f"[{pdf_path}] {msg}")
            return True, msg, {"num_pages": total_pages, "digital": True}
        else:
            msg = "This version only supports digital PDFs. Please upload a digital bank statement."
            logger.warning(f"[{pdf_path}] Scanned/Image PDF detected.")
            return False, msg, {"num_pages": total_pages, "digital": False}

    except Exception as e:
        msg = f"Unable to analyze PDF structure: {str(e)}"
        logger.error(f"[{pdf_path}] {msg}")
        return False, msg, {"num_pages": 0, "digital": False}
