FROM python:3.11-slim

# Arbeitsverzeichnis
WORKDIR /app

# System-Dependencies für Pillow
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Verzeichnisse erstellen
RUN mkdir -p /app/instance

# Port freigeben
EXPOSE 5000

# Umgebungsvariablen
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Nicht als root ausführen
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Gunicorn als Production Server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "app:app"]
