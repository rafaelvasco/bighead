from flask import Flask
from flask_cors import CORS
from flask_compress import Compress
import os

from dotenv import load_dotenv

load_dotenv()

# Configure logging
from app.utils.logging_config import setup_logging, get_logger
setup_logging()

logger = get_logger(__name__)

def create_app():
    app = Flask(__name__)

    # Configure app
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'md'}

    # Enable CORS
    CORS(app)
    
    # Enable compression
    Compress(app)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Ensure data directory exists
    data_dir = os.getenv('CHROMA_DB_PATH', './data/chroma_db')
    os.makedirs(os.path.dirname(data_dir), exist_ok=True)

    # Register blueprints
    from app.routes import documents, query, summarize, health, admin, db_stats
    app.register_blueprint(health.bp)
    app.register_blueprint(documents.bp)
    app.register_blueprint(query.bp)
    app.register_blueprint(summarize.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(db_stats.bp)

    logger.info("BigHead application started successfully")

    return app
