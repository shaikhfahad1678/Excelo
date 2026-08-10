"""
FastAPI REST API Server for Excelo Bank Statement Processing Engine
"""
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.services.statement_service import statement_service

app = FastAPI(
    title="Excelo Financial REST API",
    description="Enterprise Bank Statement Parsing, Extraction & Validation System",
    version="2.0.0"
)

# Enable CORS for React Frontend (typically running on Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Pydantic Models
class ExtractRequest(BaseModel):
    file_ids: List[str]
    engine_override: Optional[str] = None
    engine_overrides: Optional[Dict[str, str]] = None


class ValidateRequest(BaseModel):
    transactions: List[Dict[str, Any]]
    tolerance: Optional[float] = 0.05

class RetryRequest(BaseModel):
    file_id: str
    preferred_engine: str

class GenerateExcelRequest(BaseModel):
    file_ids: List[str]
    format: Optional[str] = "xlsx"

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "Excelo Statement Processing Engine",
        "engines": ["Camelot Lattice", "Camelot Stream", "pdfplumber Tables", "pdfplumber Words (Spatial)", "Tabula"],
        "version": "2.0.0"
    }

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    POST /upload
    Handles single or multiple PDF uploads.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    uploaded_cards = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        content = await file.read()
        card = statement_service.register_file(file.filename, content)
        uploaded_cards.append(card)

    if not uploaded_cards:
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    return {"status": "success", "files": uploaded_cards}



@app.post("/api/extract")
def extract_pdf(req: ExtractRequest):
    """
    POST /extract
    Executes extraction pipeline for specified files.
    """
    results = []
    overrides = req.engine_overrides or {}
    for file_id in req.file_ids:
        try:
            override = overrides.get(file_id) or req.engine_override
            res = statement_service.extract_file(file_id, engine_override=override)
            results.append(res)
        except Exception as e:
            results.append({
                "file_id": file_id,
                "filename": file_id,
                "success": False,
                "error": str(e),
                "transactions": [],
                "summary": {}
            })
    return {"status": "success", "results": results}


@app.post("/api/validate")
def validate_transactions_endpoint(req: ValidateRequest):
    """
    POST /validate
    Re-evaluates balance arithmetic validation on transaction rows.
    """
    from backend.validators.strict_validator import validate_and_enrich_transactions
    validated_txs, summary = validate_and_enrich_transactions(req.transactions, tolerance=req.tolerance or 0.05)
    return {"status": "success", "transactions": validated_txs, "summary": summary}

@app.post("/api/retry")
def retry_extraction(req: RetryRequest):
    """
    POST /retry
    Retries extraction using user's chosen fallback engine.
    """
    try:
        res = statement_service.retry_file(req.file_id, req.preferred_engine)
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-excel")
def generate_excel_endpoint(req: GenerateExcelRequest):
    """
    POST /generate-excel
    Generates Excel or CSV workbook.
    """
    try:
        export_filename = statement_service.generate_export(req.file_ids, export_format=req.format or "xlsx")
        download_url = f"/api/download/{export_filename}"
        return {"status": "success", "download_url": download_url, "filename": export_filename}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/download/{filename}")
def download_file(filename: str):
    filepath = os.path.join(statement_service.export_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Requested file not found.")

    media_type = "text/csv" if filename.endswith(".csv") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(filepath, media_type=media_type, filename=filename)

@app.get("/api/history")
def get_history():
    """
    GET /history
    """
    return {"status": "success", "history": statement_service.get_history()}

@app.get("/api/logs")
def get_logs():
    """
    GET /logs
    """
    return {"status": "success", "logs": statement_service.get_logs()}



@app.get("/api/files/{file_id}/status")
def get_file_status(file_id: str):
    """
    GET /files/{file_id}/status
    Fetches live progress and status messages during extraction.
    """
    card = statement_service.file_cards.get(file_id)
    if not card:
        return {"status": "not_found", "progress": 0, "detect_msg": ""}
    return {
        "status": "success",
        "progress": card.get("progress", 0),
        "detect_msg": card.get("detect_msg", "")
    }

@app.delete("/api/files/{file_id}")
def delete_file_endpoint(file_id: str):
    """
    DELETE /files/{file_id}
    Deletes uploaded PDF file physically from disk and workspace memory.
    """
    success = statement_service.delete_file(file_id)
    return {"status": "success" if success else "not_found"}


