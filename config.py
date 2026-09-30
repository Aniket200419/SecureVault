import os
from dotenv import load_dotenv

# Load environment variables from .env file if available
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """App configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key-change-in-production')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'c2VjdXJldmF1bHRfMzJfYnl0ZXNfa2V5XzAxMjM0NQ==')
    
    # Database config
    db_path = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'instance', 'securevault.db'))
    if db_path.startswith('sqlite:///') and not db_path.startswith('sqlite:////') and not 'instance' in db_path:
        # Normalize relative path to instance folder
        db_path = 'sqlite:///' + os.path.join(basedir, 'instance', 'securevault.db')
    
    SQLALCHEMY_DATABASE_URI = db_path
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session and security config
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv('SECRET_KEY', 'csrf-secret-key')
