# 🖼️ Bildwerkzeug

Ein einfaches, webbasiertes Bildbearbeitungstool mit Drag & Drop Funktionalität und Nutzerverwaltung.

## Features

- **🔐 Login-System** - Sichere Authentifizierung mit Admin-Bereich
- **👥 Nutzerverwaltung** - Admin kann Benutzer anlegen, bearbeiten und löschen
- **📁 Drag & Drop Upload** - Mehrere Bilder gleichzeitig hochladen
- **📐 Größe ändern** - Pixel, Prozent oder maximale Dateigröße
- **🔄 Drehen & Spiegeln** - 90°, -90°, 180° Rotation und Spiegeln
- **🎨 Filter** - Graustufen, Weichzeichnen, Schärfen
- **⚡ Anpassungen** - Helligkeit, Kontrast, Sättigung
- **✂️ Zuschneiden** - Bilder auf gewünschten Bereich beschneiden
- **💾 Export** - Download in PNG, JPEG oder WebP Format
- **🐳 Docker-ready** - Einfaches Deployment mit Docker

## Schnellstart mit Docker

```bash
# Repository klonen
git clone <repo-url>
cd Bildwerkzeug

# Mit Docker Compose starten
docker compose up -d

# Öffne http://localhost:5000
# Login: admin / admin123
```

## Lokale Installation

1. **Python 3.8+** erforderlich

2. **Virtuelle Umgebung erstellen:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # oder: venv\Scripts\activate  # Windows
   ```

3. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Umgebungsvariablen setzen (optional):**
   ```bash
   cp .env.example .env
   # .env Datei bearbeiten
   ```

5. **Server starten:**
   ```bash
   python app.py
   ```

6. **Browser öffnen:**
   ```
   http://localhost:5050
   ```

## Konfiguration

Umgebungsvariablen können in `.env` gesetzt werden:

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `SECRET_KEY` | Flask Secret Key | `dev-secret-key-...` |
| `ADMIN_USERNAME` | Admin Benutzername | `admin` |
| `ADMIN_PASSWORD` | Admin Passwort | `admin` |
| `ADMIN_EMAIL` | Admin E-Mail | `admin@localhost` |
| `DATABASE_URL` | Datenbank URI | `sqlite:///bildwerkzeug.db` |
| `MAX_UPLOAD_MB` | Max Upload-Größe | `50` |
| `SESSION_LIFETIME_HOURS` | Session Dauer | `24` |

## Projektstruktur

```
Bildwerkzeug/
├── app.py              # Flask Backend
├── config.py           # Konfiguration
├── models.py           # Datenbankmodelle
├── requirements.txt    # Python Abhängigkeiten
├── Dockerfile          # Docker Image
├── docker-compose.yml  # Docker Compose
├── .env.example        # Beispiel Umgebungsvariablen
├── templates/
│   ├── index.html      # Hauptseite
│   ├── login.html      # Login-Seite
│   └── admin.html      # Admin-Panel
└── static/
    ├── style.css       # CSS Styles
    └── script.js       # JavaScript Frontend
```

## Docker Build

```bash
# Image bauen
docker build -t bildwerkzeug .

# Container starten
docker run -d \
  -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e ADMIN_PASSWORD=secure-password \
  -v bildwerkzeug_data:/app/data \
  --name bildwerkzeug \
  bildwerkzeug
```

## Technologien

- **Backend:** Python, Flask, Flask-Login, Flask-SQLAlchemy
- **Datenbank:** SQLite
- **Bildverarbeitung:** Pillow (PIL)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Deployment:** Docker, Gunicorn

## Lizenz

MIT License
