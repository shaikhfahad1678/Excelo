"""
Professional Excel Generator (.xlsx) using openpyxl & pandas
Includes bold headers, Sr No. column, frozen top row, auto-fit column widths,
numeric/date formatting, auto-filters, and conditional status highlighting.
"""
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from backend.utils.logger import logger

def generate_excel_workbook(
    sheet_data_map: Dict[str, List[Dict[str, Any]]],
    output_filepath: str
) -> str:
    """
    Generates a professionally styled Excel workbook.
    Adds `Sr No.` as column 1 (numbered sequentially 1..N across all pages).
    `sheet_data_map` maps sheet names to list of transaction dicts.
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active) # Remove default sheet

    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Dark Navy Slate header
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    alt_row_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    
    # Conditional Status Fills & Fonts
    status_styles = {
        "PASS": (PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid"), Font(name="Calibri", size=10, color="166534")),
        "LOW CONFIDENCE": (PatternFill(start_color="FEFCE8", end_color="FEFCE8", fill_type="solid"), Font(name="Calibri", size=10, color="854D0E")),
        "RECONSTRUCTED": (PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid"), Font(name="Calibri", size=10, color="1E40AF")),
        "FAILED VALIDATION": (PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid"), Font(name="Calibri", size=10, color="991B1B")),
        "MISSING DATA": (PatternFill(start_color="FFF7ED", end_color="FFF7ED", fill_type="solid"), Font(name="Calibri", size=10, color="9A3412")),
        "DUPLICATE": (PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid"), Font(name="Calibri", size=10, color="475569")),
        "BALANCE MISMATCH": (PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"), Font(name="Calibri", size=10, color="991B1B", bold=True)),
    }

    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    columns_order = [
        "Sr No.", "Date", "Description", "Cheque No.",
        "Debit", "Credit", "Balance", "Validation Status"
    ]

    global_sr_no = 1

    for sheet_name, transactions in sheet_data_map.items():
        safe_sheet_name = sheet_name[:30].replace("[", "").replace("]", "").replace("*", "").replace(":", "").replace("?", "").replace("/", "")
        ws = wb.create_sheet(title=safe_sheet_name or "Transactions")

        # Freeze top row
        ws.freeze_panes = "A2"

        # Write Header
        ws.append(columns_order)
        for col_num, col_name in enumerate(columns_order, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Write Data
        for row_idx, tx in enumerate(transactions, start=2):
            status = tx.get("Validation Status", "PASS")
            sr_num = tx.get("Sr No.") or global_sr_no

            row_data = [
                sr_num,
                tx.get("Date", ""),
                tx.get("Description", ""),
                tx.get("Cheque No.", ""),
                tx.get("Debit"),
                tx.get("Credit"),
                tx.get("Balance"),
                status
            ]
            ws.append(row_data)
            global_sr_no += 1

            status_fill, status_font = status_styles.get(status, (None, None))

            # Apply row styling & number formatting
            for col_idx in range(1, len(columns_order) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = thin_border

                if status_fill and status != "PASS":
                    cell.fill = status_fill
                    if status_font:
                        cell.font = status_font
                elif row_idx % 2 == 1:
                    cell.fill = alt_row_fill

                col_name = columns_order[col_idx - 1]
                if col_name in ["Debit", "Credit", "Balance"]:
                    if cell.value is not None and isinstance(cell.value, (int, float)):
                        cell.number_format = '#,##0.00'
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                elif col_name in ["Sr No.", "Date", "Validation Status"]:
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
    logger.info(f"Excel workbook generated successfully with Sr No. column: {output_filepath}")
    return output_filepath

def generate_csv(transactions: List[Dict[str, Any]], output_filepath: str) -> str:
    """Exports transactions list to CSV file."""
    cleaned_txs = []
    for tx in transactions:
        t = dict(tx)
        t.pop("Currency", None)
        t.pop("Ref No.", None)
        t.pop("Validation Details", None)
        t.pop("Confidence", None)
        cleaned_txs.append(t)
    df = pd.DataFrame(cleaned_txs)
    df.to_csv(output_filepath, index=False)
    logger.info(f"CSV file generated: {output_filepath}")
    return output_filepath
