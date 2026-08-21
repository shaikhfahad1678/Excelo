"""
FastAPI REST API Server for Excelo Bank Statement Processing Engine
"""
import os
import sys
from pathlib import Path

# Add project root and backend directory to sys.path for Vercel Serverless environment
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.services.statement_service import statement_service
from backend.utils.logger import logger

app = FastAPI(
    title="Excelo Financial REST API",
    description="Enterprise Bank Statement Parsing, Extraction & Validation System",
    version="2.6.0"
)

# Enable CORS for React Frontend (running on Vite or Vercel)
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

# Router for all API endpoints
router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "online",
        "service": "Excelo Statement Processing Engine",
        "engines": ["Camelot Lattice", "Camelot Stream", "pdfplumber Tables", "pdfplumber Words (Spatial)", "Tabula"],
        "version": "2.6.0"
    }

@router.get("/cloudflare/status")
def cloudflare_status():
    """
    Checks Cloudflare R2 connection status and credential configuration.
    """
    return statement_service.check_cloudflare_connection()

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
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

@router.post("/extract")
def extract_pdf(req: ExtractRequest):
    """
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

@router.post("/validate")
def validate_transactions_endpoint(req: ValidateRequest):
    """
    Re-evaluates balance arithmetic validation on transaction rows.
    """
    from backend.validators.strict_validator import validate_and_enrich_transactions
    validated_txs, summary = validate_and_enrich_transactions(req.transactions, tolerance=req.tolerance or 0.05)
    return {"status": "success", "transactions": validated_txs, "summary": summary}

@router.post("/retry")
def retry_extraction(req: RetryRequest):
    """
    Retries extraction using chosen fallback engine.
    """
    try:
        res = statement_service.retry_file(req.file_id, req.preferred_engine)
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-excel")
def generate_excel_endpoint(req: GenerateExcelRequest):
    """
    Generates Excel or CSV workbook.
    """
    try:
        export_path_or_name = statement_service.generate_export(req.file_ids, export_format=req.format or "xlsx")
        export_filename = os.path.basename(export_path_or_name)
        download_url = f"/api/download/{export_filename}"
        return {"status": "success", "download_url": download_url, "filename": export_filename}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/download/{filename}")
def download_file(filename: str):
    clean_filename = os.path.basename(filename)
    filepath = os.path.join(statement_service.export_dir, clean_filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Requested file not found.")

    media_type = "text/csv" if clean_filename.endswith(".csv") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(filepath, media_type=media_type, filename=clean_filename)

@router.get("/history")
def get_history():
    return {"status": "success", "history": statement_service.get_history()}

@router.get("/logs")
def get_logs():
    return {"status": "success", "logs": statement_service.get_logs()}

@router.get("/files/{file_id}/status")
def get_file_status(file_id: str):
    card = statement_service.get_card(file_id)
    if not card:
        return {"status": "not_found", "progress": 100, "detect_msg": "Processing"}
    return {
        "status": "success",
        "progress": card.get("progress", 0),
        "detect_msg": card.get("detect_msg", "")
    }

@router.delete("/files/{file_id}")
def delete_file_endpoint(file_id: str):
    success = statement_service.delete_file(file_id)
    return {"status": "success" if success else "not_found"}

# Mount router for both '/api' prefixed requests and root requests (handles all Vercel path rewrite modes)
app.include_router(router, prefix="/api")
app.include_router(router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global server error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": str(exc), "message": f"Server Error: {str(exc)}"}
    )
