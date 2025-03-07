# Table Extractor API

This API extracts tabular data from images and PDFs. It identifies rows and columns, detects text within each cell using OCR, and returns the structured data in JSON format.

## Features

- Extract tables from images (PNG, JPG, TIFF, BMP)
- Extract tables from PDF documents
- Highlight detected tables with bounding boxes
- Return structured JSON data with cell text and positions
- Simple web interface for testing

## Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/table-extractor-api.git
   cd table-extractor-api
   ```

2. Build and start the Docker container:
   ```bash
   docker-compose up -d
   ```

3. The API will be available at http://localhost:5006

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/table-extractor-api.git
   cd table-extractor-api
   ```

2. Install Tesseract OCR and Poppler:
   - Ubuntu/Debian:
     ```bash
     sudo apt-get update
     sudo apt-get install -y tesseract-ocr libtesseract-dev poppler-utils
     ```
   - macOS:
     ```bash
     brew install tesseract poppler
     ```
   - Windows:
     - Download and install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
     - Download and install [Poppler](https://github.com/oschwartz10612/poppler-windows/releases/)

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. The API will be available at http://localhost:5000

## API Documentation

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web interface for testing the API |
| GET | `/health` | Check API health status |
| POST | `/extract_table` | Extract table from image or PDF |
| GET | `/highlighted_image/<filename>` | View highlighted image |
| GET | `/download_highlighted_image/<filename>` | Download highlighted image |

### Detailed API Reference

#### Health Check

```
GET /health
```

Checks if the API is running properly.

**Response:**
```json
{
  "status": "healthy",
  "message": "Table Extractor API is running"
}
```

#### Extract Table

```
POST /extract_table
```

Extracts tabular data from an uploaded image or PDF.

**Request:**
- Content-Type: `multipart/form-data`
- Form Parameters:
  - `file`: The image or PDF file containing a table (required)

**Response:**
```json
{
  "message": "Table extracted successfully",
  "table_data": {
    "cells": [
      [
        {
          "text": "Cell content",
          "bounding_box": {
            "x": 100,
            "y": 200,
            "width": 150,
            "height": 50
          },
          "row": 0,
          "column": 0
        },
        // More cells in the same row
      ],
      // More rows
    ],
    "structure": {
      "num_rows": 5,
      "num_columns": 4,
      "rows": [{"row_index": 0}, {"row_index": 1}, ...],
      "columns": [{"column_index": 0}, {"column_index": 1}, ...]
    }
  },
  "image_info": {
    "width": 1200,
    "height": 800
  },
  "highlighted_image": "highlighted_uuid_filename.png",
  "file_type": "image" // or "pdf"
}
```

**Error Responses:**

- 400 Bad Request:
  ```json
  {
    "error": "No file part in the request"
  }
  ```
  
- 400 Bad Request:
  ```json
  {
    "error": "No file selected"
  }
  ```
  
- 400 Bad Request:
  ```json
  {
    "error": "File type not allowed. Allowed types: png, jpg, jpeg, tif, tiff, bmp, pdf"
  }
  ```
  
- 500 Internal Server Error:
  ```json
  {
    "error": "Error message details",
    "status": "error"
  }
  ```

#### View Highlighted Image

```
GET /highlighted_image/<filename>
```

Returns the highlighted image with bounding boxes around detected cells.

**Parameters:**
- `filename`: The name of the highlighted image (returned from `/extract_table`)

**Response:**
- Content-Type: `image/jpeg`
- Body: Image file

**Error Response:**
- 404 Not Found:
  ```json
  {
    "error": "Highlighted image not found"
  }
  ```

#### Download Highlighted Image

```
GET /download_highlighted_image/<filename>
```

Downloads the highlighted image with a user-friendly filename.

**Parameters:**
- `filename`: The name of the highlighted image (returned from `/extract_table`)

**Response:**
- Content-Type: `image/jpeg`
- Content-Disposition: `attachment; filename="table_highlighted_filename.png"`
- Body: Image file

**Error Response:**
- 404 Not Found:
  ```json
  {
    "error": "Highlighted image not found"
  }
  ```

## Usage Examples

### Using cURL

**Extract table from an image:**
```bash
curl -X POST -F "file=@table_image.png" http://localhost:5006/extract_table
```

**Extract table from a PDF:**
```bash
curl -X POST -F "file=@document.pdf" http://localhost:5006/extract_table
```

**Download highlighted image:**
```bash
curl -X GET "http://localhost:5006/download_highlighted_image/highlighted_uuid_filename.png" --output table_highlighted.png
```

### Using Python

```python
import requests
import json

def extract_table(image_path, api_url="http://localhost:5006"):
    with open(image_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(f"{api_url}/extract_table", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Table extracted successfully with {len(result['table_data']['cells'])} rows")
        
        # Download highlighted image
        highlighted_image = result['highlighted_image']
        image_response = requests.get(f"{api_url}/download_highlighted_image/{highlighted_image}", stream=True)
        
        if image_response.status_code == 200:
            with open("highlighted_table.png", 'wb') as f:
                for chunk in image_response:
                    f.write(chunk)
            print("Highlighted image saved as highlighted_table.png")
        
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

# Example usage
result = extract_table("table_image.png")
```

### Using JavaScript/Fetch API

```javascript
async function extractTable(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  try {
    const response = await fetch('http://localhost:5006/extract_table', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('Table extracted successfully:', result);
    
    // Display or download the highlighted image
    const highlightedImageUrl = `http://localhost:5006/highlighted_image/${result.highlighted_image}`;
    document.getElementById('resultImage').src = highlightedImageUrl;
    
    return result;
  } catch (error) {
    console.error('Error extracting table:', error);
    return null;
  }
}

