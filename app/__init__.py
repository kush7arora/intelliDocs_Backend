from flask import Flask
from flask_cors import CORS
import os
from app.config import Config

def create_app():
    """
    Application factory function
    Creates and configures the Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Enable CORS for frontend integration
    CORS(app)
    
    # Create uploads folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register routes blueprint
    from app.routes import api
    app.register_blueprint(api, url_prefix='/api')
    
    return app
