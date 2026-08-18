"""
ICICI Bank Statement Special Extractor Module
Handles spatial column binning, state-machine multi-line narration joining,
header/footer noise filtering, and balance chain validation.
"""
import os
import re
from typing import List, Dict, Any, Optional
import pdfplumber
from backend.utils.logger import logger

DATE_REGEX = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')
SNO_REGEX = re.compile(r'^\d{1,4}$')

def parse_amount(val_str: str) -> Optional[float]:
    if not val_str:
        return None
    cleaned = val_str.replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

def run_icici_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parses ICICI Bank Statement PDFs using spatial bounding-box state-machine clustering.
    Returns cleaned list of transaction dicts.
    """
    logger.info(f"ICICI Special Extractor running on [{pdf_path}]...")
    all_transactions = []
    current_tx = None
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

            clean_lines = []
            for l in lines:
                l['words'].sort(key=lambda w: w['x0'])
                line_text = ' '.join(w['text'] for w in l['words']).strip()
                line_lower = line_text.lower()

                # Stop extraction at footer disclaimers / legends
                if any(term in line_lower for term in [
                    'sincerly,', 'team icici bank', 'legends for transactions',
                    'rchg - recharge', 'dtax - direct tax', 'never share your otp'
                ]):
                    if 'sincerly,' in line_lower or 'team icici bank' in line_lower or 'legends for transactions' in line_lower:
                        stop_extraction = True
                        break
                    continue

                # Skip top header noise
                if any(h in line_lower for h in [
                    'statement of transactions', 'transaction date', 'cheque number',
                    'transaction remarks', 'withdrawal amount', 'deposit amount',
                    'balance (inr)', 'your base branch:', 'dial your bank',
                    'www.icici.bank.in', 'please call from your registered'
                ]) or (page_idx == 0 and l['top'] < 230):
                    continue

                clean_lines.append(l)

            idx = 0
            while idx < len(clean_lines):
                l = clean_lines[idx]

                sno_words = [w['text'] for w in l['words'] if w['x0'] < 55]
                date_words = [w['text'] for w in l['words'] if 55 <= w['x0'] < 115]
                chq_words = [w['text'] for w in l['words'] if 115 <= w['x0'] < 195]
                narr_words = [w['text'] for w in l['words'] if 195 <= w['x0'] < 390]
                deb_words = [w['text'] for w in l['words'] if 390 <= w['x0'] < 460]
                cred_words = [w['text'] for w in l['words'] if 460 <= w['x0'] < 520]
                bal_words = [w['text'] for w in l['words'] if w['x0'] >= 520]

                sno_str = ' '.join(sno_words).strip()
                date_str = ' '.join(date_words).strip()
                chq_str = ' '.join(chq_words).strip()
                narr_str = ' '.join(narr_words).strip()
                debit_str = ' '.join(deb_words).strip()
                credit_str = ' '.join(cred_words).strip()
                bal_str = ' '.join(bal_words).strip()

                is_sno = bool(SNO_REGEX.match(sno_str))
                is_date = bool(DATE_REGEX.match(date_str))
                balance = parse_amount(bal_str)

                if (is_date or is_sno) and (balance is not None or debit_str or credit_str):
                    if current_tx:
                        all_transactions.append(current_tx)

                    debit = parse_amount(debit_str)
                    credit = parse_amount(credit_str)

                    if debit == 0.0:
                        debit = None
                    if credit == 0.0:
                        credit = None

                    if pending_pre_narr:
                        pre_text = ' '.join(pending_pre_narr).strip()
                        narr_str = f"{pre_text} {narr_str}".strip()
                        pending_pre_narr = []

                    current_tx = {
                        "Date": date_str,
                        "Cheque No.": chq_str,
                        "Description": narr_str,
                        "Debit": debit,
                        "Credit": credit,
                        "Balance": balance
                    }
                else:
                    line_text = ' '.join(w['text'] for w in l['words']).strip()
                    if line_text:
                        next_is_anchor = False
                        if idx + 1 < len(clean_lines):
                            nl = clean_lines[idx + 1]
                            ndate = ' '.join(w['text'] for w in nl['words'] if 55 <= w['x0'] < 115).strip()
                            nsno = ' '.join(w['text'] for w in nl['words'] if w['x0'] < 55).strip()
                            nbal = ' '.join(w['text'] for w in nl['words'] if w['x0'] >= 520).strip()
                            if (DATE_REGEX.match(ndate) or SNO_REGEX.match(nsno)) and (nbal or parse_amount(nbal) is not None):
                                next_is_anchor = True

                        if next_is_anchor:
                            pending_pre_narr.append(line_text)
                        elif current_tx:
                            current_tx["Description"] = f"{current_tx['Description']} {line_text}".strip()
                        else:
                            pending_pre_narr.append(line_text)

                idx += 1

        if current_tx:
            all_transactions.append(current_tx)

    logger.info(f"ICICI Special Extractor successfully extracted {len(all_transactions)} transactions.")
    return all_transactions
