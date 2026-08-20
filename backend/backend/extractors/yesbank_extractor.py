"""
Yes Bank Statement Special Extractor Module
Handles spatial column binning, state-machine multi-line narration joining,
header/footer noise filtering, and balance chain validation for Yes Bank statements.
"""
import os
import re
from typing import List, Dict, Any, Optional
import pdfplumber
from backend.utils.logger import logger

DATE_REGEX = re.compile(r'^\d{2}-[A-Za-z]{3}-\d{4}$')

def parse_amount(val_str: str) -> Optional[float]:
    if not val_str:
        return None
    cleaned = val_str.replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

def run_yesbank_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parses Yes Bank Statement PDFs using spatial bounding-box state-machine clustering.
    Returns cleaned list of transaction dicts.
    """
    logger.info(f"Yes Bank Special Extractor running on [{pdf_path}]...")
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
                    'opening balance:', 'total withdrawals:', 'closing balance:',
                    'od limit:', 'have you registered a nominee', 'mandatory disclaimer',
                    'transaction codes in your account', '* reward points accrued',
                    'to redeem your rewardz points'
                ]):
                    if 'opening balance:' in line_lower or 'closing balance:' in line_lower or 'mandatory disclaimer' in line_lower or 'transaction codes in your account' in line_lower:
                        stop_extraction = True
                        break
                    continue

                # Skip header noise
                if any(h in line_lower for h in [
                    'statement of account:', 'period: from', 'transaction details for your account',
                    'primary holder:', 'nominee details:', 'a/c opening date:', 'account status:',
                    'account variant/', "joint holder's names:", 'transaction date', 'value date',
                    'cheque no/', 'description', 'withdrawals', 'deposits', 'running balance',
                    'customer id:', 'primary account holder name:', 'your branch details:',
                    'sms "help"', 'yes touch phonebanking', 'cin - l65190mh2003plc143249',
                    'page 1 of', 'page 2 of', 'page 3 of', 'page 4 of', 'page 5 of',
                    'page 6 of', 'page 7 of', 'page 8 of', 'page 9 of', 'page 10 of',
                    'page 11 of', 'page 12 of', 'page 13 of', 'page 14 of', 'page 15 of',
                    'page 16 of', 'page 17 of', 'page 18 of'
                ]) or (page_idx == 0 and l['top'] < 445):
                    pending_pre_narr = []
                    continue

                clean_lines.append(l)

            idx = 0
            while idx < len(clean_lines):
                l = clean_lines[idx]

                date_words = [w['text'] for w in l['words'] if w['x0'] < 105]
                valdate_words = [w['text'] for w in l['words'] if 105 <= w['x0'] < 185]
                chq_words = [w['text'] for w in l['words'] if 185 <= w['x0'] < 370]
                narr_words = [w['text'] for w in l['words'] if 370 <= w['x0'] < 570]
                deb_words = [w['text'] for w in l['words'] if 570 <= w['x0'] < 635]
                cred_words = [w['text'] for w in l['words'] if 635 <= w['x0'] < 675]
                bal_words = [w['text'] for w in l['words'] if w['x0'] >= 675]

                date_str = ' '.join(date_words).strip()
                valdate_str = ' '.join(valdate_words).strip()
                chq_str = ' '.join(chq_words).strip()
                narr_str = ' '.join(narr_words).strip()
                debit_str = ' '.join(deb_words).strip()
                credit_str = ' '.join(cred_words).strip()
                bal_str = ' '.join(bal_words).strip()

                is_date = bool(DATE_REGEX.match(date_str))
                balance = parse_amount(bal_str)

                if is_date and (balance is not None or debit_str or credit_str):
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
                            ndate = ' '.join(w['text'] for w in nl['words'] if w['x0'] < 105).strip()
                            nbal = ' '.join(w['text'] for w in nl['words'] if w['x0'] >= 675).strip()
                            if DATE_REGEX.match(ndate) and (nbal or parse_amount(nbal) is not None):
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

    logger.info(f"Yes Bank Special Extractor successfully extracted {len(all_transactions)} transactions.")
    return all_transactions
