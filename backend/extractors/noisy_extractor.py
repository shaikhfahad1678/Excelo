"""
Dedicated Extractor for TYPE 4: Noisy / Complex Digital PDFs
Uses adaptive spatial word clustering, watermark/glyph noise filtering,
and dynamic X-histogram column mapping to cleanly extract tables from noisy PDFs.
"""
import re
from typing import List, Dict, Any, Tuple
import pdfplumber
import numpy as np
from backend.utils.logger import logger

DATE_IN_LINE_REGEX = re.compile(
    r'\b(\d{1,2}[\s\/\.-]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\/\.-]+\d{2,4}|\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4}|\d{4}[\/\.-]\d{1,2}[\/\.-]\d{1,2})\b',
    re.IGNORECASE
)

def parse_num(val_str: str) -> float | None:
    cleaned = re.sub(r'[^\d.-]', '', val_str)
    try:
        return float(cleaned)
    except ValueError:
        return None

def extract_noisy_digital_tables(pdf_path: str) -> List[List[str]]:
    """
    Extracts structured transaction rows from noisy or complex layout digital PDFs.
    """
    raw_rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # 1. Extract words with tight tolerances to assemble fragments
                words = page.extract_words(
                    x_tolerance=3,
                    y_tolerance=3,
                    keep_blank_chars=False,
                    use_text_flow=True
                )
                if not words:
                    continue

                # 2. Filter out isolated noise words (watermarks, tiny 1-char artifacts far off)
                clean_words = []
                for w in words:
                    txt = w['text'].strip()
                    # Skip watermark / micro noise text
                    if not txt or (len(txt) == 1 and not txt.isalnum() and txt not in ['/', '-', '.']):
                        continue
                    clean_words.append(w)

                if not clean_words:
                    continue

                # 3. Group words into horizontal lines using fuzzy Y-top coordinates
                words_sorted = sorted(clean_words, key=lambda w: (w['top'], w['x0']))
                lines = []
                current_line = []
                last_top = None

                for w in words_sorted:
                    if last_top is None or abs(w['top'] - last_top) <= 4.5:
                        current_line.append(w)
                    else:
                        lines.append(current_line)
                        current_line = [w]
                    last_top = w['top']
                if current_line:
                    lines.append(current_line)

                if not lines:
                    continue

                # 4. Identify lines that contain transaction dates (anchors)
                tx_lines = []
                for line in lines:
                    line_str = " ".join([w['text'] for w in line])
                    if DATE_IN_LINE_REGEX.search(line_str):
                        tx_lines.append(line)

                # If no date anchors found, fall back to line strings
                if not tx_lines:
                    for line in lines:
                        line_cells = [w['text'] for w in line]
                        if line_cells:
                            raw_rows.append(line_cells)
                    continue

                # 5. Build dynamic X-column bins from all date anchor lines
                x_positions = []
                for line in tx_lines:
                    for w in line:
                        x_positions.append((w['x0'], w['x1']))

                # Sort by x0
                x_positions.sort(key=lambda item: item[0])
                col_bins = []
                for b0, b1 in x_positions:
                    if not col_bins:
                        col_bins.append([b0, b1])
                    else:
                        last_b0, last_b1 = col_bins[-1]
                        if b0 <= last_b1 + 12: # Merge close column clusters
                            col_bins[-1] = [last_b0, max(last_b1, b1)]
                        else:
                            col_bins.append([b0, b1])

                # 6. Reconstruct rows by mapping words to nearest column bin
                for line in lines:
                    row_cells = [""] * len(col_bins)
                    line_str = " ".join([w['text'] for w in line])
                    
                    # Skip obvious page headers / footers
                    if "statement of account" in line_str.lower() or "page " in line_str.lower():
                        continue

                    for w in line:
                        x_center = (w['x0'] + w['x1']) / 2
                        matched = False
                        for c_idx, (b0, b1) in enumerate(col_bins):
                            if (b0 - 8) <= x_center <= (b1 + 8):
                                if row_cells[c_idx]:
                                    row_cells[c_idx] += " " + w['text']
                                else:
                                    row_cells[c_idx] = w['text']
                                matched = True
                                break
                        if not matched:
                            # Assign to nearest column
                            dists = [abs(x_center - (b0 + b1) / 2) for (b0, b1) in col_bins]
                            nearest_idx = int(np.argmin(dists))
                            if row_cells[nearest_idx]:
                                row_cells[nearest_idx] += " " + w['text']
                            else:
                                row_cells[nearest_idx] = w['text']

                    if any(cell.strip() for cell in row_cells):
                        raw_rows.append(row_cells)

        return raw_rows
    except Exception as e:
        logger.warning(f"Noisy digital extractor failed on {pdf_path}: {e}")
        return []
