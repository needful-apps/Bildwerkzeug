"""
Bildwerkzeug - Datenbankmodelle
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Benutzer-Modell"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Passwort hashen und speichern"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Passwort überprüfen"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """User als Dictionary (ohne Passwort)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


def init_db(app):
    """Datenbank initialisieren und Admin-User erstellen"""
    with app.app_context():
        db.create_all()
        
        # Prüfen ob Admin existiert
        admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
        
        if not admin:
            # Admin aus Konfiguration erstellen
            admin = User(
                username=app.config['ADMIN_USERNAME'],
                email=app.config['ADMIN_EMAIL'],
                is_admin=True,
                is_active=True
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin-Benutzer '{app.config['ADMIN_USERNAME']}' erstellt")
        else:
            print(f"ℹ️  Admin-Benutzer '{app.config['ADMIN_USERNAME']}' existiert bereits")
