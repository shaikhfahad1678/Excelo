"""
Multi-Stage Intelligent Extraction Pipeline
Routes PDF statements exclusively to the supported bank statement special extractors:
- Union Bank Statement Special Extractor
- Yes Bank Statement Special Extractor
- HDFC Bank Statement Special Extractor
- Axis Bank Statement Special Extractor
- ICICI Bank Statement Special Extractor
- IndusInd Bank Statement Special Extractor
"""
from typing import List, Dict, Any, Tuple
from backend.extractors.pdf_classifier import (
    classify_pdf_type,
    TYPE_KOTAK,
    TYPE_PNB,
    TYPE_HDFC,
    TYPE_INDUSIND,
    TYPE_AXIS,
    TYPE_ICICI,
    TYPE_YESBANK,
    TYPE_UNION
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

    score = (total_count * 5.0) + (pass_rate * 5.0) - (mismatches * 20.0) - (duplicates * 10.0)
    return max(round(score, 2), 0.0)

def execute_intelligent_pipeline(pdf_path: str) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    """
    Main Extraction Pipeline entry point for supported bank statements.
    """
    pdf_type, class_meta = classify_pdf_type(pdf_path)
    logger.info(f"Initiating pipeline for [{pdf_path}] classified as: {pdf_type}")

    if pdf_type == TYPE_KOTAK:
        from backend.extractors.candidate_extractors import run_kotak_extractor
        candidate_sequence = [("Kotak Bank Special Extractor", run_kotak_extractor)]
    elif pdf_type == TYPE_PNB:
        from backend.extractors.candidate_extractors import run_pnb_extractor
        candidate_sequence = [("PNB Bank Special Extractor", run_pnb_extractor)]
    elif pdf_type == TYPE_UNION:
        from backend.extractors.candidate_extractors import run_union_extractor
        candidate_sequence = [("Union Bank Special Extractor", run_union_extractor)]
    elif pdf_type == TYPE_YESBANK:
        from backend.extractors.candidate_extractors import run_yesbank_extractor
        candidate_sequence = [("Yes Bank Special Extractor", run_yesbank_extractor)]
    elif pdf_type == TYPE_ICICI:
        from backend.extractors.candidate_extractors import run_icici_extractor
        candidate_sequence = [("ICICI Bank Special Extractor", run_icici_extractor)]
    elif pdf_type == TYPE_AXIS:
        from backend.extractors.candidate_extractors import run_axis_extractor
        candidate_sequence = [("Axis Bank Special Extractor", run_axis_extractor)]
    elif pdf_type == TYPE_INDUSIND:
        from backend.extractors.candidate_extractors import run_indusind_extractor
        candidate_sequence = [("IndusInd Bank Special Extractor", run_indusind_extractor)]
    elif pdf_type == TYPE_HDFC:
        from backend.extractors.candidate_extractors import run_hdfc_extractor
        candidate_sequence = [("HDFC Bank Special Extractor", run_hdfc_extractor)]
    else:
        candidate_sequence = []

    diagnostics = {
        "pdf_path": pdf_path,
        "pdf_type": pdf_type,
        "classification_meta": class_meta,
        "candidates": [],
        "attempted_methods": [],
        "selected_method": "None",
        "selection_reason": "Unsupported PDF type. Please provide a supported bank statement (HDFC, Axis, ICICI, IndusInd, Yes Bank, Union Bank).",
        "is_failsafe_triggered": True
    }

    if not candidate_sequence:
        logger.warning(f"Unsupported PDF type [{pdf_type}] for file [{pdf_path}].")
        return [], "None", diagnostics

    all_candidate_results = []

    for method_name, extractor_func in candidate_sequence:
        diagnostics["attempted_methods"].append(method_name)
        logger.info(f"Executing Extractor: [{method_name}]")

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

            logger.info(f"Extractor [{method_name}] Result: Rows={summary['total_count']}, Valid={summary['is_valid']}, Score={score}")

            if summary["is_valid"] and score > 0:
                diagnostics["selected_method"] = method_name
                diagnostics["selection_reason"] = f"Extractor [{method_name}] successfully extracted {summary['total_count']} transactions."
                diagnostics["is_failsafe_triggered"] = False
                return enriched_txs, method_name, diagnostics

        except Exception as e:
            logger.warning(f"Extractor [{method_name}] failed execution: {e}")
            diagnostics["candidates"].append({
                "method": method_name,
                "rows_found": 0,
                "pass_count": 0,
                "failed_count": 0,
                "is_valid": False,
                "score": 0.0,
                "error": str(e)
            })

    if all_candidate_results and all_candidate_results[0][0] > 0:
        score, method_name, enriched_txs, summary, cand_info = all_candidate_results[0]
        diagnostics["selected_method"] = method_name
        diagnostics["selection_reason"] = f"Extracted [{method_name}] with score ({score})."
        diagnostics["is_failsafe_triggered"] = not summary["is_valid"]
        return enriched_txs, method_name, diagnostics
    else:
        diagnostics["is_failsafe_triggered"] = True
        return [], "None", diagnostics
