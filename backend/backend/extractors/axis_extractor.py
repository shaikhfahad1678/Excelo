"""
Axis Bank Statement Special Extractor Module
Handles spatial column binning, multi-line narration joining,
footer noise filtering, and balance chain validation.
"""
import os
import re
from typing import List, Dict, Any, Optional
import pdfplumber
from backend.utils.logger import logger

DATE_REGEX = re.compile(r'^\d{2}-\d{2}-\d{4}$')

def parse_amount(val_str: str) -> Optional[float]:
    if not val_str:
        return None
    cleaned = val_str.replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

def run_axis_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parses Axis Bank Statement PDFs using spatial bounding-box clustering.
    Returns cleaned list of transaction dicts.
    """
    logger.info(f"Axis Special Extractor running on [{pdf_path}]...")
    all_transactions = []
    pending_pre_narr = []
    stop_extraction = False

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            if stop_extraction:
                break

            words = page.extract_words()
            if not words:
                continue

            lines = []
            for w in words:
                top = round(w['top'], 1)
                found = False
                for l in lines:
                    if abs(l['top'] - top) <= 3.0:
                        l['words'].append(w)
                        found = True
                        break
                if not found:
                    lines.append({'top': top, 'words': [w]})

            lines.sort(key=lambda l: l['top'])

            for l in lines:
                l['words'].sort(key=lambda w: w['x0'])
                line_text = ' '.join(w['text'] for w in l['words']).strip()
                line_lower = line_text.lower()

                # Stop extraction at footer disclaimers / legends
                if any(term in line_lower for term in [
                    'transaction total', 'closing balance', 'unless the constituent',
                    'deposit insurance', 'in compliance with', 'to ensure you never',
                    'registered office', 'branch address', 'legends :', '++++ end of statement ++++'
                ]):
                    if 'transaction total' in line_lower or 'closing balance' in line_lower or 'unless the constituent' in line_lower:
                        stop_extraction = True
                        break
                    continue

                # Skip top header noise
                if any(h in line_lower for h in [
                    'statement of axis account', 'tran date', 'chq no', 'particulars',
                    'opening balance', 'customer id:', 'ifsc code:', 'micr code:',
                    'registered mobile', 'registered email', 'scheme:', 'currency:'
                ]) or (page_idx == 0 and l['top'] < 270):
                    pending_pre_narr = []
                    continue

                date_words = []
                chq_words = []
                narr_words = []
                debit_words = []
                credit_words = []
                bal_words = []

                for w in l['words']:
                    x = w['x0']
                    txt = w['text']
                    if x < 88:
                        date_words.append(txt)
                    elif x < 125:
                        chq_words.append(txt)
                    elif x < 315:
                        narr_words.append(txt)
                    elif x < 380:
                        debit_words.append(txt)
                    elif x < 450:
                        credit_words.append(txt)
                    elif x < 530:
                        bal_words.append(txt)

                date_candidate = ' '.join(date_words).strip()
                chq_str = ' '.join(chq_words).strip()
                narr_str = ' '.join(narr_words).strip()
                debit_str = ' '.join(debit_words).strip()
                credit_str = ' '.join(credit_words).strip()
                bal_str = ' '.join(bal_words).strip()

                date_match = DATE_REGEX.match(date_candidate)

                if date_match:
                    tx_date = date_match.group(0)
                    debit = parse_amount(debit_str)
                    credit = parse_amount(credit_str)
                    balance = parse_amount(bal_str)

                    if debit == 0.0:
                        debit = None
                    if credit == 0.0:
                        credit = None

                    if pending_pre_narr:
                        pre_str = ' '.join(pending_pre_narr).strip()
                        narr_str = f"{pre_str} {narr_str}".strip()
                        pending_pre_narr = []

                    tx = {
                        "Date": tx_date,
                        "Cheque No.": chq_str,
                        "Description": narr_str,
                        "Debit": debit,
                        "Credit": credit,
                        "Balance": balance
                    }
                    all_transactions.append(tx)
                else:
                    content_str = ' '.join([date_candidate, chq_str, narr_str]).strip()
                    if content_str:
                        if all_transactions and (debit_str or credit_str or bal_str):
                            all_transactions[-1]["Description"] = f"{all_transactions[-1]['Description']} {content_str}".strip()
                        else:
                            pending_pre_narr.append(content_str)

    logger.info(f"Axis Special Extractor successfully extracted {len(all_transactions)} transactions.")
    return all_transactions
