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

def run_pypdf_fast_lines(pdf_path: str) -> List[Dict[str, Any]]:
    rows = []
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text() or ""
            lines = text.splitlines()
            for line in lines:
                parts = [p.strip() for p in line.split("  ") if p.strip()]
                if parts:
                    rows.append(parts)
        return clean_and_normalize_table(rows)
    except Exception as e:
        logger.debug(f"pypdf fast lines failed on {pdf_path}: {e}")
        return []








