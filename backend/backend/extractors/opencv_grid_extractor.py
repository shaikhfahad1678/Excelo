"""
Method 2: OpenCV Morphological Grid Line Cleaning + Cell Isolation
"""
import os
from typing import List, Dict, Any
import pdfplumber
from backend.extractors.normalizer import clean_and_normalize_table
from backend.utils.logger import logger

def extract_via_opencv_grid(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Method 2: OpenCV Morphological Grid Line Cleaning + Cell Isolation
    Uses OpenCV-based line detection to segment grid tables from bank statement scans,
    then maps extracted text elements into the localized grid cell layout.
    """
    logger.info(f"Method 2 OpenCV Grid Extractor running on [{pdf_path}]...")
    
    try:
        import cv2
        import numpy as np
    except ImportError:
        logger.warning("opencv-python not installed. Falling back to native structured grid extraction.")
        from backend.extractors.candidate_extractors import run_pdfplumber_tables
        return run_pdfplumber_tables(pdf_path)

    raw_rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                # 1. Render page to PIL image and convert to OpenCV format
                pil_img = page.to_image(resolution=150).original
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                # 2. Threshold image (adaptive binary inversion)
                binary = cv2.adaptiveThreshold(
                    ~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                    cv2.THRESH_BINARY, 15, 2
                )

                # 3. Detect horizontal and vertical grid lines
                cols, rows = gray.shape
                horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (cols // 20, 1))
                vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, rows // 20))

                detect_horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
                detect_vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)

                # 4. Merge detected lines to build a table grid mask
                grid_mask = cv2.add(detect_horizontal, detect_vertical)

                # 5. Extract contours corresponding to table cells
                contours, _ = cv2.findContours(grid_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                
                # Filter bounding boxes representing reasonable cell dimensions
                cells = []
                for c in contours:
                    x, y, w, h = cv2.boundingRect(c)
                    if w > 30 and h > 10 and w < cols * 0.9 and h < rows * 0.1:
                        cells.append((x, y, x + w, y + h))

                if len(cells) < 10:
                    logger.debug(f"Fewer than 10 OpenCV cells found on page {page_idx + 1}. Falling back to Spatial Layout OCR.")
                    from backend.extractors.spatial_ocr_extractor import extract_via_spatial_layout_ocr
                    fallback_rows = extract_via_spatial_layout_ocr(pdf_path)
                    return fallback_rows


                # 6. Map page words into cells based on coordinate overlapping
                page_width = page.width
                page_height = page.height
                img_h, img_w = gray.shape

                # Scale factors from OpenCV image pixels to PDF points
                scale_x = page_width / img_w
                scale_y = page_height / img_h

                words = page.extract_words()
                
                # Sort cells vertically (y0) then horizontally (x0)
                cells_sorted = sorted(cells, key=lambda b: (b[1], b[0]))
                
                # Group cells into rows
                grid_rows = []
                current_row = []
                last_y0 = None

                for cell in cells_sorted:
                    x0, y0, x1, y1 = cell
                    if last_y0 is None or abs(y0 - last_y0) <= 12: # cells on the same horizontal row
                        current_row.append(cell)
                    else:
                        grid_rows.append(sorted(current_row, key=lambda b: b[0]))
                        current_row = [cell]
                    last_y0 = y0
                if current_row:
                    grid_rows.append(sorted(current_row, key=lambda b: b[0]))

                # For each row, map intersecting PDF words to reconstruct clean table rows
                for row_cells in grid_rows:
                    row_txts = []
                    for cell in row_cells:
                        cx0, cy0, cx1, cy1 = cell
                        # Scale to PDF points
                        px0, py0, px1, py1 = cx0 * scale_x, cy0 * scale_y, cx1 * scale_x, cy1 * scale_y
                        
                        # Find words intersecting this cell bounds
                        cell_words = []
                        for w in words:
                            if (w['x0'] >= px0 - 2 and w['x1'] <= px1 + 2 and 
                                w['top'] >= py0 - 2 and w['bottom'] <= py1 + 2):
                                cell_words.append(w)
                        cell_words_sorted = sorted(cell_words, key=lambda w: w['x0'])
                        cell_str = " ".join([w['text'] for w in cell_words_sorted]).strip()
                        row_txts.append(cell_str)
                    
                    if any(row_txts):
                        raw_rows.append(row_txts)

        normalized = clean_and_normalize_table(raw_rows)
        logger.info(f"OpenCV Grid Extractor successfully returned {len(normalized)} rows.")
        return normalized

    except Exception as e:
        logger.error(f"OpenCV Grid Extractor failed: {e}")
        from backend.extractors.candidate_extractors import run_pdfplumber_tables
        return run_pdfplumber_tables(pdf_path)
