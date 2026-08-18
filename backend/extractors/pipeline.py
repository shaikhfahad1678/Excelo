"""
Multi-Stage Intelligent Extraction Pipeline
Executes candidate strategies based on PDF classification type:
- Native Digital PDF Strategy
- OCR Searchable PDF Strategy
- Scanned PDF Strategy

Calculates composite extraction quality scores and retries fallback engines until validation passes.
"""
from typing import List, Dict, Any, Tuple
from backend.extractors.pdf_classifier import (
    classify_pdf_type,
    TYPE_DIGITAL,
    TYPE_OCR_SEARCHABLE,
    TYPE_SCANNED,
    TYPE_HDFC,
    TYPE_INDUSIND,
    TYPE_AXIS,
    TYPE_ICICI
)
from backend.extractors.candidate_extractors import (
    run_camelot_lattice,
    run_camelot_stream,
    run_pdfplumber_tables,
    run_pdfplumber_words,
    run_tabula,
    run_noisy_digital_extractor,
    run_robust_ocr_extractor,
    run_paddleocr_extractor
)
from backend.validators.strict_validator import validate_and_enrich_transactions
from backend.utils.logger import logger

def calculate_composite_score(transactions: List[Dict[str, Any]], summary: Dict[str, Any]) -> float:
    """
    Calculates composite score based on:
    - Row count
    - Validation pass rate
    - Cell populated ratio
    - Zero duplicate / mismatch penalties
    """
    total_count = summary.get("total_count", 0)
    if total_count == 0:
        return 0.0

    pass_count = summary.get("pass_count", 0)
    pass_rate = (pass_count / total_count) * 100.0

    mismatches = summary.get("balance_mismatches", 0)
    duplicates = summary.get("duplicate_rows", 0)

    # Base score = row count points + pass rate weight - penalties
    score = (total_count * 5.0) + (pass_rate * 5.0) - (mismatches * 20.0) - (duplicates * 10.0)
    return max(round(score, 2), 0.0)

def execute_intelligent_pipeline(pdf_path: str) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    """
    Main Multi-Stage Extraction Pipeline entry point.
    1. Classifies PDF type into Native Digital, OCR Searchable, or Scanned.
    2. Runs ordered candidate strategies tailored for the classification type.
    3. Validates every row using 11 rules.
    4. Automatically falls back if validation fails.
    """
    pdf_type, class_meta = classify_pdf_type(pdf_path)
    logger.info(f"Initiating pipeline for [{pdf_path}] classified as: {pdf_type}")

    # Streamlined fast non-blocking candidate order based on PDF Type
    if pdf_type == TYPE_ICICI:
        from backend.extractors.candidate_extractors import run_icici_extractor
        candidate_sequence = [
            ("ICICI Bank Special Extractor", run_icici_extractor)
        ]
    elif pdf_type == TYPE_AXIS:
        from backend.extractors.candidate_extractors import run_axis_extractor
        candidate_sequence = [
            ("Axis Bank Special Extractor", run_axis_extractor)
        ]
    elif pdf_type == TYPE_INDUSIND:
        from backend.extractors.candidate_extractors import run_indusind_extractor
        candidate_sequence = [
            ("IndusInd Bank Special Extractor", run_indusind_extractor)
        ]
    elif pdf_type == TYPE_HDFC:
        from backend.extractors.candidate_extractors import run_hdfc_extractor
        candidate_sequence = [
            ("HDFC Bank Special Extractor", run_hdfc_extractor)
        ]
    elif pdf_type == TYPE_DIGITAL:
        candidate_sequence = [
            ("pdfplumber Tables", run_pdfplumber_tables),
            ("pdfplumber Words (Spatial)", run_pdfplumber_words),
            ("Noisy Digital Extractor", run_noisy_digital_extractor)
        ]
    elif pdf_type == TYPE_OCR_SEARCHABLE:
        candidate_sequence = [
            ("pdfplumber Words (Spatial)", run_pdfplumber_words),
            ("Noisy Digital Extractor", run_noisy_digital_extractor),
            ("Robust OCR Engine", run_robust_ocr_extractor)
        ]
    else: # TYPE_SCANNED
        candidate_sequence = [
            ("Robust OCR Engine", run_robust_ocr_extractor),
            ("PaddleOCR Engine (PP-OCRv4)", run_paddleocr_extractor)
        ]

    diagnostics = {
        "pdf_path": pdf_path,
        "pdf_type": pdf_type,
        "classification_meta": class_meta,
        "candidates": [],
        "attempted_methods": [],
        "selected_method": "None",
        "selection_reason": "No candidate strategy passed strict validation.",
        "is_failsafe_triggered": False
    }

    all_candidate_results = []

    for method_name, extractor_func in candidate_sequence:
        diagnostics["attempted_methods"].append(method_name)
        logger.info(f"Testing Candidate Strategy: [{method_name}]")

        try:
            raw_txs = extractor_func(pdf_path)
            enriched_txs, summary = validate_and_enrich_transactions(raw_txs)
            score = calculate_composite_score(enriched_txs, summary)

            cand_info = {
                "method": method_name,
                "rows_found": summary["total_count"],
                "pass_count": summary["pass_count"],
                "failed_count": summary["failed_count"],
                "is_valid": summary["is_valid"],
                "score": score,
                "summary": summary
            }
            diagnostics["candidates"].append(cand_info)
            all_candidate_results.append((score, method_name, enriched_txs, summary, cand_info))

            logger.info(f"Strategy [{method_name}] Result: Rows={summary['total_count']}, Valid={summary['is_valid']}, Score={score}")

            # If strict validation passed (is_valid == True), accept immediately!
            if summary["is_valid"] and score > 0:
                diagnostics["selected_method"] = method_name
                diagnostics["selection_reason"] = f"Strategy [{method_name}] passed all 11 strict validation rules with score {score}."
                logger.info(f"SUCCESS: Strategy [{method_name}] selected!")
                return enriched_txs, method_name, diagnostics

        except Exception as e:
            logger.warning(f"Strategy [{method_name}] failed execution: {e}")
            diagnostics["candidates"].append({
                "method": method_name,
                "rows_found": 0,
                "pass_count": 0,
                "failed_count": 0,
                "is_valid": False,
                "score": 0.0,
                "error": str(e)
            })

    # If no candidate passed 100% strict validation, pick highest scoring fallback if available
    all_candidate_results.sort(key=lambda x: x[0], reverse=True)
    if all_candidate_results and all_candidate_results[0][0] > 0:
        score, method_name, enriched_txs, summary, cand_info = all_candidate_results[0]
        diagnostics["selected_method"] = method_name
        diagnostics["selection_reason"] = (
            f"Validation fallback: Selected [{method_name}] with highest score ({score}), "
            f"though incomplete rate is {summary['incomplete_rate']}%."
        )
        diagnostics["is_failsafe_triggered"] = not summary["is_valid"]
        logger.warning(f"Fallback selection [{method_name}] with score {score}. Failsafe triggered: {diagnostics['is_failsafe_triggered']}")
        return enriched_txs, method_name, diagnostics
    else:
        diagnostics["is_failsafe_triggered"] = True
        return [], "None", diagnostics
