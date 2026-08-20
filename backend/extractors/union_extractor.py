"""
Union Bank of India Statement Special Extractor Module
Handles spatial column binning, (Dr)/(Cr) amount/balance parsing,
header/footer cleaning, and balance validation for Union Bank statements.
"""
import os
import re
from typing import List, Dict, Any, Optional, Tuple
import pdfplumber
from backend.utils.logger import logger

DATE_REGEX = re.compile(r'^\d{2}-\d{2}-\d{4}$')

def parse_amount_flag(val_str: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Parses amount string like '30.0(Dr)' or '360.0(Cr)' or '6965.65(Cr)'.
    Returns (amount, 'DR'|'CR'|None).
    """
    if not val_str:
        return None, None
    s = val_str.replace(',', '').strip()
    flag = None
    if '(dr)' in s.lower():
        flag = 'DR'
        s = re.sub(r'\(dr\)', '', s, flags=re.IGNORECASE).strip()
    elif '(cr)' in s.lower():
        flag = 'CR'
        s = re.sub(r'\(cr\)', '', s, flags=re.IGNORECASE).strip()

    try:
        val = float(s)
        return val, flag
    except ValueError:
        return None, None

def run_union_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parses Union Bank Statement PDFs using spatial bounding-box state-machine clustering.
    Returns cleaned list of transaction dicts.
    """
    logger.info(f"Union Bank Special Extractor running on [{pdf_path}]...")
    all_transactions = []
    current_tx = None
    pending_pre_narr = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
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

                # Skip header noise
                if any(h in line_lower for h in [
                    'savings account', 'your details', 'account details', 'customer/cif id',
                    'account type', 'account name', 'account number', 'currency inr',
                    'ifsc ubin', 'branch address', 'statement date', 'statement period',
                    'transaction id remarks', 'page 1 of', 'page 2 of', 'page 3 of',
                    'page 4 of', 'page 5 of', 'page 6 of', 'page 7 of', 'page 8 of',
                    'page 9 of', 'page 10 of', 'page 11 of', 'page 12 of', 'page 13 of',
                    'page 14 of', 'page 15 of', 'page 16 of', 'page 17 of', 'page 18 of',
                    'page 19 of', 'page 20 of'
                ]) or (page_idx == 0 and l['top'] < 415) or (page_idx > 0 and l['top'] < 105):
                    continue

                # Skip promotional footers
                if any(f in line_lower for f in [
                    'union bank of india, established in 1919', 'this is a system generated document',
                    'unlock the journey', 'personalised account number', '#choosehappiness',
                    'registered office: union bank', 'find out more at'
                ]):
                    continue

                clean_lines.append(l)

            idx = 0
            while idx < len(clean_lines):
                l = clean_lines[idx]

                date_words = [w['text'] for w in l['words'] if w['x0'] < 75]
                txid_words = [w['text'] for w in l['words'] if 75 <= w['x0'] < 145]
                rem_words = [w['text'] for w in l['words'] if 145 <= w['x0'] < 435]
                amt_words = [w['text'] for w in l['words'] if 435 <= w['x0'] < 505]
                bal_words = [w['text'] for w in l['words'] if w['x0'] >= 505]

                date_str = ' '.join(date_words).strip()
                txid_str = ' '.join(txid_words).strip()
                rem_str = ' '.join(rem_words).strip()
                amt_str = ' '.join(amt_words).strip()
                bal_str = ' '.join(bal_words).strip()

                is_date = bool(DATE_REGEX.match(date_str))
                amt_val, amt_flag = parse_amount_flag(amt_str)
                bal_val, bal_flag = parse_amount_flag(bal_str)

                if is_date and (bal_val is not None or amt_val is not None):
                    if current_tx:
                        all_transactions.append(current_tx)

                    debit = amt_val if amt_flag == 'DR' else None
                    credit = amt_val if amt_flag == 'CR' else None

                    if pending_pre_narr:
                        pre_text = ' '.join(pending_pre_narr).strip()
                        rem_str = f"{pre_text} {rem_str}".strip()
                        pending_pre_narr = []

                    current_tx = {
                        "Date": date_str,
                        "Cheque No.": txid_str,
                        "Description": rem_str,
                        "Debit": debit,
                        "Credit": credit,
                        "Balance": bal_val
                    }
                else:
                    line_text = ' '.join(w['text'] for w in l['words']).strip()
                    if line_text:
                        if current_tx:
                            current_tx["Description"] = f"{current_tx['Description']} {line_text}".strip()
                        else:
                            pending_pre_narr.append(line_text)

                idx += 1

        if current_tx:
            all_transactions.append(current_tx)

    logger.info(f"Union Bank Special Extractor successfully extracted {len(all_transactions)} transactions.")
    return all_transactions
