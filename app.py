"""
Bildwerkzeug - Ein Web-basiertes Bildbearbeitungstool mit Nutzerverwaltung
Bilder werden temporär auf dem Server gespeichert (pro Benutzer).
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, AnonymousUserMixin
from PIL import Image, ImageFilter, ImageEnhance
from functools import wraps
from datetime import datetime, timedelta
import io
import base64
import os
import uuid
import zipfile
import shutil
import json
import threading
import time

from config import get_config
from models import db, User, init_db

# Temporärer Upload-Ordner
UPLOAD_FOLDER = 'uploads'
TEMP_IMAGE_LIFETIME_HOURS = 24  # Bilder nach 24 Stunden löschen


class AnonymousUser(AnonymousUserMixin):
    """Anonymer Benutzer für Sessions ohne Login"""
    
    def __init__(self):
        self.id = None
        self.username = 'Anonym'
        self.is_admin = False
        self.is_active = True
    
    @property
    def session_id(self):
        """Session-ID für anonyme Benutzer (aus Flask session)"""
        from flask import session
        if 'anonymous_id' not in session:
            session['anonymous_id'] = str(uuid.uuid4())
        return session['anonymous_id']


def get_user_id():
    """Gibt die User-ID zurück (für anonyme Sessions die session_id)"""
    if current_user.is_authenticated:
        return current_user.id
    elif hasattr(current_user, 'session_id'):
        return f'anon_{current_user.session_id}'
    else:
        return None


def optional_login_required(f):
    """Decorator: Login nur erforderlich wenn LOGIN_REQUIRED=True"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if app.config.get('LOGIN_REQUIRED', True):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def create_app():
    """Flask App Factory"""
    app = Flask(__name__)
    
    # Konfiguration laden
    config = get_config()
    app.config.from_object(config)
    
    # Datenbank initialisieren
    db.init_app(app)
    
    # Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Bitte melde dich an.'
    login_manager.login_message_category = 'info'
    login_manager.anonymous_user = AnonymousUser
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Datenbank und Admin erstellen
    init_db(app)
    
    return app


app = create_app()


# Context Processor - config in allen Templates verfügbar machen
@app.context_processor
def inject_config():
    return {'config': app.config}


# Upload-Ordner erstellen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==================== TEMPORÄRE BILDSPEICHERUNG ====================

def get_user_upload_folder(user_id=None):
    """Gibt den Upload-Ordner für einen Benutzer zurück"""
    if user_id is None:
        user_id = get_user_id()
    folder = os.path.join(UPLOAD_FOLDER, f'user_{user_id}')
    os.makedirs(folder, exist_ok=True)
    return folder


def get_user_metadata_file(user_id):
    """Gibt den Pfad zur Metadaten-Datei zurück"""
    folder = get_user_upload_folder(user_id)
    return os.path.join(folder, 'metadata.json')


def load_user_metadata(user_id):
    """Lädt Metadaten für einen Benutzer"""
    meta_file = get_user_metadata_file(user_id)
    if os.path.exists(meta_file):
        try:
            with open(meta_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'images': [], 'current_id': None}


def save_user_metadata(user_id, metadata):
    """Speichert Metadaten für einen Benutzer"""
    meta_file = get_user_metadata_file(user_id)
    with open(meta_file, 'w') as f:
        json.dump(metadata, f)


def save_image_to_disk(user_id, image_id, img, is_original=False):
    """Speichert ein PIL Image auf der Festplatte"""
    folder = get_user_upload_folder(user_id)
    suffix = '_original' if is_original else ''
    filepath = os.path.join(folder, f'{image_id}{suffix}.png')
    img.save(filepath, 'PNG')
    return filepath


def save_thumbnail_to_disk(user_id, image_id, img):
    """Speichert ein Thumbnail auf der Festplatte"""
    folder = get_user_upload_folder(user_id)
    filepath = os.path.join(folder, f'{image_id}_thumb.png')
    thumb = img.copy()
    thumb.thumbnail((150, 150), Image.Resampling.LANCZOS)
    thumb.save(filepath, 'PNG')
    return filepath


