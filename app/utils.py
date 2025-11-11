import os
from werkzeug.utils import secure_filename
from flask import current_app
import PyPDF2
import docx

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension
    
    Args:
        filename (str): Name of the uploaded file
    
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def extract_text_from_file(file_path):
    """
    Extract text content from uploaded file based on file type
    
    Args:
        file_path (str): Path to the uploaded file
    
    Returns:
        str: Extracted text content
    """
    file_extension = file_path.rsplit('.', 1)[1].lower()
    
    try:
        if file_extension == 'txt':
            # Read plain text file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        elif file_extension == 'pdf':
            # Extract text from PDF
            text = ""
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        
        elif file_extension in ['doc', 'docx']:
            # Extract text from Word document
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        
        else:
            return "Unsupported file format"
    
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def get_file_size_mb(file_path):
    """
    Get file size in megabytes
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        float: File size in MB
    """
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)
