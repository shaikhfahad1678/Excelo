"""
Bank Statement Candidate Extractor Module
Contains individual specialized candidate extractors for:
- Union Bank Statement
- Yes Bank Statement
- HDFC Bank Statement
- Axis Bank Statement
- ICICI Bank Statement
- IndusInd Bank Statement
"""
from typing import List, Dict, Any
from backend.utils.logger import logger

def run_union_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.extractors.union_extractor import run_union_extractor as ext
        return ext(pdf_path)
    except Exception as e:
        logger.error(f"Union Bank extractor failed: {e}")
        return []

def run_yesbank_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.extractors.yesbank_extractor import run_yesbank_extractor as ext
        return ext(pdf_path)
    except Exception as e:
        logger.error(f"Yes Bank extractor failed: {e}")
        return []

def run_hdfc_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.extractors.hdfc_extractor import extract_hdfc_pdf
        return extract_hdfc_pdf(pdf_path)
    except Exception as e:
        logger.error(f"HDFC extractor failed: {e}")
        return []

def run_indusind_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.extractors.indusind_extractor import run_indusind_extractor as ext
        return ext(pdf_path)
    except Exception as e:
        logger.error(f"IndusInd extractor failed: {e}")
        return []

def run_axis_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.extractors.axis_extractor import run_axis_extractor as ext
        return ext(pdf_path)
    except Exception as e:
        logger.error(f"Axis extractor failed: {e}")
        return []

def run_icici_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.extractors.icici_extractor import run_icici_extractor as ext
        return ext(pdf_path)
    except Exception as e:
        logger.error(f"ICICI extractor failed: {e}")
        return []
