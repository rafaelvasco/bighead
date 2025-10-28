from flask import Flask
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)

    # Configure app
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'md'}

    # Enable CORS
    CORS(app)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Ensure data directory exists
    data_dir = os.getenv('CHROMA_DB_PATH', './data/chroma_db')
    os.makedirs(os.path.dirname(data_dir), exist_ok=True)

    # Register blueprints
    from app.routes import documents, query, summarize, health, admin
    app.register_blueprint(health.bp)
    app.register_blueprint(documents.bp)
    app.register_blueprint(query.bp)
    app.register_blueprint(summarize.bp)
    app.register_blueprint(admin.bp)

    logger.info("BigHead application started successfully")

    return app
