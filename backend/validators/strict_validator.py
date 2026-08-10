"""
Strict Validation Engine
Enforces 11 strict validation rules, row confidence scoring, and granular validation status tags:
- PASS
- LOW CONFIDENCE
- RECONSTRUCTED
- FAILED VALIDATION
- MISSING DATA
- DUPLICATE
- BALANCE MISMATCH
"""
import re
from typing import List, Dict, Any, Tuple
from backend.utils.logger import logger

DATE_PATTERN = re.compile(
    r'\b(\d{1,2}[\s\/\.-]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\/\.-]+\d{2,4}|\d{1,4}[\/\.-]\d{1,2}[\/\.-]\d{1,4})\b',
    re.IGNORECASE
)

HEADER_FOOTER_PATTERNS = [
    r'opening\s+balance',
    r'closing\s+balance',
    r'statement\s+of\s+account',
    r'page\s+\d+\s+of\s+\d+',
    r'account\s+number',
    r'cheque\s+no',
    r'date\s+particulars',
    r'value\s+date',
    r'transaction\s+details',
    r'b/f',
    r'c/f',
    r'carried\s+forward',
    r'brought\s+forward'
]

def is_header_or_footer(desc: str, has_date: bool = False, has_amount: bool = False) -> bool:
    """Rule 11: Header / Footer / Balance Summary Exclusion"""
    if has_date and has_amount:
        return False
    clean_desc = (desc or "").strip().lower()
    for pat in HEADER_FOOTER_PATTERNS:
        if re.search(pat, clean_desc):
            return True
    return False

def validate_row_rules(tx: Dict[str, Any], prev_balance: float = None, tolerance: float = 0.05) -> Tuple[str, str, Dict[str, Any]]:
    """
    Evaluates individual transaction row against strict validation rules.
    Returns (Status, Confidence, Details).
    """
    date_val = str(tx.get("Date") or "").strip()
    desc_val = str(tx.get("Description") or "").strip()
    debit = tx.get("Debit")
    credit = tx.get("Credit")
    balance = tx.get("Balance")

    has_valid_date = bool(DATE_PATTERN.search(date_val)) if date_val else False
    has_amount = debit is not None or credit is not None

    # Rule 11: Header/Footer/Opening Balance check
    if is_header_or_footer(desc_val, has_valid_date, has_amount):
        return "HEADER_FOOTER_EXCLUDED", "Low", {"reason": "Header or footer row"}

    # Rule 6: Row containing ONLY date
    if date_val and not desc_val and debit is None and credit is None and balance is None:
        return "MISSING DATA", "Low", {"reason": "Only date present"}

    # Rule 7: Row containing ONLY balance
    if balance is not None and not date_val and not desc_val and debit is None and credit is None:
        return "MISSING DATA", "Low", {"reason": "Only balance present"}

    # Rule 3: Description cannot be empty
    if not desc_val:
        return "MISSING DATA", "Low", {"reason": "Empty description"}

    # Rule 4: Valid date format check
    if not has_valid_date:
        return "MISSING DATA", "Low", {"reason": "Invalid or missing date"}

    # Rule 5: Numeric balance check
    if balance is None or not isinstance(balance, (int, float)):
        return "MISSING DATA", "Low", {"reason": "Balance non-numeric or missing"}

    # Rule 2: Date, Description, Balance, and Debit OR Credit required
    if not has_amount:
        return "MISSING DATA", "Low", {"reason": "Debit or Credit missing"}

    # Rule 11 / Balance Mismatch check against previous balance
    if prev_balance is not None:
        d_val = float(debit or 0.0)
        c_val = float(credit or 0.0)
        expected_bal = prev_balance + c_val - d_val
        actual_bal = float(balance)

        if abs(expected_bal - actual_bal) > tolerance:
            return "BALANCE MISMATCH", "Low", {
                "expected": round(expected_bal, 2),
                "actual": actual_bal,
                "diff": round(actual_bal - expected_bal, 2)
            }

    # High / Pass
    confidence = "High" if has_valid_date and has_amount else "Medium"
    status = "PASS" if confidence == "High" else "LOW CONFIDENCE"

    return status, confidence, {}

