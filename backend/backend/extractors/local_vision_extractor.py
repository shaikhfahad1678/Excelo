"""
Method 3: Local Compact Vision Model (Florence-2-base / Qwen2-VL)
"""
import base64
import json
import io
from typing import List, Dict, Any
import requests
import pdfplumber
from backend.extractors.normalizer import clean_and_normalize_table
from backend.utils.logger import logger

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def extract_via_local_vision(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Method 3: Local Compact Vision Model (Florence-2-base / Qwen2-VL)
    Extracts table transactions by rendering PDF pages and sending base64 images 
    to a local Ollama server running a vision model, or running Florence-2 locally.
    """
    logger.info(f"Method 3 Local Vision Extractor running on [{pdf_path}]...")
    
    # 1. Attempt to connect to local Ollama vision engine
    try:
        # Check if Ollama service is online
        test_res = requests.get("http://localhost:11434/api/tags", timeout=2)
        if test_res.status_code == 200:
            logger.info("Local Ollama server detected! Scanning installed models...")
            models_data = test_res.json()
            models_list = [m["name"] for m in models_data.get("models", [])]
            
            # Find first available vision-capable model
            vision_model = None
            for m in models_list:
                if any(v in m.lower() for v in ["vision", "vl", "minicpm", "llava"]):
                    vision_model = m
                    break
            
            if not vision_model and models_list:
                # Default fallback if no specific vision name but models exist
                vision_model = models_list[0]
                logger.warning(f"No explicitly named vision model found in Ollama. Trying first available: [{vision_model}]")

            if vision_model:
                logger.info(f"Running visual extraction via local Ollama model: [{vision_model}]...")
                return _extract_via_ollama(pdf_path, vision_model)
    except Exception as e:
        logger.debug(f"Local Ollama service not running or failed: {e}. Trying local transformers pipeline fallback...")

    # 2. Transformers Fallback (Florence-2 / Qwen2-VL local load)
    try:
        from transformers import AutoProcessor, AutoModelForCausalLM
        import torch
        from PIL import Image
        
        logger.info("Attempting local Florence-2-base transformers execution...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model_id = "microsoft/Florence-2-base"
        
        # Load model locally
        model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True).to(device)
        processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        
        raw_rows = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                pil_img = page.to_image(resolution=150).original.convert("RGB")
                
                # Query Florence-2 for table structure text representation
                prompt = "<OCR_WITH_REGION>"
                inputs = processor(text=prompt, images=pil_img, return_tensors="pt").to(device)
                
                generated_ids = model.generate(
                    input_ids=inputs["input_ids"],
                    pixel_values=inputs["pixel_values"],
                    max_new_tokens=1024,
                    num_beams=3
                )
                generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                
                # Florence-2 returns layout segments. We parse them into table lines.
                lines = [line.strip() for line in generated_text.split("\n") if line.strip()]
                for l in lines:
                    words = [w.strip() for w in l.split("  ") if w.strip()]
                    if words:
                        raw_rows.append(words)

        normalized = clean_and_normalize_table(raw_rows)
        logger.info(f"Florence-2 local extraction completed. Extracted {len(normalized)} rows.")
        return normalized

    except Exception as e:
        logger.warning(f"Local transformers loading skipped or failed: {e}. Falling back to spatial text parser simulation.")
        # Failsafe Local Simulation: runs native plumber words and filters borderless noisy lines cleanly
        from backend.extractors.candidate_extractors import run_noisy_digital_extractor
        return run_noisy_digital_extractor(pdf_path)


def _extract_via_ollama(pdf_path: str, model_name: str) -> List[Dict[str, Any]]:
    """Sends page images to Ollama API for structured extraction."""
    raw_rows = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            # Render page image to memory as base64 PNG
            pil_img = page.to_image(resolution=150).original
            buffer = io.BytesIO()
            pil_img.save(buffer, format="PNG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            prompt = """
            Extract all transaction rows found in this bank statement page image.
            Format the output strictly as a JSON list of transaction rows, where each row is an array of columns:
            [Date, Description, Cheque No, Debit, Credit, Balance].
            Do not include headers, footers, summaries, or introductory text. Just the JSON array.
            """

            payload = {
                "model": model_name,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False,
                "options": {
                    "temperature": 0.0
                }
            }

            try:
                res = requests.post(OLLAMA_API_URL, json=payload, timeout=45)
                if res.status_code == 200:
                    res_json = res.json()
                    response_text = res_json.get("response", "").strip()
                    
                    # Clean markdown codeblocks
                    if "```" in response_text:
                        response_text = response_text.split("```")[1]
                        if response_text.startswith("json"):
                            response_text = response_text[4:]
                    
                    parsed = json.loads(response_text)
                    if isinstance(parsed, list):
                        for row in parsed:
                            if isinstance(row, list) and any(row):
                                raw_rows.append([str(c or "") for c in row])
                else:
                    logger.warning(f"Ollama returned HTTP {res.status_code} for page {page_idx + 1}")
            except Exception as ex:
                logger.error(f"Error parsing Ollama response for page {page_idx + 1}: {ex}")

    if raw_rows:
        return clean_and_normalize_table(raw_rows)
        
    # Fallback if Ollama response was unparseable
    from backend.extractors.candidate_extractors import run_noisy_digital_extractor
    return run_noisy_digital_extractor(pdf_path)
