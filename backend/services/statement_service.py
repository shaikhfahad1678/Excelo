"""
Bank Statement Extraction & Processing Service
Manages file registration, pipeline execution, settings, and exports exclusively for:
- Union Bank Statement
- Yes Bank Statement
- HDFC Bank Statement
- Axis Bank Statement
- ICICI Bank Statement
- IndusInd Bank Statement
"""
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.extractors.pdf_classifier import classify_pdf_type
from backend.extractors.candidate_extractors import (
    run_union_extractor,
    run_yesbank_extractor,
    run_hdfc_extractor,
    run_axis_extractor,
    run_icici_extractor,
    run_indusind_extractor
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
    def __init__(self, workspace_dir: str = "c:/Fahad/excelo"):
        self.workspace_dir = workspace_dir
        self.upload_dir = os.path.join(workspace_dir, "data", "uploads")
        self.export_dir = os.path.join(workspace_dir, "data", "exports")
        self.results_dir = os.path.join(workspace_dir, "data", "results")
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)

        self.settings_file = os.path.join(workspace_dir, "data", "settings.json")

        self.file_cards: Dict[str, Dict[str, Any]] = {}
        self.extraction_results: Dict[str, Dict[str, Any]] = {}
        self.process_logs: List[Dict[str, Any]] = []
        self.history_records: List[Dict[str, Any]] = []

        self.settings: Dict[str, Any] = {
            "extraction_priority": "Accuracy First",
            "preferred_engine": "Auto Multi-Engine Pipeline",
            "confidence_threshold": 85.0,
            "validation_rules": {
                "arithmetic_check": True,
                "tolerance": 0.05,
                "duplicate_check": True
            },
            "excel_output": {
                "include_summary_sheet": True,
                "styling": "Corporate Blue",
                "format": "xlsx"
            },
            "batch_processing": {
                "max_concurrent": 4,
                "auto_export": False
            },
            "log_retention_days": 30
        }
        self._load_settings_from_disk()
        self._load_cards_and_results_from_disk()

    def _save_json_disk(self, path: str, data: Any):
        try:
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save json {path}: {e}")

    def _load_json_disk(self, path: str) -> Optional[Any]:
        try:
            import json
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load json {path}: {e}")
        return None

    def _load_cards_and_results_from_disk(self):
        try:
            import glob
            for card_file in glob.glob(os.path.join(self.results_dir, "*_card.json")):
                card = self._load_json_disk(card_file)
                if isinstance(card, dict) and "id" in card:
                    self.file_cards[card["id"]] = card
            for res_file in glob.glob(os.path.join(self.results_dir, "*_result.json")):
                res = self._load_json_disk(res_file)
                if isinstance(res, dict) and "file_id" in res:
                    self.extraction_results[res["file_id"]] = res
        except Exception as e:
            logger.warning(f"Error loading cards/results from disk: {e}")

    def register_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        file_id = str(uuid.uuid4())[:8]
        saved_filename = f"{file_id}_{filename}"
        file_path = os.path.join(self.upload_dir, saved_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        file_size = os.path.getsize(file_path)
        file_size_kb = round(file_size / 1024, 1)

        pdf_type, meta = classify_pdf_type(file_path)

        supported_types = [
            "Union Bank Statement",
            "Yes Bank Statement",
            "HDFC Bank Statement",
            "Axis Bank Statement",
            "ICICI Bank Statement",
            "IndusInd Bank Statement"
        ]
        target_engine = pdf_type if pdf_type in supported_types else self.settings.get("preferred_engine", "Auto Multi-Engine Pipeline")

        card = {
            "id": file_id,
            "filename": filename,
            "file_path": file_path,
            "pdf_type": pdf_type,
            "pages": meta.get("total_pages", 1),
            "file_size": f"{file_size_kb} KB",
            "status": "Ready",
            "extraction_method": target_engine,
            "progress": 0,
            "confidence_score": 0.0,
            "validation_status": "Pending",
            "detect_msg": f"Auto-detected as {pdf_type}",
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.file_cards[file_id] = card
        self._save_json_disk(os.path.join(self.results_dir, f"{file_id}_card.json"), card)
        return card

    def extract_file(self, file_id: str, engine_override: Optional[str] = None) -> Dict[str, Any]:
        if file_id not in self.file_cards:
            card_data = self._load_json_disk(os.path.join(self.results_dir, f"{file_id}_card.json"))
            if isinstance(card_data, dict):
                self.file_cards[file_id] = card_data
            else:
                import glob
                matches = glob.glob(os.path.join(self.upload_dir, f"{file_id}_*"))
                if matches:
                    fp = matches[0]
                    fname = os.path.basename(fp).split("_", 1)[-1]
                    pdf_type, _ = classify_pdf_type(fp)
                    card_data = {
                        "id": file_id,
                        "filename": fname,
                        "file_path": fp,
                        "pdf_type": pdf_type,
                        "pages": 1,
                        "file_size": f"{round(os.path.getsize(fp)/1024, 1)} KB",
                        "status": "Ready",
                        "extraction_method": self.settings["preferred_engine"],
                        "progress": 0,
                        "confidence_score": 0.0,
                        "validation_status": "Pending",
                        "detect_msg": f"Statement classified as {pdf_type}",
                        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.file_cards[file_id] = card_data
                else:
                    raise KeyError(f"File ID {file_id} not found in workspace.")

        card = self.file_cards[file_id]
        card["status"] = "Extracting"
        card["progress"] = 30
        pdf_path = card["file_path"]
        start_time = time.time()

        selected_engine = engine_override or self.settings["preferred_engine"]
        engine_used = selected_engine
        diagnostics = {}
        validated_txs = []
        summary = {}

        try:
            if selected_engine == "Union Bank Statement" or (selected_engine == "Auto Multi-Engine Pipeline" and card.get("pdf_type") == "Union Bank Statement"):
                raw = run_union_extractor(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
                engine_used = "Union Bank Statement Special Extractor"
            elif selected_engine == "Yes Bank Statement" or (selected_engine == "Auto Multi-Engine Pipeline" and card.get("pdf_type") == "Yes Bank Statement"):
                raw = run_yesbank_extractor(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
                engine_used = "Yes Bank Statement Special Extractor"
            elif selected_engine == "ICICI Bank Statement" or (selected_engine == "Auto Multi-Engine Pipeline" and card.get("pdf_type") == "ICICI Bank Statement"):
                raw = run_icici_extractor(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
                engine_used = "ICICI Bank Statement Special Extractor"
            elif selected_engine == "Axis Bank Statement" or (selected_engine == "Auto Multi-Engine Pipeline" and card.get("pdf_type") == "Axis Bank Statement"):
                raw = run_axis_extractor(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
                engine_used = "Axis Bank Statement Special Extractor"
            elif selected_engine == "IndusInd Bank Statement" or (selected_engine == "Auto Multi-Engine Pipeline" and card.get("pdf_type") == "IndusInd Bank Statement"):
                raw = run_indusind_extractor(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
                engine_used = "IndusInd Bank Statement Special Extractor"
            elif selected_engine == "HDFC Bank Statement" or (selected_engine == "Auto Multi-Engine Pipeline" and card.get("pdf_type") == "HDFC Bank Statement"):
                raw = run_hdfc_extractor(pdf_path)
                validated_txs, summary = validate_and_enrich_transactions(raw)
                engine_used = "HDFC Bank Statement Special Extractor"
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
        self._save_json_disk(os.path.join(self.results_dir, f"{file_id}_result.json"), result)

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
        successful_results = []
        for fid in file_ids:
            res = self.extraction_results.get(fid)
            if not res:
                res = self._load_json_disk(os.path.join(self.results_dir, f"{fid}_result.json"))
                if isinstance(res, dict):
                    self.extraction_results[fid] = res

            if not res or not res.get("success"):
                try:
                    res = self.extract_file(fid)
                except Exception as ex:
                    logger.warning(f"Auto-extraction during export failed for {fid}: {ex}")

            if res and res.get("success"):
                successful_results.append(res)

        if not successful_results:
            raise ValueError("No extracted data available for export. Please extract your PDF statement before exporting.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Excelo_Export_{timestamp}.{export_format}"
        filepath = os.path.join(self.export_dir, filename)

        if export_format == "csv":
            all_txs = []
            for res in successful_results:
                all_txs.extend(res["transactions"])
            generate_csv(all_txs, filepath)
        else:
            sheet_map = {}
            for res in successful_results:
                fname_clean = res["filename"][:25].replace(".pdf", "")
                sheet_map[fname_clean] = res["transactions"]
            generate_excel_workbook(sheet_map, filepath)

        return filepath

    def get_settings(self) -> Dict[str, Any]:
        return self.settings

    def update_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        self.settings.update(new_settings)
        self._save_settings_to_disk()
        return self.settings

    def _load_settings_from_disk(self):
        try:
            if os.path.exists(self.settings_file):
                import json
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        self.settings.update(saved)
                        logger.info("Loaded persistent settings from settings.json")
        except Exception as e:
            logger.warning(f"Could not load settings.json: {e}")

    def _save_settings_to_disk(self):
        try:
            import json
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
                logger.info("Saved persistent settings to settings.json")
        except Exception as e:
            logger.error(f"Could not save settings.json: {e}")

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.process_logs

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history_records

statement_service = StatementService()