def validate_and_enrich_transactions(
    raw_transactions: List[Dict[str, Any]],
    tolerance: float = 0.05
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Applies all 11 validation rules across full dataset.
    Adds `Sr No.` and `Validation Status`.
    Computes overall extraction score and rejection criteria (Rule 8).
    """
    if not raw_transactions:
        return [], {
            "total_count": 0,
            "pass_count": 0,
            "failed_count": 0,
            "incomplete_rate": 100.0,
            "is_valid": False,
            "rejection_reason": "No transactions extracted"
        }

    enriched_transactions = []
    seen_hashes = set()
    duplicate_count = 0
    incomplete_count = 0
    balance_mismatches = 0
    prev_balance = None
    sr_no = 1

    total_debit = 0.0
    total_credit = 0.0
    opening_balance = 0.0
    closing_balance = 0.0

    for i, tx in enumerate(raw_transactions):
        desc = str(tx.get("Description") or "").strip()
        date_str = str(tx.get("Date") or "").strip()
        debit = tx.get("Debit")
        credit = tx.get("Credit")
        balance = tx.get("Balance")

        has_valid_date = bool(DATE_PATTERN.search(date_str)) if date_str else False
        has_amount = debit is not None or credit is not None

        # Skip header/footer noise rows (Rule 11)
        if is_header_or_footer(desc, has_valid_date, has_amount):
            continue

        d_val = float(debit or 0.0)
        c_val = float(credit or 0.0)
        b_val = float(balance) if balance is not None else None

        total_debit += d_val
        total_credit += c_val

        if sr_no == 1 and b_val is not None:
            opening_balance = b_val
        if b_val is not None:
            closing_balance = b_val

        # Rule 9: Duplicate detection
        tx_hash = f"{date_str}|{desc[:25]}|{debit}|{credit}|{balance}"
        is_duplicate = tx_hash in seen_hashes
        seen_hashes.add(tx_hash)

        # Validate row
        status, confidence, details = validate_row_rules(tx, prev_balance, tolerance)

        if is_duplicate:
            status = "DUPLICATE"
            duplicate_count += 1

        if status in ["MISSING DATA", "FAILED VALIDATION"]:
            incomplete_count += 1

        if status == "BALANCE MISMATCH":
            balance_mismatches += 1

        if b_val is not None and status != "BALANCE MISMATCH":
            prev_balance = b_val

        # Enrich transaction dict
        enriched_tx = dict(tx)
        enriched_tx["Sr No."] = sr_no
        enriched_tx["Validation Status"] = status
        enriched_tx["Confidence"] = confidence
        enriched_tx["Validation Details"] = details
        enriched_transactions.append(enriched_tx)

        sr_no += 1

    total_rows = len(enriched_transactions)
    incomplete_rate = (incomplete_count / total_rows * 100.0) if total_rows > 0 else 100.0

    # Rule 8: Reject extraction if > 2% rows are incomplete
    is_valid = incomplete_rate <= 2.0 and total_rows > 0
    rejection_reason = ""
    if incomplete_rate > 2.0:
        rejection_reason = f"Rule 8 Violation: Incomplete row rate is {round(incomplete_rate, 1)}% (Limit: 2.0%)"

    summary = {
        "total_count": total_rows,
        "pass_count": sum(1 for t in enriched_transactions if t["Validation Status"] == "PASS"),
        "failed_count": incomplete_count,
        "duplicate_rows": duplicate_count,
        "balance_mismatches": balance_mismatches,
        "incomplete_rate": round(incomplete_rate, 2),
        "is_valid": is_valid,
        "rejection_reason": rejection_reason,
        "opening_balance": round(opening_balance, 2),
        "closing_balance": round(closing_balance, 2),
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2)
    }

    return enriched_transactions, summary