// Example usage with file input
document.getElementById('fileInput').addEventListener('change', (event) => {
  const file = event.target.files[0];
  if (file) {
    extractTable(file);
  }
});
```

## Web Interface

A simple web interface is available at the root URL (`/`) for testing the API. You can upload an image or PDF and see the extracted table data.

## Limitations

- The API works best with clearly defined tables with visible borders
- Complex tables with merged cells may not be accurately detected
- The quality of text extraction depends on the image resolution and clarity
- Very large files may exceed the default upload limit (16MB)

## Advanced Configuration

### Adjusting OCR Parameters

You can adjust the OCR parameters in the `TableExtractor` class to improve text recognition for specific types of documents:

```python
# In table_extractor.py
def extract_cell_text(self, img, cell):
    # ...
    # Change OCR configuration for different languages or page segmentation modes
    text = pytesseract.image_to_string(pil_img, config='--psm 6 -l eng')
    # ...
```

Common Tesseract configuration options:
- `--psm 6`: Assume a single uniform block of text
- `--psm 4`: Assume a single column of text of variable sizes
- `-l eng+fra`: Use English and French language data

### Customizing Table Detection

For tables with faint lines or no visible borders, you can adjust the preprocessing parameters:

```python
# In table_extractor.py
def preprocess_image(self, image_path):
    # ...
    # Adjust threshold values for different image qualities
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    # ...
```

### Handling Large Files

To handle larger files, adjust the maximum content length in `app.py`:

```python
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload size
```

## Troubleshooting

### Common Issues

1. **OCR quality is poor**
   - Ensure the image has sufficient resolution (at least 300 DPI)
   - Try preprocessing the image to improve contrast
   - Consider using a different Tesseract language pack

2. **Table structure not detected correctly**
   - Adjust the morphological kernel sizes in `detect_table_structure()`
   - For tables without borders, consider using a different detection approach

3. **PDF processing fails**
   - Ensure Poppler is correctly installed
   - Check if the PDF is encrypted or password-protected
   - Try converting the PDF to images manually before processing

### Logging

To enable detailed logging, add the following to `app.py`:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
```

## License

[MIT License](LICENSE) 