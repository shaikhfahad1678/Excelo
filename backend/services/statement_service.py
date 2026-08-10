"""
Bank Statement Extraction & Processing Service
Manages file registration, pipeline execution, settings, and exports.
"""
import os
import time
import uuid
import tempfile
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.extractors.pdf_classifier import classify_pdf_type, TYPE_DIGITAL
from backend.extractors.candidate_extractors import (
    run_camelot_lattice,
    run_camelot_stream,
    run_pdfplumber_tables,
    run_pdfplumber_words,
    run_tabula
)
from backend.extractors.pipeline import execute_intelligent_pipeline
from backend.validators.strict_validator import validate_and_enrich_transactions
from backend.excel.writer import generate_excel_workbook, generate_csv
from backend.utils.logger import logger

FAILSAFE_WARNING_MSG = (
    "Fail Safe Warning — Action Required\n"
    "Extraction quality is below acceptable level. Automatic retries completed. Manual review required.\n"
    "Every candidate strategy was evaluated. The current row accuracy or balance validation rate fell below the 98% threshold limit."
)

class StatementService:
    def __init__(self, workspace_dir: Optional[str] = None):
        if os.environ.get("VERCEL") or not workspace_dir or not os.path.exists(str(workspace_dir)):
            base_dir = tempfile.gettempdir()
        else:
            base_dir = str(workspace_dir)

        self.upload_dir = os.path.join(base_dir, "data", "uploads")
        self.export_dir = os.path.join(base_dir, "data", "exports")

        try:
            os.makedirs(self.upload_dir, exist_ok=True)
            os.makedirs(self.export_dir, exist_ok=True)
        except OSError:
            base_dir = tempfile.gettempdir()
            self.upload_dir = os.path.join(base_dir, "data", "uploads")
            self.export_dir = os.path.join(base_dir, "data", "exports")
            os.makedirs(self.upload_dir, exist_ok=True)
            os.makedirs(self.export_dir, exist_ok=True)

        self.file_cards: Dict[str, Dict[str, Any]] = {}
        self.extraction_results: Dict[str, Dict[str, Any]] = {}
        self.process_logs: List[Dict[str, Any]] = []
        self.history_records: List[Dict[str, Any]] = []
        self.clean_upload_directory()

    def clean_upload_directory(self):
        try:
            if os.path.exists(self.upload_dir):
                for f in os.listdir(self.upload_dir):
                    fp = os.path.join(self.upload_dir, f)
                    if os.path.isfile(fp):
                        os.remove(fp)
                logger.info("Cleaned upload directory.")
        except Exception as e:
            logger.error(f"Error cleaning upload directory: {e}")

    def delete_file(self, file_id: str) -> bool:
        card = self.get_card(file_id)
        if file_id in self.file_cards:
            self.file_cards.pop(file_id)
        
        json_path = os.path.join(self.upload_dir, f"{file_id}.json")
        if os.path.exists(json_path):
            try:
                os.remove(json_path)
            except Exception as e:
                logger.error(f"Error deleting card json {json_path}: {e}")

        file_path = card.get("file_path") if card else None
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted uploaded file from disk: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
        
        if file_id in self.extraction_results:
            del self.extraction_results[file_id]
        return True

    def save_card_to_disk(self, card: Dict[str, Any]):
        try:
            json_path = os.path.join(self.upload_dir, f"{card['id']}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(card, f)
        except Exception as e:
            logger.warning(f"Could not save card to disk: {e}")

    def save_result_to_disk(self, file_id: str, result: Dict[str, Any]):
        """Persist extraction result to disk so it survives process restarts."""
        try:
            result_path = os.path.join(self.upload_dir, f"{file_id}.result.json")
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(result, f)
        except Exception as e:
            logger.warning(f"Could not save result to disk: {e}")

    def load_result_from_disk(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Load extraction result from disk if not in memory."""
        result_path = os.path.join(self.upload_dir, f"{file_id}.result.json")
        if os.path.exists(result_path):
            try:
                with open(result_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load result from disk: {e}")
        return None

    def get_card(self, file_id: str) -> Optional[Dict[str, Any]]:
        if file_id in self.file_cards:
            return self.file_cards[file_id]

        json_path = os.path.join(self.upload_dir, f"{file_id}.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    card = json.load(f)
                    self.file_cards[file_id] = card
                    return card
            except Exception as e:
                logger.warning(f"Could not load card from disk: {e}")

        if os.path.exists(self.upload_dir):
            for fname in os.listdir(self.upload_dir):
                if fname.startswith(f"{file_id}_") and fname.endswith(".pdf"):
                    pdf_path = os.path.join(self.upload_dir, fname)
                    orig_filename = fname[len(file_id) + 1:]
                    pdf_type, meta = classify_pdf_type(pdf_path)
                    card = {
                        "id": file_id,
                        "filename": orig_filename,
                        "file_path": pdf_path,
                        "pdf_type": pdf_type,
                        "pages": 1,
                        "file_size": "PDF",
                        "status": "Ready",
                        "extraction_method": "Auto Multi-Engine Pipeline",
                        "progress": 0,
                        "confidence_score": 0.0,
                        "validation_status": "Pending",
                        "detect_msg": f"Statement classified as {pdf_type}",
                        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.file_cards[file_id] = card
                    self.save_card_to_disk(card)
                    return card
        return None

    def register_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        file_id = str(uuid.uuid4())[:8]
        saved_filename = f"{file_id}_{filename}"
        file_path = os.path.join(self.upload_dir, saved_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        file_size = os.path.getsize(file_path)
        file_size_kb = round(file_size / 1024, 1)

        pdf_type, meta = classify_pdf_type(file_path)
        is_digital = pdf_type == TYPE_DIGITAL

        card = {
            "id": file_id,
            "filename": filename,
            "file_path": file_path,
            "pdf_type": pdf_type,
            "pages": meta.get("total_pages", 1),
            "file_size": f"{file_size_kb} KB",
            "status": "Ready" if is_digital else "Failed",
            "extraction_method": "Auto Multi-Engine Pipeline",
            "progress": 0,
            "confidence_score": 0.0,
            "validation_status": "Pending" if is_digital else "Errors",
            "detect_msg": f"Statement classified as {pdf_type}" if is_digital else "Failed: Noisy or scanned non-digital PDF cannot be parsed.",
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.file_cards[file_id] = card
        self.save_card_to_disk(card)
        return card

    def extract_file(self, file_id: str, engine_override: Optional[str] = None) -> Dict[str, Any]:
        card = self.get_card(file_id)
        if not card:
            return {
                "file_id": file_id,
                "filename": file_id,
                "success": False,
                "error": "File session expired or not found on serverless container. Please re-upload PDF.",
                "transactions": [],
                "summary": {}
            }

        card["status"] = "Extracting"
        card["progress"] = 30
        self.save_card_to_disk(card)
        pdf_path = card["file_path"]
        start_time = time.time()

        pdf_type, meta = classify_pdf_type(pdf_path)
        if pdf_type != TYPE_DIGITAL:
            card["status"] = "Failed"
            card["progress"] = 100
            card["validation_status"] = "Errors"
            card["detect_msg"] = "Failed: Noisy or scanned non-digital PDF cannot be parsed."
            self.save_card_to_disk(card)
            return {
                "file_id": file_id,
                "filename": card["filename"],
                "pdf_type": pdf_type,
                "success": False,
                "engine_used": "None",
                "processing_time": 0.05,
                "confidence_score": 0.0,
                "failsafe_warning": "Failed: Noisy or scanned non-digital PDF cannot be parsed.",
                "error": "Failed: Noisy or scanned non-digital PDF cannot be parsed.",
                "transactions": [],
                "summary": {"total_count": 0, "pass_count": 0, "failed_count": 0, "is_valid": False},
                "diagnostics": {"selected_method": "None", "selection_reason": "Failed: Noisy or scanned non-digital PDF cannot be parsed."}
            }

        selected_engine = engine_override or "Auto Multi-Engine Pipeline"

        engine_used = selected_engine
        diagnostics = {}
        validated_txs = []
        summary = {}

        try:
            if "TYPE 1" in selected_engine:
                from backend.extractors.candidate_extractors import run_pdfplumber_tables, run_pdfplumber_words, run_noisy_digital_extractor
                raw = run_pdfplumber_tables(pdf_path)
                if not raw:
                    raw = run_pdfplumber_words(pdf_path)
                if not raw:
                    raw = run_noisy_digital_extractor(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
                engine_used = "TYPE 1: Native Digital PDF Pipeline"



            elif selected_engine == "Camelot Lattice":
                raw = run_camelot_lattice(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
            elif selected_engine == "Camelot Stream":
                raw = run_camelot_stream(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
            elif selected_engine == "pdfplumber Tables":
                raw = run_pdfplumber_tables(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
            elif selected_engine == "pdfplumber Words (Spatial)":
                raw = run_pdfplumber_words(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
            elif selected_engine == "Tabula":
                raw = run_tabula(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
            else:
                validated_txs, engine_used, diagnostics = execute_intelligent_pipeline(pdf_path)
                summary = diagnostics.get("candidates", [{}])[-1].get("summary", {}) if diagnostics.get("candidates") else {}
                if not summary and validated_txs:
                    _, summary = validate_and_enrich_transactions(validated_txs)
        except Exception as e:
            logger.error(f"Extraction failed for [{pdf_path}] using engine [{selected_engine}]: {e}")
            processing_time = round(time.time() - start_time, 2)
            card["status"] = "Failed"
            card["progress"] = 100
            card["confidence_score"] = 0.0
            card["extraction_method"] = selected_engine
            card["validation_status"] = "Errors"
            card["error_msg"] = str(e)

            result = {
                "file_id": file_id,
                "filename": card["filename"],
                "pdf_type": card["pdf_type"],
                "success": False,
                "engine_used": selected_engine,
                "processing_time": processing_time,
                "confidence_score": 0.0,
                "failsafe_warning": f"Extraction Engine Failure: {str(e)}",
                "error": str(e),
                "transactions": [],
                "summary": {"total_count": 0, "pass_count": 0, "failed_count": 0, "is_valid": False},
                "diagnostics": diagnostics or {"selected_method": selected_engine, "selection_reason": str(e)}
            }
            self.save_card_to_disk(card)
            self.extraction_results[file_id] = result
            return result

        card["progress"] = 70
        processing_time = round(time.time() - start_time, 2)

        total_count = summary.get("total_count", len(validated_txs))
        pass_count = summary.get("pass_count", 0)
        is_valid = summary.get("is_valid", True)
        conf_score = round((pass_count / total_count * 100), 1) if total_count > 0 else 0.0

        is_failsafe = diagnostics.get("is_failsafe_triggered", not is_valid)
        failsafe_msg = FAILSAFE_WARNING_MSG if is_failsafe else None

        card["status"] = "Completed" if (total_count > 0 and not is_failsafe) else "Failed Validation"
        card["progress"] = 100
        card["confidence_score"] = conf_score
        card["extraction_method"] = engine_used
        card["validation_status"] = "OK" if not is_failsafe else "Errors"
        self.save_card_to_disk(card)

        result = {
            "file_id": file_id,
            "filename": card["filename"],
            "pdf_type": card["pdf_type"],
            "success": total_count > 0,
            "engine_used": engine_used,
            "processing_time": processing_time,
            "confidence_score": conf_score,
            "failsafe_warning": failsafe_msg,
            "transactions": validated_txs,
            "summary": summary,
            "diagnostics": diagnostics
        }

        self.extraction_results[file_id] = result
        self.save_result_to_disk(file_id, result)

        # Log process entry
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pdf_name": card["filename"],
            "pdf_type": card["pdf_type"],
            "processing_method": engine_used,
            "fallback_methods_attempted": diagnostics.get("attempted_methods", [engine_used]),
            "pages_reprocessed": card["pages"],
            "rows_extracted": total_count,
            "rows_reconstructed": sum(1 for t in validated_txs if t.get("Validation Status") == "RECONSTRUCTED"),
            "rows_missing": summary.get("failed_count", 0),
            "validation_result": "PASS" if not is_failsafe else "FAILED VALIDATION",
            "processing_duration": f"{processing_time}s",
            "confidence_score": f"{conf_score}%"
        }
        self.process_logs.insert(0, log_entry)

        # Store history record
        history_record = {
            "session_id": str(uuid.uuid4())[:8],
            "file_id": file_id,
            "filename": card["filename"],
            "total_transactions": total_count,
            "total_debit": summary.get("total_debit", 0.0),
            "total_credit": summary.get("total_credit", 0.0),
            "engine": engine_used,
            "confidence": conf_score,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history_records.insert(0, history_record)

        return result

    def retry_file(self, file_id: str, preferred_engine: str) -> Dict[str, Any]:
        return self.extract_file(file_id, engine_override=preferred_engine)

    def generate_export(self, file_ids: List[str], export_format: str = "xlsx") -> str:
        exportable_results = []
        for fid in file_ids:
            # Prefer in-memory, then fall back to disk
            result = self.extraction_results.get(fid) or self.load_result_from_disk(fid)
            if result:
                # Cache back into memory if restored from disk
                if fid not in self.extraction_results:
                    self.extraction_results[fid] = result
                # Export if transactions exist (allow partial/failsafe results too)
                if result.get("transactions"):
                    exportable_results.append(result)

        if not exportable_results:
            raise ValueError("No extracted data available for export. Please run extraction first.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Excelo_Export_{timestamp}.{export_format}"
        filepath = os.path.join(self.export_dir, filename)

        if export_format == "csv":
            all_txs = []
            for res in exportable_results:
                all_txs.extend(res["transactions"])
            generate_csv(all_txs, filepath)
        else:
            sheet_map = {}
            for res in exportable_results:
                fname_clean = res["filename"][:25].replace(".pdf", "")
                sheet_map[fname_clean] = res["transactions"]
            generate_excel_workbook(sheet_map, filepath)

        return filename



    def get_logs(self) -> List[Dict[str, Any]]:
        return self.process_logs

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history_records

statement_service = StatementService()
