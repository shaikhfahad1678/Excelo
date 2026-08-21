"""
Backend Controller API wrapper for processing PDFs with Diagnostic support.
Provides two export modes:
  - export_to_file: writes directly to a user-chosen file path
  - export_batch_to_excel: batch mode with auto-generated filenames
"""
import os
import time
import copy
from typing import List, Dict, Any, Tuple
from datetime import datetime
from backend.utils.pdf_detector import detect_pdf_type
from backend.extractors.pipeline import run_extraction_pipeline
from backend.validators.bank_validator import validate_transactions
from backend.excel.writer import generate_excel_workbook, generate_csv
from backend.utils.logger import logger


def process_pdf_file(pdf_path: str) -> Dict[str, Any]:
    """
    Processes a single PDF bank statement:
    1. Digital PDF detection
    2. Multi-engine extraction pipeline (Camelot Lattice/Stream, pdfplumber, Tabula)
    3. Running balance validation
    Returns result metadata dictionary including Debug Diagnostics.
    """
    start_time = time.time()
    filename = os.path.basename(pdf_path)

    # Step 1: Detect PDF Type
    is_digital, detect_msg, pdf_meta = detect_pdf_type(pdf_path)
    if not is_digital:
        return {
            "success": False,
            "filename": filename,
            "error": detect_msg,
            "transactions": [],
            "summary": {},
            "diagnostics": {
                "pdf_path": pdf_path,
                "candidates": [],
                "selected_method": "None",
                "selection_reason": detect_msg
            }
        }

    # Step 2: Extract transactions via multi-engine scoring pipeline
    transactions, engine_used, diagnostics = run_extraction_pipeline(pdf_path)
    if not transactions:
        return {
            "success": False,
            "filename": filename,
            "error": "No transaction table found or unable to extract transactions.",
            "transactions": [],
            "summary": {},
            "diagnostics": diagnostics
        }

    # Step 3: Validate transactions
    validated_txs, summary = validate_transactions(transactions)
    processing_time = round(time.time() - start_time, 2)

    logger.info(f"Successfully processed [{filename}] in {processing_time}s using {engine_used}. Total: {summary['total_count']} txs.")

    return {
        "success": True,
        "filename": filename,
        "pdf_path": pdf_path,
        "engine_used": engine_used,
        "processing_time": processing_time,
        "transactions": validated_txs,
        "summary": summary,
        "diagnostics": diagnostics
    }


def export_to_file(results: List[Dict[str, Any]], filepath: str, file_format: str = "xlsx") -> str:
    """
    Exports all successful results directly to the given filepath.
    Supports 'xlsx' and 'csv' formats.
    Returns the output filepath on success, or raises an exception.
    """
    successful = [r for r in results if r.get("success") and r.get("transactions")]
    if not successful:
        raise ValueError("No successful extraction results to export.")

    if file_format == "csv":
        # CSV: merge all transactions into one flat file
        all_txs = []
        for res in successful:
            all_txs.extend(res["transactions"])
        generate_csv(all_txs, filepath)
        logger.info(f"Exported CSV to: {filepath}")
        return filepath
    else:
        # XLSX: one worksheet per PDF
        sheet_map = {}
        for res in successful:
            sheet_name = os.path.splitext(res["filename"])[0]
            sheet_map[sheet_name] = res["transactions"]
        generate_excel_workbook(sheet_map, filepath)
        logger.info(f"Exported Excel to: {filepath}")
        return filepath
