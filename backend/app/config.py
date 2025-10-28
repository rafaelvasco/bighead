import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # For embeddings only
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')  # For web search
    MODEL_NAME = "openai/gpt-4o-mini"
    EMBEDDING_MODEL = "text-embedding-3-small"
    CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './data/chroma_db')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')

    @staticmethod
    def validate():
        if not Config.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set in environment variables")
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        if not Config.PERPLEXITY_API_KEY:
            raise ValueError("PERPLEXITY_API_KEY not set in environment variables")
