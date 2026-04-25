from flask import Flask, send_from_directory
from flask_cors import CORS
from .config import Config
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global ML models disabled as per pivot.
predictor = None
extractor = None

def create_app():
    
    # Configure paths for frontend
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dir = os.path.join(os.path.dirname(base_dir), "frontend")
    
    app = Flask(__name__, 
                static_folder=frontend_dir,
                template_folder=frontend_dir)
    app.config.from_object(Config)
    
    CORS(app)
    



    # Register blueprints
    from .api.chat import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/api')

    # Add root route to serve the frontend
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    # Serve other static files (CSS, JS) automatically via static_url_path
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(app.static_folder, path)
    
    return app