def load_image_from_disk(user_id, image_id, is_original=False):
    """Lädt ein Bild von der Festplatte"""
    folder = get_user_upload_folder(user_id)
    suffix = '_original' if is_original else ''
    filepath = os.path.join(folder, f'{image_id}{suffix}.png')
    if os.path.exists(filepath):
        return Image.open(filepath)
    return None


def delete_image_from_disk(user_id, image_id):
    """Löscht alle Dateien eines Bildes"""
    folder = get_user_upload_folder(user_id)
    for suffix in ['', '_original', '_thumb']:
        filepath = os.path.join(folder, f'{image_id}{suffix}.png')
        if os.path.exists(filepath):
            os.remove(filepath)


def cleanup_old_uploads():
    """Löscht alte Upload-Ordner (älter als TEMP_IMAGE_LIFETIME_HOURS)"""
    if not os.path.exists(UPLOAD_FOLDER):
        return
    
    cutoff_time = datetime.now() - timedelta(hours=TEMP_IMAGE_LIFETIME_HOURS)
    
    for folder_name in os.listdir(UPLOAD_FOLDER):
        folder_path = os.path.join(UPLOAD_FOLDER, folder_name)
        if os.path.isdir(folder_path):
            # Prüfe das Änderungsdatum des Ordners
            folder_mtime = datetime.fromtimestamp(os.path.getmtime(folder_path))
            if folder_mtime < cutoff_time:
                try:
                    shutil.rmtree(folder_path)
                    print(f"Cleaned up old folder: {folder_name}")
                except Exception as e:
                    print(f"Error cleaning up {folder_name}: {e}")


def start_cleanup_thread():
    """Startet einen Hintergrund-Thread für regelmäßiges Cleanup"""
    def cleanup_loop():
        while True:
            time.sleep(3600)  # Jede Stunde
            cleanup_old_uploads()
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()


# Cleanup-Thread starten
start_cleanup_thread()


# ==================== HILFSFUNKTIONEN ====================

def base64_to_image(base64_string):
    """Konvertiert Base64 String zu PIL Image"""
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    img_data = base64.b64decode(base64_string)
    img = Image.open(io.BytesIO(img_data))
    
    if img.mode == 'P':
        img = img.convert('RGBA')
    
    return img


def image_to_base64(img, format='PNG'):
    """Konvertiert ein PIL Image zu Base64 String"""
    buffered = io.BytesIO()
    
    if format.upper() == 'JPEG':
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(buffered, format='JPEG', quality=95)
        mime = 'image/jpeg'
    else:
        img.save(buffered, format='PNG')
        mime = 'image/png'
    
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:{mime};base64,{img_str}"


def admin_required(f):
    """Decorator für Admin-only Routen"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin-Rechte erforderlich'}), 403
        return f(*args, **kwargs)
    return decorated_function


def apply_operation_to_image(img, operation, params):
    """Wendet eine Operation auf ein Bild an"""
    if operation == 'resize':
        width = int(params.get('width', img.width))
        height = int(params.get('height', img.height))
        keep_aspect = params.get('keep_aspect', True)
        
        if keep_aspect:
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
        else:
            img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    elif operation == 'resize_percent':
        percent = float(params.get('percent', 100))
        new_width = max(1, int(img.width * percent / 100))
        new_height = max(1, int(img.height * percent / 100))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    elif operation == 'resize_max_size':
        max_size_mb = float(params.get('max_size_mb', 1.0))
        format_type = params.get('format', 'jpeg').upper()
        quality = int(params.get('quality', 85))
        max_bytes = int(max_size_mb * 1024 * 1024)
        
        if format_type in ('JPEG', 'JPG'):
            format_type = 'JPEG'
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
        
        scale = 1.0
        while scale > 0.1:
            test_img = img.copy()
            if scale < 1.0:
                new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
                test_img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            if format_type == 'PNG':
                test_img.save(buffer, format=format_type)
            else:
                test_img.save(buffer, format=format_type, quality=quality)
            
            if buffer.tell() <= max_bytes:
                img = test_img
                break
            
            scale -= 0.05
            
    elif operation == 'rotate':
        angle = int(params.get('angle', 90))
        img = img.rotate(-angle, expand=True)
        
    elif operation == 'flip_horizontal':
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        
    elif operation == 'flip_vertical':
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        
    elif operation == 'grayscale':
        img = img.convert('L').convert('RGB')
        
    elif operation == 'blur':
        radius = float(params.get('radius', 2))
        img = img.filter(ImageFilter.GaussianBlur(radius=radius))
        
    elif operation == 'sharpen':
        factor = float(params.get('factor', 2))
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(factor)
        
    elif operation == 'brightness':
        factor = float(params.get('factor', 1.0))
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(factor)
        
    elif operation == 'contrast':
        factor = float(params.get('factor', 1.0))
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(factor)
        
    elif operation == 'saturation':
        factor = float(params.get('factor', 1.0))
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(factor)
        
    elif operation == 'crop':
        left = int(params.get('left', 0))
        top = int(params.get('top', 0))
        right = int(params.get('right', img.width))
        bottom = int(params.get('bottom', img.height))
        img = img.crop((left, top, right, bottom))
    
    return img


# ==================== AUTH ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite"""
    # Wenn Login nicht erforderlich, direkt zur Hauptseite
    if not app.config.get('LOGIN_REQUIRED', True):
        return redirect(url_for('index'))
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Dein Konto ist deaktiviert.', 'error')
                return render_template('login.html')
            
            login_user(user, remember=bool(remember))
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Ungültiger Benutzername oder Passwort.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('Du wurdest abgemeldet.', 'info')
    return redirect(url_for('login'))


