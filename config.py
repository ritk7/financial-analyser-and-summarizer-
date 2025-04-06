import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-hackathon'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///financial_analyzer.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size