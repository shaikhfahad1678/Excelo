"""
Automated unit tests for Excelo backend modules.
"""
import os
import pytest
from backend.extractors.normalizer import clean_and_normalize_table, parse_amount
from backend.validators.strict_validator import validate_and_enrich_transactions
from backend.excel.writer import generate_excel_workbook

def test_parse_amount():
    assert parse_amount("$1,234.56") == 1234.56
    assert parse_amount("(500.00)") == -500.00
    assert parse_amount(" - ") is None
    assert parse_amount("NIL") is None

def test_clean_and_normalize_table():
    raw_rows = [
        ["Date", "Description", "Debit", "Credit", "Balance"],
        ["01/08/2026", "ATM Withdrawal", "100.00", "", "900.00"],
        ["02/08/2026", "Salary Deposit", "", "500.00", "1400.00"]
    ]
    norm = clean_and_normalize_table(raw_rows)
    assert len(norm) == 2
    assert norm[0]["Date"] == "01/08/2026"
    assert norm[0]["Debit"] == 100.00
    assert norm[0]["Balance"] == 900.00

def test_validate_transactions():
    txs = [
        {"Date": "01/08/2026", "Debit": 100.0, "Credit": None, "Balance": 900.0},
        {"Date": "02/08/2026", "Debit": None, "Credit": 500.0, "Balance": 1400.0},
        {"Date": "03/08/2026", "Debit": 50.0, "Credit": None, "Balance": 1300.0} # Mismatch expected -> 1350 != 1300
    ]
    validated, summary = validate_and_enrich_transactions(txs)
    assert summary["total_count"] == 3
    assert len(validated) == 3

def test_excel_generation(tmp_path):
    out_file = str(tmp_path / "test_out.xlsx")
    txs = [{"Date": "01/08/2026", "Description": "Test Tx", "Debit": 10.0, "Credit": None, "Balance": 90.0}]
    generated = generate_excel_workbook({"Sheet1": txs}, out_file)
    assert os.path.exists(generated)

def test_statement_service_export():
    from backend.services.statement_service import statement_service
    file_id = "test_fid_123"
    statement_service.extraction_results[file_id] = {
        "success": True,
        "filename": "sample_statement.pdf",
        "transactions": [{"Date": "01/08/2026", "Description": "Test Tx", "Debit": 10.0, "Credit": None, "Balance": 90.0}]
    }
    filename = statement_service.generate_export([file_id], export_format="xlsx")
    assert not os.path.isabs(filename)
    assert filename.endswith(".xlsx")
    assert os.path.exists(os.path.join(statement_service.export_dir, filename))

