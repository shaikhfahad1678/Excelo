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
TYPE_OCR_SEARCHABLE = "TYPE 2: OCR Searchable PDF"
TYPE_SCANNED = "TYPE 3: Scanned PDF"
TYPE_HDFC = "HDFC Bank Statement"
TYPE_INDUSIND = "IndusInd Bank Statement"
TYPE_AXIS = "Axis Bank Statement"
TYPE_ICICI = "ICICI Bank Statement"

def classify_pdf_type(pdf_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    Ultra-fast PDF classification inspecting up to first 2 pages.
    Eliminates vector path parsing overhead for instant registration.
    """
    total_pages = 0
    total_text_length = 0
    pages_with_text = 0
    full_sample_text = ""

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
                    full_sample_text += " " + clean_text

        avg_text_per_page = total_text_length / max(len(sample_pages), 1)

        # Bank Detection checks looking at top page header text to avoid narration collisions
        sample_lower = full_sample_text.lower()
        top_header_text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                top_header_text = (pdf.pages[0].extract_text(layout=False) or "")[:1000].lower()
        except:
            top_header_text = sample_lower[:1000]

        is_axis = "axis bank" in top_header_text or "statement of axis account" in top_header_text or ("tran date" in top_header_text and "particulars" in top_header_text and "init. br" in top_header_text)
        is_icici = "icici bank" in top_header_text or "statement of transactions" in top_header_text or ("transaction remarks" in top_header_text and "withdrawal" in top_header_text and "deposit" in top_header_text)
        is_indusind = "indusind" in top_header_text or "indus privilege" in top_header_text or "transaction history" in top_header_text or ("chq no/ref no" in top_header_text and "withdrawal" in top_header_text)
        is_hdfc = "hdfc0" in top_header_text or "hdfc bank" in top_header_text or "statementof account" in top_header_text or ("chq./ref.no" in top_header_text and "value dt" in top_header_text)

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

        if is_axis:
            pdf_type = TYPE_AXIS
        elif is_icici:
            pdf_type = TYPE_ICICI
        elif is_indusind:
            pdf_type = TYPE_INDUSIND
        elif is_hdfc:
            pdf_type = TYPE_HDFC
        elif pages_with_text == len(sample_pages) and avg_text_per_page > 150:
            if has_vectors or not has_large_images:
                pdf_type = TYPE_DIGITAL
            else:
                pdf_type = TYPE_OCR_SEARCHABLE
        elif pages_with_text > 0:
            pdf_type = TYPE_OCR_SEARCHABLE
        else:
            pdf_type = TYPE_SCANNED


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
