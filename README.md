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

## API Endpoints

### Health Check 