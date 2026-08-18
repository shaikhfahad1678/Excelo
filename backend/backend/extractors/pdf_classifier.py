"""
PDF Type Classifier Module
Classifies PDF bank statements exclusively into 4 supported bank types:
- HDFC Bank Statement
- Axis Bank Statement
- ICICI Bank Statement
- IndusInd Bank Statement
"""
from typing import Tuple, Dict, Any
import pdfplumber
from backend.utils.logger import logger

TYPE_HDFC = "HDFC Bank Statement"
TYPE_AXIS = "Axis Bank Statement"
TYPE_ICICI = "ICICI Bank Statement"
TYPE_INDUSIND = "IndusInd Bank Statement"
TYPE_UNKNOWN = "Unknown PDF Type"

def classify_pdf_type(pdf_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    Ultra-fast PDF classification inspecting sample pages for supported bank statement types.
    """
    total_pages = 0
    total_text_length = 0
    pages_with_text = 0
    full_sample_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            sample_pages = pdf.pages[:2]
            for page in sample_pages:
                text = page.extract_text(layout=False) or ""
                clean_text = text.strip()
                if len(clean_text) > 50:
                    pages_with_text += 1
                    total_text_length += len(clean_text)
                    full_sample_text += " " + clean_text

        avg_text_per_page = total_text_length / max(len(sample_pages), 1)
        sample_lower = full_sample_text.lower()

        # Bank Detection heuristic checks
        is_axis = ("statement of axis account" in sample_lower) or ("axis bank" in sample_lower and "tran date" in sample_lower and "particulars" in sample_lower)
        is_icici = ("statement of transactions in saving account" in sample_lower) or ("icici bank" in sample_lower and "transaction remarks" in sample_lower)
        is_indusind = ("indusind bank" in sample_lower or "indus privilege" in sample_lower) or ("transaction history" in sample_lower and "chq no/ref no" in sample_lower and "withdrawal" in sample_lower)
        is_hdfc = ("hdfc bank" in sample_lower or "hdfc0" in sample_lower) and ("chq./ref.no" in sample_lower or "value dt" in sample_lower or "statement of account" in sample_lower)

        if is_axis:
            pdf_type = TYPE_AXIS
        elif is_icici:
            pdf_type = TYPE_ICICI
        elif is_indusind:
            pdf_type = TYPE_INDUSIND
        elif is_hdfc:
            pdf_type = TYPE_HDFC
        else:
            pdf_type = TYPE_UNKNOWN

        metadata = {
            "total_pages": total_pages,
            "pages_with_text": pages_with_text,
            "avg_text_per_page": round(avg_text_per_page, 1),
            "pdf_type": pdf_type
        }

        logger.info(f"PDF Classification for [{pdf_path}]: {pdf_type} (Total Pages: {total_pages})")
        return pdf_type, metadata

    except Exception as e:
        logger.error(f"Error classifying PDF [{pdf_path}]: {e}")
        return TYPE_UNKNOWN, {
            "total_pages": 1,
            "pages_with_text": 0,
            "avg_text_per_page": 0,
            "pdf_type": TYPE_UNKNOWN,
            "error": str(e)
        }
