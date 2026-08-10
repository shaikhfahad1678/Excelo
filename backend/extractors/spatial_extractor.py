"""
Spatial Word-Based Table Extractor using pdfplumber words & x-coordinate clustering.
Used when standard lattice/stream table extraction produces poor cell boundaries.
"""
from typing import List, Dict, Any
import pdfplumber
import numpy as np
from backend.utils.logger import logger

def extract_tables_via_words(pdf_path: str) -> List[List[str]]:
    """
    Extracts structured rows using word x/y coordinate clustering.
    """
    raw_rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words(
                    x_tolerance=3,
                    y_tolerance=3,
                    keep_blank_chars=False,
                    use_text_flow=True
                )
                if not words:
                    continue

                # 1. Group words into lines by top/bottom coordinates (y-tolerance)
                lines = []
                words_sorted = sorted(words, key=lambda w: (w['top'], w['x0']))
                
                current_line = []
                last_top = None
                for w in words_sorted:
                    if last_top is None or abs(w['top'] - last_top) <= 4:
                        current_line.append(w)
                    else:
                        lines.append(current_line)
                        current_line = [w]
                    last_top = w['top']
                if current_line:
                    lines.append(current_line)

                if not lines:
                    continue

                # 2. Find header line to establish column x-boundaries
                header_line_idx = None
                for idx, line in enumerate(lines[:10]):
                    line_str = " ".join([w['text'] for w in line]).lower()
                    if ("date" in line_str and ("balance" in line_str or "description" in line_str or "particulars" in line_str)):
                        header_line_idx = idx
                        break

                if header_line_idx is not None:
                    header_words = lines[header_line_idx]
                    # Establish column bins from header word positions
                    col_bounds = []
                    for hw in header_words:
                        col_bounds.append((hw['x0'] - 5, hw['x1'] + 25))
                    
                    # Sort bounds by x0
                    col_bounds.sort(key=lambda b: b[0])
                    
                    # Merge overlapping bounds
                    merged_bounds = []
                    for b in col_bounds:
                        if not merged_bounds:
                            merged_bounds.append(b)
                        else:
                            lb0, lb1 = merged_bounds[-1]
                            if b[0] <= lb1:
                                merged_bounds[-1] = (lb0, max(lb1, b[1]))
                            else:
                                merged_bounds.append(b)

                    # Build rows based on merged bounds
                    for line in lines[header_line_idx:]:
                        row = [""] * len(merged_bounds)
                        for w in line:
                            # Find which column bin this word falls into
                            x_center = (w['x0'] + w['x1']) / 2
                            matched = False
                            for c_idx, (b0, b1) in enumerate(merged_bounds):
                                if b0 <= x_center <= b1:
                                    if row[c_idx]:
                                        row[c_idx] += " " + w['text']
                                    else:
                                        row[c_idx] = w['text']
                                    matched = True
                                    break
                            if not matched:
                                # Assign to nearest column
                                dists = [abs(x_center - (b0+b1)/2) for (b0, b1) in merged_bounds]
                                nearest_idx = int(np.argmin(dists))
                                if row[nearest_idx]:
                                    row[nearest_idx] += " " + w['text']
                                else:
                                    row[nearest_idx] = w['text']
                        
                        if any(cell.strip() for cell in row):
                            raw_rows.append(row)
                else:
                    # Generic line string splitting if no explicit header found
                    for line in lines:
                        row_str = [w['text'] for w in line]
                        if row_str:
                            raw_rows.append(row_str)

        return raw_rows
    except Exception as e:
        logger.warning(f"Spatial word extraction failed on {pdf_path}: {e}")
        return []
