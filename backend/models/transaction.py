"""
Transaction Data Model
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class Transaction:
    date: str = ""
    description: str = ""
    cheque_no: str = ""
    ref_no: str = ""
    debit: Optional[float] = None
    credit: Optional[float] = None
    balance: Optional[float] = None
    currency: str = ""
    is_valid: bool = True
    validation_status: str = "OK"
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Date": self.date,
            "Description": self.description,
            "Cheque No.": self.cheque_no,
            "Ref No.": self.ref_no,
            "Debit": self.debit if self.debit is not None else "",
            "Credit": self.credit if self.credit is not None else "",
            "Balance": self.balance if self.balance is not None else "",
            "Currency": self.currency,
            "Validation Status": self.validation_status
        }
