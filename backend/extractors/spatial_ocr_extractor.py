"""
Method 1: Spatial Bounding-Box Layout Clustering + PP-OCRv4
"""
import re
from typing import List, Dict, Any
from backend.utils.logger import logger

def extract_via_spatial_layout_ocr(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Method 1: Spatial Bounding-Box Layout Clustering + PP-OCRv4.
    Extracts transaction tables by clustering word bounding boxes vertically and aligning them horizontally.
    """
    logger.info(f"Method 1 Spatial OCR running on [{pdf_path}]...")
    from backend.ocr.engine import ocr_engine

    # 1. Attempt to run via local PaddleOCR first
    try:
        # PaddleOCR wrapper will parse visually and return sorted lines
        logger.info("Attempting local PaddleOCR engine extraction...")
        rows = ocr_engine.process_via_paddleocr(pdf_path)
        if rows:
            logger.info(f"PaddleOCR extracted {len(rows)} rows.")
            return rows
    except Exception as e:
        logger.warning(f"PaddleOCR failed/not found: {e}. Falling back to spatial Tesseract OCR.")

    # 2. Fall back to Spatial Tesseract OCR
    logger.info("Running Spatial Tesseract OCR fallback...")
    res = ocr_engine.process_scanned_pdf(pdf_path)
    rows = res.get("transactions", [])
    logger.info(f"Spatial Tesseract OCR extracted {len(rows)} rows.")
    return rows