# ==================== ADMIN ROUTES ====================

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    """Admin-Panel"""
    return render_template('admin.html')


@app.route('/api/admin/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Alle Benutzer abrufen"""
    users = User.query.all()
    return jsonify({
        'success': True,
        'users': [user.to_dict() for user in users]
    })


@app.route('/api/admin/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    """Neuen Benutzer erstellen"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    is_admin = data.get('is_admin', False)
    
    if not username or not email or not password:
        return jsonify({'error': 'Alle Felder sind erforderlich'}), 400
    
    if len(password) < 4:
        return jsonify({'error': 'Passwort muss mindestens 4 Zeichen haben'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Benutzername bereits vergeben'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'E-Mail bereits vergeben'}), 400
    
    user = User(
        username=username,
        email=email,
        is_admin=is_admin,
        is_active=True
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    })


@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Benutzer aktualisieren"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if user.id == get_user_id() and 'is_admin' in data and not data['is_admin']:
        return jsonify({'error': 'Du kannst dir selbst nicht die Admin-Rechte entziehen'}), 400
    
    if 'username' in data:
        new_username = data['username'].strip()
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Benutzername bereits vergeben'}), 400
        user.username = new_username
    
    if 'email' in data:
        new_email = data['email'].strip()
        existing = User.query.filter_by(email=new_email).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'E-Mail bereits vergeben'}), 400
        user.email = new_email
    
    if 'password' in data and data['password']:
        if len(data['password']) < 4:
            return jsonify({'error': 'Passwort muss mindestens 4 Zeichen haben'}), 400
        user.set_password(data['password'])
    
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
    
    if 'is_active' in data:
        if user.id == get_user_id() and not data['is_active']:
            return jsonify({'error': 'Du kannst dich nicht selbst deaktivieren'}), 400
        user.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    })


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Benutzer löschen"""
    user = User.query.get_or_404(user_id)
    
    if user.id == get_user_id():
        return jsonify({'error': 'Du kannst dich nicht selbst löschen'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True})


# ==================== MAIN ROUTES ====================

@app.route('/')
@optional_login_required
def index():
    """Hauptseite mit Drag & Drop Interface"""
    return render_template('index.html')


# ==================== TEMPORÄRE BILD-API ====================

@app.route('/api/images', methods=['GET'])
@optional_login_required
def get_images():
    """Liste aller gespeicherten Bilder für den aktuellen Benutzer"""
    try:
        metadata = load_user_metadata(get_user_id())
        return jsonify({
            'success': True,
            'images': metadata.get('images', []),
            'current_id': metadata.get('current_id')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images', methods=['POST'])
@optional_login_required
def upload_image():
    """Neues Bild hochladen und auf Server speichern"""
    try:
        data = request.get_json()
        image_data = data.get('image')
        filename = data.get('filename', 'image.png')
        
        if not image_data:
            return jsonify({'error': 'Kein Bild übermittelt'}), 400
        
        # Bild verarbeiten
        img = base64_to_image(image_data)
        image_id = str(uuid.uuid4())[:8]
        
        # Bild und Original speichern
        save_image_to_disk(get_user_id(), image_id, img, is_original=True)
        save_image_to_disk(get_user_id(), image_id, img, is_original=False)
        save_thumbnail_to_disk(get_user_id(), image_id, img)
        
        # Metadaten aktualisieren
        metadata = load_user_metadata(get_user_id())
        image_info = {
            'id': image_id,
            'filename': filename,
            'width': img.width,
            'height': img.height,
            'created_at': datetime.now().isoformat()
        }
        metadata['images'].append(image_info)
        if not metadata.get('current_id'):
            metadata['current_id'] = image_id
        save_user_metadata(get_user_id(), metadata)
        
        # Ordner-Zeitstempel aktualisieren für Cleanup
        folder = get_user_upload_folder(get_user_id())
        os.utime(folder, None)
        
        return jsonify({
            'success': True,
            'image': image_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images/<image_id>', methods=['GET'])
@optional_login_required
def get_image(image_id):
    """Ein bestimmtes Bild abrufen (als Base64)"""
    try:
        img = load_image_from_disk(get_user_id(), image_id)
        if not img:
            return jsonify({'error': 'Bild nicht gefunden'}), 404
        
        return jsonify({
            'success': True,
            'image': image_to_base64(img),
            'width': img.width,
            'height': img.height
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images/<image_id>/thumbnail', methods=['GET'])
@optional_login_required
def get_image_thumbnail(image_id):
    """Thumbnail eines Bildes abrufen"""
    try:
        folder = get_user_upload_folder(get_user_id())
        thumb_path = os.path.join(folder, f'{image_id}_thumb.png')
        
        if os.path.exists(thumb_path):
            return send_file(thumb_path, mimetype='image/png')
        
        return jsonify({'error': 'Thumbnail nicht gefunden'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images/<image_id>/original', methods=['GET'])
@optional_login_required
def get_image_original(image_id):
    """Original-Bild abrufen (als Base64)"""
    try:
        img = load_image_from_disk(get_user_id(), image_id, is_original=True)
        if not img:
            return jsonify({'error': 'Original nicht gefunden'}), 404
        
        return jsonify({
            'success': True,
            'image': image_to_base64(img),
            'width': img.width,
            'height': img.height
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images/<image_id>', methods=['PUT'])
@optional_login_required
def update_image(image_id):
    """Bild aktualisieren (nach Bearbeitung)"""
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'Kein Bild übermittelt'}), 400
        
        # Prüfen ob Bild existiert
        metadata = load_user_metadata(get_user_id())
        image_info = next((img for img in metadata['images'] if img['id'] == image_id), None)
        if not image_info:
            return jsonify({'error': 'Bild nicht gefunden'}), 404
        
        # Neues Bild speichern
        img = base64_to_image(image_data)
        save_image_to_disk(get_user_id(), image_id, img, is_original=False)
        save_thumbnail_to_disk(get_user_id(), image_id, img)
        
        # Metadaten aktualisieren
        image_info['width'] = img.width
        image_info['height'] = img.height
        image_info['updated_at'] = datetime.now().isoformat()
        save_user_metadata(get_user_id(), metadata)
        
        return jsonify({
            'success': True,
            'image': image_info,
            'width': img.width,
            'height': img.height
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images/<image_id>/reset', methods=['POST'])
@optional_login_required
def reset_image(image_id):
    """Bild auf Original zurücksetzen"""
    try:
        # Original laden
        original = load_image_from_disk(get_user_id(), image_id, is_original=True)
        if not original:
            return jsonify({'error': 'Original nicht gefunden'}), 404
        
        # Als aktuelles Bild speichern
        save_image_to_disk(get_user_id(), image_id, original, is_original=False)
        save_thumbnail_to_disk(get_user_id(), image_id, original)
        
        # Metadaten aktualisieren
        metadata = load_user_metadata(get_user_id())
        image_info = next((img for img in metadata['images'] if img['id'] == image_id), None)
        if image_info:
            image_info['width'] = original.width
            image_info['height'] = original.height
            image_info['updated_at'] = datetime.now().isoformat()
            save_user_metadata(get_user_id(), metadata)
        
        return jsonify({
            'success': True,
            'image': image_to_base64(original),
            'width': original.width,
            'height': original.height
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images/<image_id>', methods=['DELETE'])
@optional_login_required
def delete_image(image_id):
    """Bild löschen"""
    try:
        # Dateien löschen
        delete_image_from_disk(get_user_id(), image_id)
        
        # Metadaten aktualisieren
        metadata = load_user_metadata(get_user_id())
        metadata['images'] = [img for img in metadata['images'] if img['id'] != image_id]
        
        # Wenn gelöschtes Bild das aktuelle war, neues auswählen
        if metadata.get('current_id') == image_id:
            metadata['current_id'] = metadata['images'][0]['id'] if metadata['images'] else None
        
        save_user_metadata(get_user_id(), metadata)
        
        return jsonify({
            'success': True,
            'current_id': metadata.get('current_id')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images/current', methods=['PUT'])
@optional_login_required
def set_current_image():
    """Aktuelles Bild setzen"""
    try:
        data = request.get_json()
        image_id = data.get('image_id')
        
        metadata = load_user_metadata(get_user_id())
        
        # Prüfen ob Bild existiert
        if not any(img['id'] == image_id for img in metadata['images']):
            return jsonify({'error': 'Bild nicht gefunden'}), 404
        
        metadata['current_id'] = image_id
        save_user_metadata(get_user_id(), metadata)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images/clear', methods=['DELETE'])
@optional_login_required
def clear_all_images():
    """Alle Bilder des Benutzers löschen"""
    try:
        folder = get_user_upload_folder(get_user_id())
        if os.path.exists(folder):
            shutil.rmtree(folder)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== BILDBEARBEITUNG API ====================

@app.route('/api/process', methods=['POST'])
@optional_login_required
def process_image():
    """
    Bildbearbeitung durchführen.
    Kann entweder image_id oder base64 image verwenden.
    """
    try:
        data = request.get_json()
        image_id = data.get('image_id')
        image_data = data.get('image')
        operation = data.get('operation')
        params = data.get('params', {})
        
        if not operation:
            return jsonify({'error': 'Keine Operation angegeben'}), 400
        
        # Bild laden - entweder per ID oder Base64
        if image_id:
            img = load_image_from_disk(get_user_id(), image_id)
            if not img:
                return jsonify({'error': 'Bild nicht gefunden'}), 404
        elif image_data:
            img = base64_to_image(image_data)
        else:
            return jsonify({'error': 'Kein Bild übermittelt'}), 400
        
        # Operation anwenden
        img = apply_operation_to_image(img, operation, params)
        
        # Wenn image_id vorhanden, Bild auf Server speichern
        if image_id:
            save_image_to_disk(get_user_id(), image_id, img, is_original=False)
            save_thumbnail_to_disk(get_user_id(), image_id, img)
            
            # Metadaten aktualisieren
            metadata = load_user_metadata(get_user_id())
            image_info = next((i for i in metadata['images'] if i['id'] == image_id), None)
            if image_info:
                image_info['width'] = img.width
                image_info['height'] = img.height
                save_user_metadata(get_user_id(), metadata)
        
        response_data = {
            'success': True,
            'image': image_to_base64(img),
            'width': img.width,
            'height': img.height
        }
        
        if operation == 'resize_max_size':
            format_type = params.get('format', 'jpeg').upper()
            quality = int(params.get('quality', 85))
            
            buffer = io.BytesIO()
            if format_type == 'PNG':
                img.save(buffer, format='PNG')
            else:
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                img.save(buffer, format=format_type, quality=quality)
            
            response_data['file_size_kb'] = buffer.tell() / 1024
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/process_batch', methods=['POST'])
@optional_login_required
def process_batch():
    """Batch-Bildbearbeitung für mehrere Bilder (verwendet image_ids)."""
    try:
        data = request.get_json()
        image_ids = data.get('image_ids', [])
        operation = data.get('operation')
        params = data.get('params', {})
        
        if not image_ids:
            return jsonify({'error': 'Keine Bilder übermittelt'}), 400
        
        if not operation:
            return jsonify({'error': 'Keine Operation angegeben'}), 400
        
        results = []
        metadata = load_user_metadata(get_user_id())
        
        for image_id in image_ids:
            try:
                img = load_image_from_disk(get_user_id(), image_id)
                if not img:
                    continue
                
                img = apply_operation_to_image(img, operation, params)
                
                # Bild speichern
                save_image_to_disk(get_user_id(), image_id, img, is_original=False)
                save_thumbnail_to_disk(get_user_id(), image_id, img)
                
                # Metadaten aktualisieren
                image_info = next((i for i in metadata['images'] if i['id'] == image_id), None)
                if image_info:
                    image_info['width'] = img.width
                    image_info['height'] = img.height
                
                results.append({
                    'id': image_id,
                    'width': img.width,
                    'height': img.height
                })
                
            except Exception as e:
                print(f"Fehler bei Bild {image_id}: {e}")
                continue
        
        # Metadaten speichern
        save_user_metadata(get_user_id(), metadata)
        
        return jsonify({
            'success': True,
            'processed': len(results),
            'total': len(image_ids),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/create_thumbnail', methods=['POST'])
@optional_login_required
def create_thumbnail():
    """Erstellt ein Thumbnail für ein Bild."""
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'Kein Bild übermittelt'}), 400
        
        img = base64_to_image(image_data)
        original_width = img.width
        original_height = img.height
        
        thumb = img.copy()
        thumb.thumbnail((150, 150), Image.Resampling.LANCZOS)
        
        return jsonify({
            'success': True,
            'thumbnail': image_to_base64(thumb),
            'width': original_width,
            'height': original_height
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
@optional_login_required
def download_image():
    """Bild herunterladen (POST wegen Base64 Daten)."""
    try:
        data = request.get_json()
        image_data = data.get('image')
        filename = data.get('filename', 'bild')
        format_type = data.get('format', 'png').lower()
        quality = int(data.get('quality', 95))
        
        if not image_data:
            return jsonify({'error': 'Kein Bild übermittelt'}), 400
        
        img = base64_to_image(image_data)
        
        name_without_ext = os.path.splitext(filename)[0]
        new_filename = f"{name_without_ext}_bearbeitet.{format_type}"
        
        img_bytes = io.BytesIO()
        
        if format_type in ('jpeg', 'jpg'):
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(img_bytes, format='JPEG', quality=quality)
            mimetype = 'image/jpeg'
        elif format_type == 'webp':
            img.save(img_bytes, format='WEBP', quality=quality)
            mimetype = 'image/webp'
        else:
            img.save(img_bytes, format='PNG')
            mimetype = 'image/png'
        
        img_bytes.seek(0)
        
        return send_file(
            img_bytes,
            mimetype=mimetype,
            as_attachment=True,
            download_name=new_filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download_zip', methods=['POST'])
@optional_login_required
def download_zip():
    """Mehrere Bilder als ZIP herunterladen."""
    try:
        data = request.get_json()
        images = data.get('images', [])
        format_type = data.get('format', 'png').lower()
        quality = int(data.get('quality', 95))
        
        if not images:
            return jsonify({'error': 'Keine Bilder übermittelt'}), 400
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for img_item in images:
                try:
                    filename = img_item.get('filename', 'bild')
                    image_data = img_item.get('image')
                    
                    if not image_data:
                        continue
                    
                    img = base64_to_image(image_data)
                    
                    name_without_ext = os.path.splitext(filename)[0]
                    new_filename = f"{name_without_ext}_bearbeitet.{format_type}"
                    
                    img_bytes = io.BytesIO()
                    
                    if format_type in ('jpeg', 'jpg'):
                        if img.mode == 'RGBA':
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[3])
                            img = background
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        img.save(img_bytes, format='JPEG', quality=quality)
                    elif format_type == 'webp':
                        img.save(img_bytes, format='WEBP', quality=quality)
                    else:
                        img.save(img_bytes, format='PNG')
                    
                    img_bytes.seek(0)
                    zip_file.writestr(new_filename, img_bytes.getvalue())
                    
                except Exception as e:
                    print(f"Fehler bei Bild {img_item.get('filename')}: {e}")
                    continue
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='bilder_bearbeitet.zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("🖼️  Bildwerkzeug startet...")
    print("📍 Öffne http://localhost:5056 im Browser")
    print("💾 Bilder werden im Browser LocalStorage gespeichert")
    app.run(debug=True, port=5056)
