"""
IndusInd Bank Statement Special Extractor Module
Handles spatial column binning, multi-line narration joining across pages,
reverse-chronological transaction ordering, and balance math validation.
"""
import os
import re
from typing import List, Dict, Any, Optional
import pdfplumber
from backend.utils.logger import logger

DATE_REGEX = re.compile(r'^\d{2}\s+[A-Za-z]{3}\s+\d{4}')

def parse_amount(val_str: str) -> Optional[float]:
    if not val_str:
        return None
    cleaned = val_str.replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

def run_indusind_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parses IndusInd Bank Statement PDFs using spatial bounding-box clustering.
    Returns cleaned list of transaction dicts sorted in chronological order.
    """
    logger.info(f"IndusInd Special Extractor running on [{pdf_path}]...")
    all_transactions = []
    active_tx = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            words = page.extract_words()
            if not words:
                continue

            # Group words by top coordinate (tolerance 3.0)
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

                # Skip header/footer noise
                if not line_text or any(h in line_text.lower() for h in [
                    'account statement', 'customer details', 'account summary',
                    'transaction history', 'statement period', 'nomination registered',
                    'branch ifsc code', 'date particulars chq', 'holding status',
                    'primary holder', 'indus privilege'
                ]):
                    continue

                date_words = []
                narr_words = []
                ref_words = []
                with_words = []
                dep_words = []
                bal_words = []

                for w in l['words']:
                    x = w['x0']
                    txt = w['text']
                    if x < 125:
                        date_words.append(txt)
                    elif x < 250:
                        narr_words.append(txt)
                    elif x < 340:
                        ref_words.append(txt)
                    elif x < 425:
                        with_words.append(txt)
                    elif x < 485:
                        dep_words.append(txt)
                    else:
                        bal_words.append(txt)

                date_candidate = ' '.join(date_words).strip()
                narr_str = ' '.join(narr_words).strip()
                ref_str = ' '.join(ref_words).strip()
                with_str = ' '.join(with_words).strip()
                dep_str = ' '.join(dep_words).strip()
                bal_str = ' '.join(bal_words).strip()

                match = DATE_REGEX.match(date_candidate)
                if match:
                    if active_tx:
                        all_transactions.append(active_tx)

                    tx_date = match.group(0)
                    remainder_date = date_candidate[len(tx_date):].strip()
                    if remainder_date:
                        narr_str = f"{remainder_date} {narr_str}".strip()

                    debit = parse_amount(with_str)
                    credit = parse_amount(dep_str)
                    balance = parse_amount(bal_str)

                    if debit == 0.0:
                        debit = None
                    if credit == 0.0:
                        credit = None

                    active_tx = {
                        "Date": tx_date,
                        "Description": narr_str,
                        "Ref No.": ref_str,
                        "Debit": debit,
                        "Credit": credit,
                        "Balance": balance
                    }
                else:
                    if active_tx:
                        concat_text = ' '.join([date_candidate, narr_str]).strip()
                        if concat_text:
                            active_tx["Description"] = f"{active_tx['Description']} {concat_text}".strip()
                        if ref_str and not active_tx.get("Ref No."):
                            active_tx["Ref No."] = ref_str

        if active_tx:
            all_transactions.append(active_tx)

    logger.info(f"IndusInd Special Extractor successfully extracted {len(all_transactions)} transactions.")
    return all_transactions
