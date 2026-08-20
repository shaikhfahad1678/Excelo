"""
Professional Excel Generator (.xlsx) using openpyxl & pandas
Includes bold headers, Sr No. column, frozen top row, auto-fit column widths,
numeric/date formatting, and auto-filters.
"""
import re
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from backend.utils.logger import logger

import json
ILLEGAL_CHARACTERS_RE = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]')

def sanitize_value(val: Any) -> Any:
    if val is None:
        return ""
    if isinstance(val, (dict, list)):
        return json.dumps(val) if val else ""
    if isinstance(val, str):
        return ILLEGAL_CHARACTERS_RE.sub('', val)
    return val

def generate_excel_workbook(
    sheet_data_map: Dict[str, List[Dict[str, Any]]],
    output_filepath: str
) -> str:
    """
    Generates a professionally styled Excel workbook.
    Adds `Sr No.` as column 1 (numbered sequentially 1..N across all pages).
    `sheet_data_map` maps sheet names to list of transaction dicts.
    Excludes internal validation status and confidence columns for clean financial presentation.
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active) # Remove default sheet

    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Dark Navy Slate header
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    alt_row_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    global_sr_no = 1

    for sheet_name, transactions in sheet_data_map.items():
        safe_sheet_name = sheet_name[:30].replace("[", "").replace("]", "").replace("*", "").replace(":", "").replace("?", "").replace("/", "")
        ws = wb.create_sheet(title=safe_sheet_name or "Transactions")

        # Freeze top row
        ws.freeze_panes = "A2"

        # Dynamically discover all unique keys in the transactions excluding internal metadata
        all_keys = []
        for tx in transactions:
            for k in tx.keys():
                if k not in all_keys and k not in [
                    "Currency", "Sr No.", "Validation Status", "Validation Details",
                    "Confidence", "diagnostics", "is_valid", "confidence_score"
                ]:
                    all_keys.append(k)

        # Standard header priority ordering
        columns_order = ["Sr No."]
        std_keys = ["Date", "Description", "Cheque No.", "Ref No.", "Debit", "Credit", "Balance"]
        for k in std_keys:
            if k in all_keys:
                columns_order.append(k)
        for k in all_keys:
            if k not in columns_order:
                columns_order.append(k)

        # Write Header
        ws.append(columns_order)
        for col_num, col_name in enumerate(columns_order, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Write Data
        for row_idx, tx in enumerate(transactions, start=2):
            sr_num = tx.get("Sr No.") or global_sr_no

            row_data = [sr_num]
            for col_name in columns_order[1:]:
                row_data.append(sanitize_value(tx.get(col_name, "")))
            ws.append(row_data)
            global_sr_no += 1

            # Apply row styling & number formatting
            for col_idx in range(1, len(columns_order) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = thin_border

                if row_idx % 2 == 1:
                    cell.fill = alt_row_fill

                col_name = columns_order[col_idx - 1]
                if col_name in ["Debit", "Credit", "Balance"]:
                    if cell.value is not None and isinstance(cell.value, (int, float)):
                        cell.number_format = '#,##0.00'
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                elif col_name in ["Sr No.", "Date"]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")

        # Enable Auto-filters
        if len(transactions) > 0:
            last_col_letter = get_column_letter(len(columns_order))
            ws.auto_filter.ref = f"A1:{last_col_letter}{len(transactions) + 1}"

        # Auto-fit Column Widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or '')
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = min(max(max_len + 4, 10), 60)

    wb.save(output_filepath)
    logger.info(f"Excel workbook generated successfully without Validation Status column: {output_filepath}")
    return output_filepath

def generate_csv(transactions: List[Dict[str, Any]], output_filepath: str) -> str:
    """Exports transactions list to CSV file without internal validation columns."""
    cleaned_txs = []
    for tx in transactions:
        t = dict(tx)
        t.pop("Currency", None)
        t.pop("Validation Status", None)
        t.pop("Validation Details", None)
        t.pop("Confidence", None)
        t.pop("diagnostics", None)
        cleaned_txs.append(t)
    df = pd.DataFrame(cleaned_txs)
    df.to_csv(output_filepath, index=False)
    logger.info(f"CSV file generated without Validation Status: {output_filepath}")
    return output_filepath
