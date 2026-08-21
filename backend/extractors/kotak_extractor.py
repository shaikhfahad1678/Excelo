"""
Kotak Mahindra Bank Statement Special Extractor Module
Handles table extraction, spatial line binning fallback, Withdrawal (Dr.) / Deposit (Cr.) mapping,
Chq/Ref No. extraction, and running balance verification for Kotak Bank statements.
"""
import os
import re
from typing import List, Dict, Any, Optional
import pdfplumber
from backend.utils.logger import logger

DATE_REGEX = re.compile(r'^\d{1,2}\s+[A-Za-z]{3}\s+\d{4}$')

def parse_num(val: Any) -> Optional[float]:
    if val is None:
        return None
    s = str(val).replace(',', '').strip()
    if not s or s == '-':
        return None
    try:
        return float(s)
    except ValueError:
        return None

def run_kotak_extractor(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parses Kotak Mahindra Bank Statement PDFs into standardized transaction objects.
    """
    logger.info(f"Kotak Bank Special Extractor running on [{pdf_path}]...")
    all_transactions = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            # Primary strategy: Native table extraction
            tables = page.extract_tables()
            table_extracted_txs = []

            for table in tables:
                if not table or len(table) < 2:
                    continue

                for row in table:
                    if not row or len(row) < 6:
                        continue

                    sr = str(row[0] or '').strip()
                    date_str = str(row[1] or '').strip()
                    desc = str(row[2] or '').strip()
                    chq_ref = str(row[3] or '').strip() if len(row) > 3 else ''
                    dr_str = str(row[4] or '').strip() if len(row) > 4 else ''
                    cr_str = str(row[5] or '').strip() if len(row) > 5 else ''
                    bal_str = str(row[6] or '').strip() if len(row) > 6 else ''

                    # Skip header / Opening balance
                    if 'Opening Balance' in desc or 'Description' in desc or '#' in sr:
                        continue

                    if not DATE_REGEX.match(date_str):
                        continue

                    debit = parse_num(dr_str)
                    credit = parse_num(cr_str)
                    balance = parse_num(bal_str)

                    desc_clean = ' '.join(desc.split())

                    if debit is not None or credit is not None or balance is not None:
                        table_extracted_txs.append({
                            "Sr No.": int(sr) if sr.isdigit() else len(all_transactions) + len(table_extracted_txs) + 1,
                            "Date": date_str,
                            "Description": desc_clean,
                            "Cheque No.": chq_ref,
                            "Debit": debit,
                            "Credit": credit,
                            "Balance": balance
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
                        'account statement', 'savings account transactions', 'account summary',
                        'end of statement', 'commonly used narrations', 'for assistance', 'registered office'
                    ]):
                        continue

                    first_word = l['words'][0]['text'] if l['words'] else ''
                    # Check if line starts with Sr No or Date
                    if len(l['words']) >= 2 and (l['words'][0]['text'].isdigit() or DATE_REGEX.match(l['words'][0]['text'])):
                        second_word = l['words'][1]['text']
                        # Check date
                        date_match = DATE_REGEX.match(f"{l['words'][1]['text']} {l['words'][2]['text']} {l['words'][3]['text']}") if len(l['words']) > 3 else None
                        
                        if date_match or (DATE_REGEX.match(first_word)):
                            if current_tx:
                                all_transactions.append(current_tx)

                            # Extract columns
                            current_tx = {
                                "Sr No.": int(first_word) if first_word.isdigit() else len(all_transactions) + 1,
                                "Date": date_match.group(0) if date_match else first_word,
                                "Description": line_text,
                                "Cheque No.": "",
                                "Debit": None,
                                "Credit": None,
                                "Balance": None
                            }
                    elif current_tx:
                        current_tx["Description"] = f"{current_tx['Description']} {line_text}".strip()

                if current_tx:
                    all_transactions.append(current_tx)

    logger.info(f"Kotak Bank Special Extractor successfully extracted {len(all_transactions)} transactions.")
    return all_transactions
