from flask import Flask, request, jsonify, send_file
import os
import uuid
from werkzeug.utils import secure_filename
from table_extractor import TableExtractor
import cv2

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tif', 'tiff', 'bmp', 'pdf'}
OUTPUT_FOLDER = 'outputs'

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "message": "Table Extractor API is running"})

@app.route('/extract_table', methods=['POST'])
def extract_table():
    """
    Extract table from an uploaded image or PDF
    
    Returns:
        JSON with extracted table data or error message
    """
    # Check if file is in the request
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify({
            "error": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400
    
    try:
        # Generate unique filename
        unique_filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        file.save(file_path)
        
        # Initialize the extractor
        extractor = TableExtractor()
        
        # Check if it's a PDF file
        is_pdf = file.filename.lower().endswith('.pdf')
        
        # Extract table data
        if is_pdf:
            # For PDF, we'll extract from the first page by default
            table_data = extractor.extract_table_from_pdf(file_path, page_num=0)
            # Get image dimensions from the converted PDF page
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_filename.split('.')[0]}_page0.png")
            
            # Check if the converted image exists
            if not os.path.exists(img_path):
                return jsonify({"error": f"Failed to convert PDF to image: {img_path} not found"}), 500
                
            img = cv2.imread(img_path)
            if img is None:
                return jsonify({"error": f"Failed to load converted PDF image: {img_path}"}), 500
        else:
            # For images, use the existing method
            table_data = extractor.extract_table(file_path)
            img = cv2.imread(file_path)
            if img is None:
                return jsonify({"error": f"Failed to load image: {file_path}"}), 500
        
        # Get image dimensions
        height, width = img.shape[:2]
        
        # Create highlighted image
        highlighted_filename = f"highlighted_{unique_filename}"
        if is_pdf:
            highlighted_filename = f"highlighted_{unique_filename.split('.')[0]}_page0.png"
        highlighted_path = os.path.join(app.config['OUTPUT_FOLDER'], highlighted_filename)
        
        # For PDF, use the converted image for highlighting
        if is_pdf:
            extractor.highlight_cells(img_path, table_data["cells"], highlighted_path)
        else:
            extractor.highlight_cells(file_path, table_data["cells"], highlighted_path)
        
        # Return the extracted data
        response = {
            "message": "Table extracted successfully",
            "table_data": table_data,
            "image_info": {
                "width": width,
                "height": height
            },
            "highlighted_image": highlighted_filename,
            "file_type": "pdf" if is_pdf else "image"
        }
        
        return jsonify(response)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Clean up uploaded file after processing
        if os.path.exists(file_path):
            os.remove(file_path)
        # Clean up converted PDF pages if any
        if file.filename.lower().endswith('.pdf'):
            for f in os.listdir(app.config['UPLOAD_FOLDER']):
                if f.startswith(unique_filename.split('.')[0]) and f.endswith('.png'):
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
                    except:
                        pass

@app.route('/highlighted_image/<filename>', methods=['GET'])
def get_highlighted_image(filename):
    """
    Get the highlighted image with bounding boxes
    
    Args:
        filename: Name of the highlighted image file
    
    Returns:
        The highlighted image file
    """
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "Highlighted image not found"}), 404
    
    return send_file(file_path, mimetype='image/jpeg')

@app.route('/download_highlighted_image/<filename>', methods=['GET'])
def download_highlighted_image(filename):
    """
    Download the highlighted image with bounding boxes with a custom filename
    
    Args:
        filename: Name of the highlighted image file in the server
    
    Returns:
        The highlighted image file as a downloadable attachment
    """
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "Highlighted image not found"}), 404
    
    # Get the original filename without the UUID prefix
    original_name = filename
    if '_' in filename:
        parts = filename.split('_', 1)
        if len(parts) > 1:
            original_name = parts[1]
    
    # If it's a highlighted image, clean up the filename
    if original_name.startswith('highlighted_'):
        original_name = original_name.replace('highlighted_', '')
    
    # Ensure the filename has an extension
    if not any(original_name.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
        original_name += '.png'
    
    # Return the file as a downloadable attachment with the cleaned-up filename
    return send_file(
        file_path, 
        as_attachment=True,
        download_name=f"table_highlighted_{original_name}"
    )

@app.route('/', methods=['GET'])
def index():
    """
    Simple HTML form to test the API
    """
    return '''
    <!doctype html>
    <html>
    <head>
        <title>Table Extractor API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            form { background: #f8f8f8; padding: 20px; border-radius: 5px; }
            input[type=file] { margin: 10px 0; }
            input[type=submit] { background: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
            input[type=submit]:hover { background: #45a049; }
            .api-info { margin-top: 30px; background: #e9f7ef; padding: 15px; border-radius: 5px; }
            .endpoint { background: #f1f1f1; padding: 10px; margin: 5px 0; border-radius: 3px; font-family: monospace; }
        </style>
    </head>
    <body>
        <h1>Table Extractor API</h1>
        <form action="/extract_table" method="post" enctype="multipart/form-data">
            <h3>Upload an image or PDF containing a table:</h3>
            <input type="file" name="file" accept=".png,.jpg,.jpeg,.tif,.tiff,.bmp,.pdf">
            <br>
            <input type="submit" value="Extract Table">
        </form>
        
        <div class="api-info">
            <h3>API Endpoints:</h3>
            <div class="endpoint">GET /health - Check API status</div>
            <div class="endpoint">POST /extract_table - Extract table from image/PDF</div>
            <div class="endpoint">GET /highlighted_image/&lt;filename&gt; - View highlighted image</div>
            <div class="endpoint">GET /download_highlighted_image/&lt;filename&gt; - Download highlighted image</div>
        </div>
    </body>
    </html>
    '''

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all exceptions and return JSON response"""
    return jsonify({
        "error": str(e),
        "status": "error"
    }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 