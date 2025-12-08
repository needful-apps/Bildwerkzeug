"""
Bildwerkzeug - Ein Web-basiertes Bildbearbeitungstool mit Nutzerverwaltung
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from PIL import Image, ImageFilter, ImageEnhance
from functools import wraps
from datetime import datetime
import io
import base64
import os
import uuid

from config import get_config
from models import db, User, init_db


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
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Datenbank und Admin erstellen
    init_db(app)
    
    return app


app = create_app()

# Temporärer Speicher für Bilder (pro User-Session)
user_images = {}  # {user_id: {image_id: {...}}}
user_current_image = {}  # {user_id: current_image_id}


def get_user_images():
    """Hole Bilder des aktuellen Nutzers"""
    user_id = current_user.id
    if user_id not in user_images:
        user_images[user_id] = {}
    return user_images[user_id]


def get_current_image_id():
    """Hole aktuelle Bild-ID des Nutzers"""
    return user_current_image.get(current_user.id)


def set_current_image_id(image_id):
    """Setze aktuelle Bild-ID des Nutzers"""
    user_current_image[current_user.id] = image_id


def admin_required(f):
    """Decorator für Admin-only Routen"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin-Rechte erforderlich'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ==================== AUTH ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite"""
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
    # Bilder des Nutzers aus Speicher entfernen
    user_id = current_user.id
    if user_id in user_images:
        del user_images[user_id]
    if user_id in user_current_image:
        del user_current_image[user_id]
    
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
    
    # Validierung
    if not username or not email or not password:
        return jsonify({'error': 'Alle Felder sind erforderlich'}), 400
    
    if len(password) < 4:
        return jsonify({'error': 'Passwort muss mindestens 4 Zeichen haben'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Benutzername bereits vergeben'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'E-Mail bereits vergeben'}), 400
    
    # Benutzer erstellen
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
    
    # Nicht den eigenen Admin-Status entfernen
    if user.id == current_user.id and 'is_admin' in data and not data['is_admin']:
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
        # Nicht sich selbst deaktivieren
        if user.id == current_user.id and not data['is_active']:
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
    
    # Nicht sich selbst löschen
    if user.id == current_user.id:
        return jsonify({'error': 'Du kannst dich nicht selbst löschen'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True})


# ==================== MAIN ROUTES ====================

@app.route('/')
@login_required
def index():
    """Hauptseite mit Drag & Drop Interface"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
@login_required
def upload_image():
    """Mehrere Bilder hochladen via Drag & Drop"""
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'Keine Dateien gefunden'}), 400
        
        files = request.files.getlist('files[]')
        uploaded_images = []
        images = get_user_images()
        
        for file in files:
            if file.filename == '':
                continue
            
            try:
                # Bild öffnen
                img = Image.open(file.stream)
                
                # In RGB konvertieren falls nötig (für JPEG-Kompatibilität)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Eindeutige ID generieren
                image_id = str(uuid.uuid4())[:8]
                
                # Bild im Speicher halten
                images[image_id] = {
                    'image': img.copy(),
                    'original': img.copy(),
                    'filename': file.filename
                }
                
                # Thumbnail für Galerie erstellen
                thumb = img.copy()
                thumb.thumbnail((150, 150), Image.Resampling.LANCZOS)
                thumb_data = image_to_base64(thumb)
                
                uploaded_images.append({
                    'id': image_id,
                    'filename': file.filename,
                    'width': img.width,
                    'height': img.height,
                    'thumbnail': thumb_data
                })
                
            except Exception as e:
                print(f"Fehler beim Laden von {file.filename}: {e}")
                continue
        
        if not uploaded_images:
            return jsonify({'error': 'Keine gültigen Bilder gefunden'}), 400
        
        # Erstes Bild als aktuelles setzen
        current_image_id = uploaded_images[0]['id']
        set_current_image_id(current_image_id)
        first_img = images[current_image_id]['image']
        
        return jsonify({
            'success': True,
            'images': uploaded_images,
            'current': {
                'id': current_image_id,
                'image': image_to_base64(first_img),
                'width': first_img.width,
                'height': first_img.height,
                'filename': uploaded_images[0]['filename']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/select/<image_id>', methods=['POST'])
@login_required
def select_image(image_id):
    """Bild aus Galerie auswählen"""
    try:
        images = get_user_images()
        
        if image_id not in images:
            return jsonify({'error': 'Bild nicht gefunden'}), 404
        
        set_current_image_id(image_id)
        img_data = images[image_id]
        img = img_data['image']
        
        return jsonify({
            'success': True,
            'id': image_id,
            'image': image_to_base64(img),
            'width': img.width,
            'height': img.height,
            'filename': img_data['filename']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/remove/<image_id>', methods=['DELETE'])
@login_required
def remove_image(image_id):
    """Bild aus Galerie entfernen"""
    try:
        images = get_user_images()
        current_image_id = get_current_image_id()
        
        if image_id not in images:
            return jsonify({'error': 'Bild nicht gefunden'}), 404
        
        del images[image_id]
        
        # Wenn das aktuelle Bild gelöscht wurde, anderes wählen
        if current_image_id == image_id:
            if images:
                new_current_id = list(images.keys())[0]
                set_current_image_id(new_current_id)
                img_data = images[new_current_id]
                img = img_data['image']
                return jsonify({
                    'success': True,
                    'newCurrent': {
                        'id': new_current_id,
                        'image': image_to_base64(img),
                        'width': img.width,
                        'height': img.height,
                        'filename': img_data['filename']
                    }
                })
            else:
                set_current_image_id(None)
                return jsonify({'success': True, 'newCurrent': None})
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/process', methods=['POST'])
@login_required
def process_image():
    """Bildbearbeitung durchführen"""
    try:
        data = request.get_json()
        operation = data.get('operation')
        params = data.get('params', {})
        
        images = get_user_images()
        current_image_id = get_current_image_id()
        
        if current_image_id is None or current_image_id not in images:
            return jsonify({'error': 'Kein Bild geladen'}), 400
        
        img = images[current_image_id]['image'].copy()
        
        # Variable für optionale Dateigröße
        final_size_kb = None
        
        # Verschiedene Operationen
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
            new_width = int(img.width * percent / 100)
            new_height = int(img.height * percent / 100)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        elif operation == 'resize_max_size':
            max_size_mb = float(params.get('max_size_mb', 1.0))
            format_type = params.get('format', 'jpeg').upper()
            quality = int(params.get('quality', 85))
            max_bytes = int(max_size_mb * 1024 * 1024)
            
            if format_type == 'JPEG' or format_type == 'JPG':
                format_type = 'JPEG'
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
            
            # Iterativ verkleinern bis Zielgröße erreicht
            scale = 1.0
            while scale > 0.1:
                test_img = img.copy()
                if scale < 1.0:
                    new_size = (int(img.width * scale), int(img.height * scale))
                    test_img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Größe testen
                buffer = io.BytesIO()
                if format_type == 'PNG':
                    test_img.save(buffer, format=format_type)
                else:
                    test_img.save(buffer, format=format_type, quality=quality)
                
                if buffer.tell() <= max_bytes:
                    img = test_img
                    break
                
                scale -= 0.05
            
            # Zusätzliche Info zurückgeben
            final_buffer = io.BytesIO()
            if format_type == 'PNG':
                img.save(final_buffer, format=format_type)
            else:
                img.save(final_buffer, format=format_type, quality=quality)
            final_size_kb = final_buffer.tell() / 1024
                
        elif operation == 'rotate':
            angle = int(params.get('angle', 90))
            # PIL dreht gegen den Uhrzeigersinn, daher negieren für intuitive Richtung
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
            
        elif operation == 'reset':
            img = images[current_image_id]['original'].copy()
            
        else:
            return jsonify({'error': f'Unbekannte Operation: {operation}'}), 400
        
        # Aktualisiertes Bild speichern
        images[current_image_id]['image'] = img
        
        # Bild als Base64 zurückgeben
        img_data = image_to_base64(img)
        
        # Response mit optionaler Dateigröße
        response_data = {
            'success': True,
            'image': img_data,
            'width': img.width,
            'height': img.height
        }
        
        if final_size_kb is not None:
            response_data['file_size_kb'] = final_size_kb
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download', methods=['GET'])
@login_required
def download_image():
    """Bearbeitetes Bild herunterladen"""
    try:
        format_type = request.args.get('format', 'png').lower()
        quality = int(request.args.get('quality', 95))
        image_id = request.args.get('id', get_current_image_id())
        
        images = get_user_images()
        
        if image_id is None or image_id not in images:
            return jsonify({'error': 'Kein Bild zum Download verfügbar'}), 400
        
        img = images[image_id]['image']
        original_filename = images[image_id]['filename']
        
        # Dateiname generieren
        name_without_ext = os.path.splitext(original_filename)[0]
        new_filename = f"{name_without_ext}_bearbeitet.{format_type}"
        
        # Bild in Bytes konvertieren
        img_bytes = io.BytesIO()
        
        if format_type == 'jpeg' or format_type == 'jpg':
            if img.mode == 'RGBA':
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


def image_to_base64(img):
    """Konvertiert ein PIL Image zu Base64 String"""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("🖼️  Bildwerkzeug startet...")
    print("📍 Öffne http://localhost:5050 im Browser")
    app.run(debug=True, port=5050)
