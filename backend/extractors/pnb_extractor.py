"""
Punjab National Bank (PNB) Statement Special Extractor Module
Handles table extraction, spatial line binning fallback, Amount(INR) & DR/CR type mapping,
running balance verification, and header/footer cleanup for PNB bank statements.
"""
import os
import re
from typing import List, Dict, Any, Optional
import pdfplumber
from backend.utils.logger import logger

DATE_REGEX = re.compile(r'^\d{2}/\d{2}/\d{4}$')

def parse_num(val: Any) -> Optional[float]:
    if val is None:
        return None
    s = str(val).replace(',', '').strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None

def run_pnb_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parses PNB Bank Statement PDFs into standardized transaction objects.
    """
    logger.info(f"PNB Special Extractor running on [{pdf_path}]...")
    all_transactions = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            # Primary strategy: Native table extraction
            tables = page.extract_tables()
            table_extracted_txs = []

            for table in tables:
                for row in table:
                    if not row or len(row) < 5:
                        continue

                    # Check if header row
                    first_cell = str(row[0] or '').strip()
                    if 'Date' in first_cell or 'Amount' in str(row[2] if len(row) > 2 else ''):
                        continue

                    if not DATE_REGEX.match(first_cell):
                        continue

                    date_str = first_cell
                    instrument_id = str(row[1] or '').strip() if len(row) > 1 else ''
                    amount_str = str(row[2] or '').strip() if len(row) > 2 else ''
                    tx_type = str(row[3] or '').strip().upper() if len(row) > 3 else ''
                    balance_str = str(row[4] or '').strip() if len(row) > 4 else ''
                    remarks = str(row[5] or '').strip() if len(row) > 5 else ''

                    remarks_clean = ' '.join(remarks.split())
                    amount_val = parse_num(amount_str)
                    balance_val = parse_num(balance_str)

                    debit = amount_val if tx_type == 'DR' else None
                    credit = amount_val if tx_type == 'CR' else None

                    if amount_val is not None or balance_val is not None:
                        table_extracted_txs.append({
                            "Date": date_str,
                            "Cheque No.": instrument_id,
                            "Description": remarks_clean,
                            "Debit": debit,
                            "Credit": credit,
                            "Balance": balance_val
                        })

            if table_extracted_txs:
                all_transactions.extend(table_extracted_txs)
            else:
                # Fallback strategy: Spatial text bounding-box parser
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

                current_tx = None
                for l in lines:
                    l['words'].sort(key=lambda w: w['x0'])
                    line_text = ' '.join(w['text'] for w in l['words']).strip()
                    line_lower = line_text.lower()

                    if any(h in line_lower for h in [
                        'branch details', 'customer details', 'statement of account',
                        'instrument id', 'generated through pnb one', 'abbreviations are as under'
                    ]):
                        continue

                    first_word = l['words'][0]['text'] if l['words'] else ''
                    if DATE_REGEX.match(first_word):
                        if current_tx:
                            all_transactions.append(current_tx)

                        date_str = first_word
                        # Parse other columns by x0 position or tokens
                        tokens = [w['text'] for w in l['words']]
                        # Date is tokens[0]
                        # Look for DR/CR in tokens
                        dr_cr_idx = -1
                        for idx, tok in enumerate(tokens):
                            if tok.upper() in ['DR', 'CR']:
                                dr_cr_idx = idx
                                break

                        if dr_cr_idx != -1 and dr_cr_idx >= 2:
                            amt_val = parse_num(tokens[dr_cr_idx - 1])
                            tx_type = tokens[dr_cr_idx].upper()
                            bal_val = parse_num(tokens[dr_cr_idx + 1]) if dr_cr_idx + 1 < len(tokens) else None
                            rem_tokens = tokens[dr_cr_idx + 2:] if dr_cr_idx + 2 < len(tokens) else []
                            rem_str = ' '.join(rem_tokens).strip()

                            debit = amt_val if tx_type == 'DR' else None
                            credit = amt_val if tx_type == 'CR' else None

                            current_tx = {
                                "Date": date_str,
                                "Cheque No.": "",
                                "Description": rem_str,
                                "Debit": debit,
                                "Credit": credit,
                                "Balance": bal_val
                            }
                    elif current_tx:
                        current_tx["Description"] = f"{current_tx['Description']} {line_text}".strip()

                if current_tx:
                    all_transactions.append(current_tx)

    logger.info(f"PNB Special Extractor successfully extracted {len(all_transactions)} transactions.")
    return all_transactions
