"""
Bildwerkzeug - Konfiguration

Umgebungsvariablen können in .env Datei oder direkt gesetzt werden.
"""

import os
from dotenv import load_dotenv

# .env Datei laden falls vorhanden
load_dotenv()


class Config:
    """Basis-Konfiguration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Datenbank
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///bildwerkzeug.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_MB', 50)) * 1024 * 1024
    
    # Admin-Benutzer (wird beim ersten Start erstellt falls nicht vorhanden)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')  # Sollte in Produktion geändert werden!
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@localhost')
    
    # Session
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('SESSION_LIFETIME_HOURS', 24)) * 3600


class DevelopmentConfig(Config):
    """Entwicklungs-Konfiguration"""
    DEBUG = True


class ProductionConfig(Config):
    """Produktions-Konfiguration"""
    DEBUG = False
    
    # In Produktion muss SECRET_KEY gesetzt sein
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError("SECRET_KEY muss in Produktion gesetzt sein!")
        return key


# Konfiguration basierend auf Umgebung wählen
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])()
