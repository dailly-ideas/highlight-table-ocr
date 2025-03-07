FROM python:3.9-slim

# Install system dependencies including Tesseract OCR and Poppler for PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for uploads and outputs
RUN mkdir -p uploads outputs

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"] 