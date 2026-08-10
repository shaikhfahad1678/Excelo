"""
PDF Type Classifier Module
Classifies PDF bank statements into 3 categories:
- TYPE 1: Native Digital PDF (selectable text objects, clean grid structure)
- TYPE 2: OCR Searchable PDF (images with background/invisible OCR layer)
- TYPE 3: Scanned PDF (image only, zero selectable text)
"""
from typing import Tuple, Dict, Any
import pdfplumber
from backend.utils.logger import logger

TYPE_DIGITAL = "TYPE 1: Native Digital PDF"
TYPE_UNSUPPORTED = "Unsupported PDF Type (Scanned/Image)"

def classify_pdf_type(pdf_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    Ultra-fast PDF classification inspecting up to first 2 pages.
    Eliminates vector path parsing overhead for instant registration.
    """
    total_pages = 0
    total_text_length = 0
    pages_with_text = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            sample_pages = pdf.pages[:2] # Ultra-fast 2-page sampling
            for page in sample_pages:
                text = page.extract_text(layout=False) or ""
                clean_text = text.strip()
                if len(clean_text) > 50:
                    pages_with_text += 1
                    total_text_length += len(clean_text)

        avg_text_per_page = total_text_length / max(len(sample_pages), 1)

        # Classification Heuristics
        # Native Digital PDFs typically have text AND vector elements (lines/rectangles).
        # OCR Searchable PDFs typically have text but NO vector lines (just large images).
        
        has_vectors = False
        has_large_images = False
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages[:2]:
                    if len(page.lines) > 5 or len(page.rects) > 5:
                        has_vectors = True
                    if len(page.images) > 0:
                        has_large_images = True
        except:
            pass

        if pages_with_text > 0 and avg_text_per_page > 50:
            pdf_type = TYPE_DIGITAL
        else:
            pdf_type = TYPE_UNSUPPORTED


        metadata = {
            "total_pages": total_pages,
            "pages_with_text": pages_with_text,
            "avg_text_per_page": round(avg_text_per_page, 1),
            "pdf_type": pdf_type
        }

        logger.info(f"PDF Fast Classification for [{pdf_path}]: {pdf_type} (Total Pages: {total_pages}, Sample Avg Text: {round(avg_text_per_page, 1)})")
        return pdf_type, metadata

    except Exception as e:
        logger.error(f"Error classifying PDF [{pdf_path}]: {e}")
        return TYPE_DIGITAL, {
            "total_pages": 1,
            "pages_with_text": 1,
            "avg_text_per_page": 0,
            "pdf_type": TYPE_DIGITAL,
            "error": str(e)
        }
