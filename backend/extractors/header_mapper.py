"""
Header Mapper and Alias Dictionary
Maps extracted column headers to standardized internal field names.
"""
import re
from typing import Dict, List, Optional

COLUMN_ALIASES = {
    "Date": [
        r"date", r"txn\s*date", r"trans\s*date", r"value\s*date", r"post\s*date", r"posting\s*date"
    ],
    "Description": [
        r"description", r"narration", r"particulars", r"transaction\s*details", r"details", r"remarks", r"description\s*/\s*narration"
    ],
    "Cheque No": [
        r"chq\s*/\s*ref", r"chq\s*no", r"cheque\s*no", r"cheque\s*number", r"cheque\s*/\s*ref", r"chq"
    ],
    "Ref No": [
        r"ref\s*no", r"reference\s*no", r"reference\s*number", r"utr", r"utrn", r"txn\s*ref", r"ref"
    ],
    "Debit": [
        r"withdrawal", r"withdrawals", r"debit", r"debits", r"dr", r"dr\."
    ],
    "Credit": [
        r"deposit", r"deposits", r"credit", r"credits", r"cr", r"cr\."
    ],
    "Balance": [
        r"balance", r"running\s*balance", r"closing\s*balance", r"bal"
    ],
    "Index": [
        r"^#$", r"^s\.?\s*no\.?$", r"^sl\.?\s*no\.?$", r"^serial"
    ]
}

def map_column_name(header_text: str) -> Optional[str]:
    """
    Matches raw header text against regex patterns to identify standardized field name.
    """
    clean_text = header_text.strip().lower()
    if not clean_text:
        return None

    # Specific check for combined Chq/Ref. No.
    if ("chq" in clean_text or "cheque" in clean_text) and ("ref" in clean_text or "utr" in clean_text):
        return "Chq/Ref No"

    for standard_name, patterns in COLUMN_ALIASES.items():
        for pattern in patterns:
            if re.search(r'\b' + pattern + r'\b', clean_text, re.IGNORECASE) or pattern in clean_text:
                return standard_name

    return None

def identify_table_headers(row_cells: List[str]) -> Dict[int, str]:
    """
    Scans a candidate header row and maps column index -> standardized field name.
    """
    mapped_headers = {}
    for idx, cell in enumerate(row_cells):
        mapped = map_column_name(str(cell))
        if mapped:
            mapped_headers[idx] = mapped
    return mapped_headers
