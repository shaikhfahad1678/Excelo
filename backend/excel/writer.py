"""
Professional Excel Generator (.xlsx) using openpyxl & pandas
Layout:
Row 1: Subtotal row (above Debit: sub total debit value; above Credit: sub total credit value)
Row 2: Header row (Sr No., Date, Description, Ledger, Debit, Credit, Balance)
Row 3+: Data rows with empty Ledger column, numeric formatting, thin borders, and auto-filters.
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
    Columns: Sr No., Date, Description, Ledger, Debit, Credit, Balance.
    Row 1: Subtotal row with Debit subtotal value above Debit column and Credit subtotal value above Credit column.
    Row 2: Header row.
    Row 3..N+2: Transaction data rows.
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active) # Remove default sheet

    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Dark Navy Slate header
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    subtotal_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid") # Soft Slate Subtotal fill
    subtotal_font = Font(name="Calibri", size=11, bold=True, color="0F172A")
    
    alt_row_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )
    
    subtotal_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='medium', color='94A3B8')
    )

    global_sr_no = 1

    for sheet_name, transactions in sheet_data_map.items():
        safe_sheet_name = sheet_name[:30].replace("[", "").replace("]", "").replace("*", "").replace(":", "").replace("?", "").replace("/", "")
        ws = wb.create_sheet(title=safe_sheet_name or "Transactions")

        # Freeze top 2 rows (Row 1 subtotal + Row 2 header)
        ws.freeze_panes = "A3"

        # Standard requested columns: Sr No., Date, Description, Ledger, Debit, Credit, Balance
        columns_order = ["Sr No.", "Date", "Description", "Ledger", "Debit", "Credit", "Balance"]

        # Calculate numeric subtotals for Debit and Credit
        total_debit = 0.0
        total_credit = 0.0
        for tx in transactions:
            d = tx.get("Debit")
            c = tx.get("Credit")
            if d is not None:
                try:
                    d_float = float(str(d).replace(',', ''))
                    total_debit += d_float
                except (ValueError, TypeError):
                    pass
            if c is not None:
                try:
                    c_float = float(str(c).replace(',', ''))
                    total_credit += c_float
                except (ValueError, TypeError):
                    pass

        # ----------------------------------------------------
        # ROW 1: Subtotal Row (above header)
        # ----------------------------------------------------
        row_1_values = []
        for col_name in columns_order:
            if col_name == "Debit":
                row_1_values.append(round(total_debit, 2) if total_debit > 0 else "")
            elif col_name == "Credit":
                row_1_values.append(round(total_credit, 2) if total_credit > 0 else "")
            else:
                row_1_values.append("")

        ws.append(row_1_values)

        for col_idx, col_name in enumerate(columns_order, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = subtotal_font
            cell.fill = subtotal_fill
            cell.border = subtotal_border
            if col_name in ["Debit", "Credit"]:
                if cell.value != "":
                    cell.number_format = '#,##0.00'
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="center", vertical="center")

        # ----------------------------------------------------
        # ROW 2: Header Row
        # ----------------------------------------------------
        ws.append(columns_order)
        for col_idx, col_name in enumerate(columns_order, 1):
            cell = ws.cell(row=2, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        # ----------------------------------------------------
        # ROW 3+: Data Rows
        # ----------------------------------------------------
        for row_idx, tx in enumerate(transactions, start=3):
            sr_num = tx.get("Sr No.") or global_sr_no

            row_data = [
                sr_num,
                sanitize_value(tx.get("Date", "")),
                sanitize_value(tx.get("Description", "")),
                sanitize_value(tx.get("Ledger", "")), # Empty Ledger column
                tx.get("Debit"),
                tx.get("Credit"),
                tx.get("Balance")
            ]
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
                elif col_name == "Ledger":
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        # Enable Auto-filters on Header Row (Row 2)
        if len(transactions) > 0:
            last_col_letter = get_column_letter(len(columns_order))
            ws.auto_filter.ref = f"A2:{last_col_letter}{len(transactions) + 2}"

        # Auto-fit Column Widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or '')
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 60)

        # Set specific minimum width for empty Ledger column
        ws.column_dimensions['D'].width = 20

    wb.save(output_filepath)
    logger.info(f"Excel workbook generated successfully with Subtotal Row and Ledger column: {output_filepath}")
    return output_filepath

def generate_csv(transactions: List[Dict[str, Any]], output_filepath: str) -> str:
    """Exports transactions list to CSV file with Ledger column and Subtotal row."""
    total_debit = 0.0
    total_credit = 0.0
    for tx in transactions:
        d = tx.get("Debit")
        c = tx.get("Credit")
        if d is not None:
            try:
                total_debit += float(str(d).replace(',', ''))
            except (ValueError, TypeError):
                pass
        if c is not None:
            try:
                total_credit += float(str(c).replace(',', ''))
            except (ValueError, TypeError):
                pass

    rows = []
    # Row 1: Subtotal values above Debit and Credit
    rows.append({
        "Sr No.": "",
        "Date": "",
        "Description": "",
        "Ledger": "",
        "Debit": round(total_debit, 2) if total_debit > 0 else "",
        "Credit": round(total_credit, 2) if total_credit > 0 else "",
        "Balance": ""
    })

    # Data Rows
    for idx, tx in enumerate(transactions, 1):
        rows.append({
            "Sr No.": tx.get("Sr No.") or idx,
            "Date": tx.get("Date", ""),
            "Description": tx.get("Description", ""),
            "Ledger": tx.get("Ledger", ""),
            "Debit": tx.get("Debit", ""),
            "Credit": tx.get("Credit", ""),
            "Balance": tx.get("Balance", "")
        })

    df = pd.DataFrame(rows)
    df.to_csv(output_filepath, index=False)
    logger.info(f"CSV file generated with Subtotal Row and Ledger column: {output_filepath}")
    return output_filepath
