"""
HDFC Bank Statement PDF Extractor
Specialized high-precision extractor for HDFC Bank Statements.
Handles multiline narrations, page breaks, column alignment, debit/credit split, and balance math validation.
"""
import re
from typing import List, Dict, Any, Optional
import pdfplumber
from backend.extractors.normalizer import parse_amount
from backend.utils.logger import logger

DATE_REGEX = re.compile(r'^\d{2}/\d{2}/\d{2,4}$')

HDFC_NOISE_PHRASES = [
    "statementofaccount", "pageno", "hdfcbanklimited", "accountbranch",
    "jointholders", "nomination", "odlimit", "rtgs/neftifsc",
    "closingbalanceincludes", "contentsofthisstatement",
    "stateaccountbranchgstn", "registeredofficeaddress", "hdfcbankgstin",
    "address:", "city:", "state:", "phoneno", "currency:", "custid",
    "accountno", "a/copendate", "accountstatus", "micr:", "branchcode",
    "accounttype", "datenarration", "chq./ref.no.", "valuedt",
    "withdrawalamt.", "depositamt.", "closingbalance", "periodfrom",
    "from:01", "from:02", "from:03", "from:04", "from:05", "to:31", "to:30"
]

def is_noise_line(line_text: str) -> bool:
    clean = line_text.lower().replace(' ', '')
    if not clean:
        return True
    tokens = line_text.split()
    if tokens and DATE_REGEX.match(tokens[0]):
        return False
    for phrase in HDFC_NOISE_PHRASES:
        phrase_clean = phrase.replace(' ', '')
        if phrase_clean in clean:
            return True
    return False

def extract_hdfc_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts structured transactions from HDFC Bank Statement PDF.
    Supports native digital PDFs via spatial word clustering and scanned PDFs via OCR.
    """
    logger.info(f"HDFC Special Extractor running on [{pdf_path}]...")
    transactions = []
    
    # Pass 1: pdfplumber spatial extraction
    try:
        with pdfplumber.open(pdf_path) as pdf:
            active_tx = None
            prev_balance = None
            
            for page in pdf.pages:
                words = [w for w in page.extract_words() if 200.0 <= w['top'] <= 780.0]
                if not words:
                    continue
                words_sorted = sorted(words, key=lambda w: (w['top'], w['x0']))
                
                lines = []
                curr_line = []
                curr_y = None
                
                for w in words_sorted:
                    if curr_y is None or abs(w['top'] - curr_y) <= 3.5:
                        curr_line.append(w)
                        if curr_y is None:
                            curr_y = w['top']
                    else:
                        lines.append((curr_y, curr_line))
                        curr_line = [w]
                        curr_y = w['top']
                if curr_line:
                    lines.append((curr_y, curr_line))
                    
                for y, line_words in lines:
                    line_text = " ".join([w['text'] for w in line_words]).strip()
                    if is_noise_line(line_text):
                        continue
                        
                    first_word = line_words[0]['text']
                    x0_start = line_words[0]['x0']
                    
                    if x0_start < 50.0 and DATE_REGEX.match(first_word):
                        if active_tx:
                            transactions.append(active_tx)
                            
                        tx_date = first_word
                        
                        narr_words = []
                        ref_words = []
                        val_dt_words = []
                        with_words = []
                        dep_words = []
                        bal_words = []
                        
                        for w in line_words[1:]:
                            x = w['x0']
                            txt = w['text']
                            if x < 275:
                                narr_words.append(txt)
                            elif x < 360:
                                ref_words.append(txt)
                            elif x < 415:
                                val_dt_words.append(txt)
                            elif x < 475:
                                with_words.append(txt)
                            elif x < 540:
                                dep_words.append(txt)
                            else:
                                bal_words.append(txt)
                                
                        narr_str = " ".join(narr_words).strip()
                        ref_str = " ".join(ref_words).strip()
                        val_dt_str = " ".join(val_dt_words).strip()
                        with_str = " ".join(with_words).strip()
                        dep_str = " ".join(dep_words).strip()
                        bal_str = " ".join(bal_words).strip()
                        
                        if ref_str:
                            parts = ref_str.split()
                            if len(parts) > 1 and DATE_REGEX.match(parts[-1]):
                                val_dt_str = parts[-1]
                                ref_str = " ".join(parts[:-1])
                        if not val_dt_str:
                            val_dt_str = tx_date
                            
                        debit = parse_amount(with_str)
                        credit = parse_amount(dep_str)
                        balance = parse_amount(bal_str)
                        
                        # Balance math cross check
                        if balance is not None and prev_balance is not None:
                            amt = debit or credit
                            if amt is not None:
                                if abs((prev_balance - amt) - balance) < 0.05:
                                    debit = amt
                                    credit = None
                                elif abs((prev_balance + amt) - balance) < 0.05:
                                    credit = amt
                                    debit = None
                                    
                        if balance is not None:
                            prev_balance = balance
                            
                        active_tx = {
                            "Date": tx_date,
                            "Description": narr_str,
                            "Ref No.": ref_str,
                            "Value Date": val_dt_str,
                            "Debit": debit,
                            "Credit": credit,
                            "Balance": balance
                        }
                    else:
                        if active_tx:
                            if not is_noise_line(line_text):
                                active_tx["Description"] = (active_tx["Description"] + " " + line_text).strip()
                                
            if active_tx:
                transactions.append(active_tx)
                
            if transactions:
                logger.info(f"HDFC Special Extractor successfully parsed {len(transactions)} transactions via spatial digital mode.")
                return transactions
    except Exception as e:
        logger.warning(f"HDFC spatial digital pass encountered error: {e}. Trying OCR fallback...")

    # Pass 2: OCR Fallback for Scanned HDFC Statements
    try:
        from backend.ocr.engine import ocr_engine
        raw_ocr = ocr_engine.process_via_paddleocr(pdf_path) or ocr_engine.process_scanned_pdf(pdf_path).get("transactions", [])
        if raw_ocr:
            logger.info(f"HDFC Extractor returned {len(raw_ocr)} transactions via OCR fallback.")
            return raw_ocr
    except Exception as e:
        logger.error(f"HDFC OCR fallback failed: {e}")
        
    return []
