"""
Multi-Engine Candidate Extractor Module
Implements individual candidate extraction engines:
A. Camelot Lattice
B. Camelot Stream
C. pdfplumber extract_tables()
D. pdfplumber extract_words() spatial clustering
E. Tabula
"""
from typing import List, Dict, Any, Tuple
import pdfplumber
from backend.extractors.spatial_extractor import extract_tables_via_words
from backend.extractors.normalizer import clean_and_normalize_table
from backend.utils.logger import logger

def run_camelot_lattice(pdf_path: str) -> List[Dict[str, Any]]:
    rows = []
    try:
        import camelot
        tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
        for t in tables:
            for _, r in t.df.iterrows():
                rows.append(r.tolist())
        return clean_and_normalize_table(rows)
    except Exception as e:
        logger.debug(f"Camelot Lattice failed on {pdf_path}: {e}")
        return []

def run_camelot_stream(pdf_path: str) -> List[Dict[str, Any]]:
    rows = []
    try:
        import camelot
        tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
        for t in tables:
            for _, r in t.df.iterrows():
                rows.append(r.tolist())
        return clean_and_normalize_table(rows)
    except Exception as e:
        logger.debug(f"Camelot Stream failed on {pdf_path}: {e}")
        return []

def run_pdfplumber_tables(pdf_path: str) -> List[Dict[str, Any]]:
    rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for r in table:
                        if r:
                            rows.append(r)
        return clean_and_normalize_table(rows)
    except Exception as e:
        logger.debug(f"pdfplumber tables failed on {pdf_path}: {e}")
        return []

def run_pdfplumber_words(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        raw_rows = extract_tables_via_words(pdf_path)
        return clean_and_normalize_table(raw_rows)
    except Exception as e:
        logger.debug(f"pdfplumber words failed on {pdf_path}: {e}")
        return []

def run_tabula(pdf_path: str) -> List[Dict[str, Any]]:
    rows = []
    try:
        import tabula
        dfs = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, silent=True)
        for df in dfs:
            for _, r in df.iterrows():
                rows.append(r.tolist())
        return clean_and_normalize_table(rows)
    except Exception as e:
        logger.debug(f"Tabula failed on {pdf_path}: {e}")
        return []

def run_noisy_digital_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.extractors.noisy_extractor import extract_noisy_digital_tables
        raw_rows = extract_noisy_digital_tables(pdf_path)
        return clean_and_normalize_table(raw_rows)
    except Exception as e:
        logger.debug(f"Noisy digital extractor failed on {pdf_path}: {e}")
        return []

def run_robust_ocr_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.ocr.engine import ocr_engine
        result = ocr_engine.process_scanned_pdf(pdf_path)
        return result.get("transactions", [])
    except Exception as e:
        logger.debug(f"Robust OCR extractor failed on {pdf_path}: {e}")
        return []

def run_paddleocr_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.ocr.engine import ocr_engine
        return ocr_engine.process_via_paddleocr(pdf_path)
    except Exception as e:
        logger.debug(f"PaddleOCR extractor failed on {pdf_path}: {e}")
        return []


def run_spatial_ocr_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.extractors.spatial_ocr_extractor import extract_via_spatial_layout_ocr
        return extract_via_spatial_layout_ocr(pdf_path)
    except Exception as e:
        logger.debug(f"Spatial OCR extractor failed: {e}")
        return []

def run_opencv_grid_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.extractors.opencv_grid_extractor import extract_via_opencv_grid
        return extract_via_opencv_grid(pdf_path)
    except Exception as e:
        logger.debug(f"OpenCV grid extractor failed: {e}")
        return []

def run_local_vision_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from backend.extractors.local_vision_extractor import extract_via_local_vision
        return extract_via_local_vision(pdf_path)
    except Exception as e:
        logger.debug(f"Local vision extractor failed: {e}")
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




