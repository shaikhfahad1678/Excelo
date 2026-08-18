"""
Robust Table Normalizer & Multi-Line Row Reconstructor
Parses raw extracted grid rows into standardized transaction dictionaries.
Filters out pre-table header noise, metadata blocks, and page headers cleanly.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from backend.extractors.header_mapper import map_column_name, identify_table_headers
from backend.utils.logger import logger

# Date regex pattern supporting formats like 01 Jul 2026, 01/07/2026, 2026-07-01
DATE_REGEX = re.compile(
    r'^\s*(\d{1,2}[\s\/\.-]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\/\.-]+\d{2,4}|\d{1,4}[\/\.-]\d{1,2}[\/\.-]\d{1,4})\s*$',
    re.IGNORECASE
)

DATE_IN_LINE_REGEX = re.compile(
    r'\b(\d{1,2}[\s\/\.-]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\/\.-]+\d{2,4}|\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4}|\d{4}[\/\.-]\d{1,2}[\/\.-]\d{1,2})\b',
    re.IGNORECASE
)

HEADER_KEYWORDS = {"date", "description", "particulars", "narration", "withdrawal", "deposit", "debit", "credit", "balance", "chq", "ref"}

NOISE_KEYWORDS = [
    "statement of account", "page ", "page no", "savings account", "current account",
    "account summary", "opening balance", "closing balance", "carried forward",
    "brought forward", "total deposit", "total withdrawal", "net balance",
    "customer id", "cust id", "account number", "account no", "acc no", "ifsc code",
    "micr code", "branch address", "branch name", "statement period", "period from",
    "type of account", "scheme name", "nominee", "mode of operation",
    "gstin", "pan no", "bank ltd", "bank limited", "tax invoice",
    "generated on", "date of issue", "currency:", "address:", "email:",
    "phone:", "mobile:", "customer name", "fd summary", "overdraft limit",
    "rate of interest", "sanction limit", "drawing power", "interest rate",
    "account statement", "summary of account"
]

def parse_amount(val: Any) -> Optional[float]:
    """Cleans numeric string to float preserving decimal precision and negative values."""
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ["nil", "none", "-", "", "0.00", "0"]:
        if val_str in ["0.00", "0"]:
            return 0.0
        return None

    is_neg = False
    if val_str.startswith("(") and val_str.endswith(")"):
        is_neg = True
        val_str = val_str[1:-1]

    # Remove currency symbols and formatting commas
    cleaned = re.sub(r'[^\d.-]', '', val_str)
    try:
        f = float(cleaned)
        return -f if is_neg else f
    except ValueError:
        return None

def is_header_row(row_cells: List[str]) -> bool:
    match_count = 0
    for cell in row_cells:
        cell_lower = str(cell).strip().lower()
        if any(kw in cell_lower for kw in HEADER_KEYWORDS):
            match_count += 1
    return match_count >= 2

def is_noise_row(row_str: str) -> bool:
    lower = row_str.strip().lower()
    if not lower:
        return True
    
    # If line matches any pre-table noise keyword and lacks a transaction date, filter it out
    for kw in NOISE_KEYWORDS:
        if kw in lower:
            # Allow line if it contains a valid transaction date or numeric amount
            if not DATE_IN_LINE_REGEX.search(row_str):
                return True
    return False

def clean_and_normalize_table(raw_rows: List[List[Any]]) -> List[Dict[str, Any]]:
    """
    Cleans raw extracted grid rows:
    1. Identifies table header row and establishes column mappings.
    2. Filters out pre-table header noise & page top metadata.
    3. Merges multi-line descriptions into single transaction rows.
    4. Standardizes outputs.
    """
    if not raw_rows:
        return []

    # Find header row index and column mapping
    header_row_idx = None
    col_map = {} # col_idx -> standard_field_name

    for idx, row in enumerate(raw_rows[:25]):
        str_cells = [str(c or "").strip() for c in row]
        if is_header_row(str_cells):
            mapped = identify_table_headers(str_cells)
            if len(mapped) >= 2:
                header_row_idx = idx
                col_map = mapped
                break

    transactions = []
    current_tx = None

    start_idx = header_row_idx + 1 if header_row_idx is not None else 0

    for row in raw_rows[start_idx:]:
        str_cells = [str(c or "").strip() for c in row]
        row_text = " ".join([c for c in str_cells if c])

        if not row_text or is_noise_row(row_text) or is_header_row(str_cells):
            continue

        # Extract values using col_map if available, otherwise positional heuristics
        date_val = ""
        desc_val = ""
        cheque_val = ""
        ref_val = ""
        debit_val = None
        credit_val = None
        balance_val = None

        if col_map:
            # Explicit column mapping
            for c_idx, field_name in col_map.items():
                if c_idx < len(str_cells):
                    cell_str = str_cells[c_idx]
                    if field_name == "Date":
                        m = DATE_IN_LINE_REGEX.search(cell_str)
                        if m:
                            date_val = m.group(1)
                    elif field_name == "Description":
                        desc_val = cell_str
                    elif field_name in ["Cheque No", "Ref No", "Chq/Ref No"]:
                        if "UPI" in cell_str or "REF" in cell_str or "FOS" in cell_str or cell_str.isalnum():
                            ref_val = cell_str
                        else:
                            cheque_val = cell_str
                    elif field_name == "Debit":
                        debit_val = parse_amount(cell_str)
                    elif field_name == "Credit":
                        credit_val = parse_amount(cell_str)
                    elif field_name == "Balance":
                        balance_val = parse_amount(cell_str)
        else:
            # Heuristic mapping when col_map not detected
            for c in str_cells[:3]:
                m = DATE_IN_LINE_REGEX.search(c)
                if m:
                    date_val = m.group(1)
                    break

            amounts = []
            non_amounts = []
            for c in str_cells:
                if c == date_val:
                    continue
                amt = parse_amount(c)
                if amt is not None:
                    amounts.append(amt)
                elif c:
                    non_amounts.append(c)

            if len(amounts) >= 3:
                debit_val, credit_val, balance_val = amounts[0], amounts[1], amounts[2]
            elif len(amounts) == 2:
                debit_val, balance_val = amounts[0], amounts[1]
            elif len(amounts) == 1:
                balance_val = amounts[0]

            desc_val = " ".join(non_amounts)

        # Transaction Anchor Verification
        has_new_tx_anchors = bool(date_val) or debit_val is not None or credit_val is not None or balance_val is not None

        if has_new_tx_anchors:
            if current_tx:
                transactions.append(current_tx)

            current_tx = {
                "Date": date_val,
                "Description": desc_val.replace('\n', ' ').strip(),
                "Cheque No.": cheque_val,
                "Ref No.": ref_val,
                "Debit": debit_val,
                "Credit": credit_val,
                "Balance": balance_val,
                "Currency": ""
            }
        else:
            # Continuation line for multi-line description or reference
            if current_tx:
                # Filter out accidental page header noise appended mid-description
                if desc_val and not is_noise_row(desc_val):
                    current_tx["Description"] = (current_tx["Description"] + " " + desc_val.replace('\n', ' ')).strip()
                if ref_val and not current_tx["Ref No."]:
                    current_tx["Ref No."] = ref_val
                if cheque_val and not current_tx["Cheque No."]:
                    current_tx["Cheque No."] = cheque_val
                if debit_val is not None and current_tx["Debit"] is None:
                    current_tx["Debit"] = debit_val
                if credit_val is not None and current_tx["Credit"] is None:
                    current_tx["Credit"] = credit_val
                if balance_val is not None and current_tx["Balance"] is None:
                    current_tx["Balance"] = balance_val
            else:
                # Ignore pre-table header noise appearing before the first valid transaction anchor
                logger.debug(f"Discarded pre-table header line: {row_text}")

    if current_tx:
        transactions.append(current_tx)

    # Clean description spacing and validate transaction rows
    processed_transactions = []
    for tx in transactions:
        tx["Description"] = re.sub(r'\s+', ' ', tx.get("Description") or "").strip()
        
        has_valid_data = any([
            bool(tx.get("Date")),
            tx.get("Debit") is not None,
            tx.get("Credit") is not None,
            tx.get("Balance") is not None
        ])
        
        if has_valid_data:
            processed_transactions.append(tx)

    return processed_transactions
