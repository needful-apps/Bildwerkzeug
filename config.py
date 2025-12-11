"""
Bildwerkzeug - Configuration

Environment variables can be set in .env file or directly.
"""

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Login required? If False, anonymous sessions are used
    LOGIN_REQUIRED = os.environ.get('LOGIN_REQUIRED', 'true').lower() in ('true', '1', 'yes')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///bildwerkzeug.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_MB', 50)) * 1024 * 1024
    
    # Admin user (created on first start if not present)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')  # Should be changed in production!
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@localhost')
    
    # Session
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('SESSION_LIFETIME_HOURS', 24)) * 3600


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # In production, SECRET_KEY must be set
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError("SECRET_KEY must be set in production!")
        return key


# Choose configuration based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])()
