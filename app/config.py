import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    # File upload settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 16)) * 1024 * 1024  # MB to bytes
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
    
    # AWS Configuration (we'll use these in later steps)
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE', 'intellidocs-transcripts')
    S3_BUCKET = os.getenv('S3_BUCKET', 'intellidocs-text-files')
