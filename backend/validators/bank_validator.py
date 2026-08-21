"""
Transaction Validator
Rule: Balance(prev) + Credit - Debit ≈ Balance(curr)
Marks invalid rows as "Validation Failed" without modifying values automatically.
"""
from typing import List, Dict, Any, Tuple

def validate_transactions(transactions: List[Dict[str, Any]], tolerance: float = 0.05) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Validates arithmetic running balance integrity.
    """
    if not transactions:
        return [], {"total_count": 0, "valid_count": 0, "failed_count": 0, "opening_balance": 0.0, "closing_balance": 0.0, "total_debit": 0.0, "total_credit": 0.0}

    valid_count = 0
    failed_count = 0
    total_debit = 0.0
    total_credit = 0.0

    opening_balance = 0.0
    closing_balance = 0.0

    # Determine opening balance from first row if present
    for i, tx in enumerate(transactions):
        d_val = float(tx.get("Debit") or 0.0)
        c_val = float(tx.get("Credit") or 0.0)
        b_val = tx.get("Balance")

        total_debit += d_val
        total_credit += c_val

        if i == 0 and b_val is not None:
            opening_balance = float(b_val)
        
        if i == len(transactions) - 1 and b_val is not None:
            closing_balance = float(b_val)

        # Validate sequence if previous balance is present
        if i > 0:
            prev_b = transactions[i-1].get("Balance")
            curr_b = tx.get("Balance")

            if prev_b is not None and curr_b is not None:
                expected_curr = float(prev_b) + c_val - d_val
                actual_curr = float(curr_b)

                if abs(expected_curr - actual_curr) > tolerance:
                    tx["Validation Status"] = "Validation Failed"
                    failed_count += 1
                else:
                    tx["Validation Status"] = "OK"
                    valid_count += 1
            else:
                tx["Validation Status"] = "OK"
                valid_count += 1
        else:
            tx["Validation Status"] = "OK"
            valid_count += 1

    summary = {
        "total_count": len(transactions),
        "valid_count": valid_count,
        "failed_count": failed_count,
        "opening_balance": opening_balance,
        "closing_balance": closing_balance,
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2)
    }

    return transactions, summary
