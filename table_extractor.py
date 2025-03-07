import cv2
import numpy as np
import pytesseract
import json
from PIL import Image
import os

class TableExtractor:
    def __init__(self, tesseract_path=None):
        """
        Initialize the TableExtractor.
        
        Args:
            tesseract_path: Path to tesseract executable if not in PATH
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def preprocess_image(self, image_path):
        """
        Preprocess the image to enhance table detection.
        
        Args:
            image_path: Path to the input image
            
        Returns:
            Preprocessed image
        """
        # Read the image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # Dilate to connect text in the same cell
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        
        return img, gray, dilated
    
    def detect_table_structure(self, dilated):
        """
        Detect table structure (lines, rows, columns).
        
        Args:
            dilated: Dilated binary image
            
        Returns:
            Horizontal and vertical lines
        """
        # Find horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(dilated, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        
        # Find vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(dilated, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        return horizontal_lines, vertical_lines
    
    def find_table_cells(self, horizontal_lines, vertical_lines):
        """
        Find table cells using horizontal and vertical lines.
        
        Args:
            horizontal_lines: Detected horizontal lines
            vertical_lines: Detected vertical lines
            
        Returns:
            Contours of table cells
        """
        # Combine horizontal and vertical lines
        table_structure = cv2.add(horizontal_lines, vertical_lines)
        
        # Find contours
        contours, _ = cv2.findContours(table_structure, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours to get cells
        cells = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 20 and h > 20:  # Filter out small contours
                cells.append((x, y, w, h))
        
        return cells
    
    def extract_cell_text(self, img, cell):
        """
        Extract text from a cell using OCR.
        
        Args:
            img: Original image
            cell: Cell coordinates (x, y, width, height)
            
        Returns:
            Extracted text
        """
        x, y, w, h = cell
        cell_img = img[y:y+h, x:x+w]
        
        # Convert to PIL Image for Tesseract
        pil_img = Image.fromarray(cv2.cvtColor(cell_img, cv2.COLOR_BGR2RGB))
        
        # Extract text
        text = pytesseract.image_to_string(pil_img, config='--psm 6').strip()
        
        return text
    
    def organize_cells_into_rows(self, cells, threshold=10):
        """
        Organize cells into rows based on y-coordinate.
        
        Args:
            cells: List of cell coordinates
            threshold: Vertical distance threshold to consider cells in the same row
            
        Returns:
            Cells organized by rows
        """
        # Sort cells by y-coordinate
        sorted_cells = sorted(cells, key=lambda cell: cell[1])
        
        rows = []
        current_row = [sorted_cells[0]]
        
        for cell in sorted_cells[1:]:
            if abs(cell[1] - current_row[0][1]) <= threshold:
                current_row.append(cell)
            else:
                # Sort cells in the row by x-coordinate
                current_row.sort(key=lambda cell: cell[0])
                rows.append(current_row)
                current_row = [cell]
        
        # Add the last row
        if current_row:
            current_row.sort(key=lambda cell: cell[0])
            rows.append(current_row)
        
        return rows
    
    def extract_table(self, image_path):
        """
        Extract table data from an image.
        
        Args:
            image_path: Path to the input image
            
        Returns:
            JSON representation of the table
        """
        # Preprocess the image
        img, gray, dilated = self.preprocess_image(image_path)
        
        # Detect table structure
        horizontal_lines, vertical_lines = self.detect_table_structure(dilated)
        
        # Find table cells
        cells = self.find_table_cells(horizontal_lines, vertical_lines)
        
        # Organize cells into rows
        rows = self.organize_cells_into_rows(cells)
        
        # Extract text from each cell
        table_data = []
        
        # Calculate the total number of rows and columns
        num_rows = len(rows)
        num_cols = max([len(row) for row in rows]) if rows else 0
        
        for row_idx, row in enumerate(rows):
            row_data = []
            for cell_idx, cell in enumerate(row):
                x, y, w, h = cell
                text = self.extract_cell_text(img, cell)
                
                cell_data = {
                    "text": text,
                    "bounding_box": {
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h
                    },
                    "row": row_idx,
                    "column": cell_idx
                }
                
                row_data.append(cell_data)
            
            table_data.append(row_data)
        
        # Create a structured table representation with row and column information
        table_structure = {
            "cells": table_data,
            "structure": {
                "num_rows": num_rows,
                "num_columns": num_cols,
                "rows": [{"row_index": i} for i in range(num_rows)],
                "columns": [{"column_index": i} for i in range(num_cols)]
            }
        }
        
        return table_structure
    
    def save_to_json(self, table_data, output_path):
        """
        Save table data to a JSON file.
        
        Args:
            table_data: Extracted table data
            output_path: Path to save the JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(table_data, f, indent=2, ensure_ascii=False)
    
    def highlight_cells(self, image_path, table_data, output_path=None):
        """
        Draw bounding boxes around detected cells and save to a new image.
        
        Args:
            image_path: Path to the original image
            table_data: Extracted table data with bounding boxes
            output_path: Path to save the highlighted image (optional)
            
        Returns:
            Path to the highlighted image or the image itself if output_path is None
        """
        # Read the original image
        img = cv2.imread(image_path)
        
        # Make a copy to draw on
        highlighted_img = img.copy()
        
        # Get max row and column for labeling
        max_row = max([cell["row"] for row in table_data for cell in row]) if table_data else 0
        max_col = max([cell["column"] for row in table_data for cell in row]) if table_data else 0
        
        # Add padding to the image to accommodate row and column labels
        padding = 50
        padded_img = cv2.copyMakeBorder(
            highlighted_img, 
            padding, padding, padding, padding, 
            cv2.BORDER_CONSTANT, 
            value=(255, 255, 255)
        )
        
        # Draw row and column labels
        for i in range(max_row + 1):
            cv2.putText(
                padded_img, 
                f"Row {i}", 
                (10, padding + i * 50 + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.6, (0, 0, 255), 2
            )
        
        for i in range(max_col + 1):
            cv2.putText(
                padded_img, 
                f"Col {i}", 
                (padding + i * 100, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.6, (0, 0, 255), 2
            )
        
        # Draw bounding boxes for each cell
        for row in table_data:
            for cell in row:
                # Get bounding box coordinates
                x = cell["bounding_box"]["x"] + padding
                y = cell["bounding_box"]["y"] + padding
                w = cell["bounding_box"]["width"]
                h = cell["bounding_box"]["height"]
                
                # Draw rectangle (green color with 2px thickness)
                cv2.rectangle(padded_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Add text labels (row, column)
                label = f"R{cell['row']}C{cell['column']}"
                cv2.putText(padded_img, label, (x + 5, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                
                # Add the cell text (truncated if too long)
                text = cell["text"]
                if len(text) > 15:
                    text = text[:12] + "..."
                cv2.putText(padded_img, text, (x + 5, y + h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # Save the highlighted image if output_path is provided
        if output_path:
            cv2.imwrite(output_path, padded_img)
            return output_path
        
        return padded_img
    
    def extract_table_from_pdf(self, pdf_path, page_num=0):
        """
        Extract table data from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number to extract (0-based index)
            
        Returns:
            JSON representation of the table
        """
        # Import pdf2image for PDF conversion
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise ImportError("pdf2image is required for PDF processing. Install it with 'pip install pdf2image'")
        
        try:
            # Convert PDF page to image
            images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)
            
            if not images or len(images) == 0:
                raise ValueError(f"Could not extract page {page_num} from PDF")
            
            # Save the image temporarily
            base_name = os.path.basename(pdf_path)
            base_name_without_ext = os.path.splitext(base_name)[0]
            dir_name = os.path.dirname(pdf_path)
            image_path = os.path.join(dir_name, f"{base_name_without_ext}_page{page_num}.png")
            
            # Ensure the image is saved properly
            images[0].save(image_path, 'PNG')
            
            # Verify the image was saved
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Failed to save PDF page as image: {image_path}")
            
            # Extract table from the image
            table_data = self.extract_table(image_path)
            
            # Add PDF-specific information
            table_data["pdf_info"] = {
                "source_file": os.path.basename(pdf_path),
                "page_number": page_num,
                "image_path": image_path
            }
            
            return table_data
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"Error processing PDF: {str(e)}")
