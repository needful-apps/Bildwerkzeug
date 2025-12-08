// Bildwerkzeug - JavaScript

// DOM Elemente
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const editor = document.getElementById('editor');
const previewImage = document.getElementById('previewImage');
const loading = document.getElementById('loading');
const toast = document.getElementById('toast');

// Bildinfo
let currentWidth = 0;
let currentHeight = 0;
let originalWidth = 0;
let originalHeight = 0;

// Multi-Image Verwaltung
let uploadedImages = [];  // Liste aller Bilder {id, filename, thumbnail}
let currentImageId = null;  // ID des aktuell ausgewählten Bildes

// Initialisierung
document.addEventListener('DOMContentLoaded', () => {
    setupDropzone();
    setupSliders();
    setupAspectRatio();
    setupAddMoreInput();
});

// Dropzone Setup
function setupDropzone() {
    // Drag & Drop Events
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadFiles(files);
        }
    });

    // Klick zum Auswählen
    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFiles(e.target.files);
        }
    });
}

// Weitere Bilder hinzufügen Setup
function setupAddMoreInput() {
    const addInput = document.getElementById('addFileInput');
    if (addInput) {
        addInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                uploadFiles(e.target.files, true);  // true = zu bestehenden hinzufügen
            }
        });
    }
}

// Button für weitere Bilder
function addMoreImages() {
    document.getElementById('addFileInput').click();
}

// Slider Updates
function setupSliders() {
    // Blur Slider
    const blurSlider = document.getElementById('blurRadius');
    blurSlider.addEventListener('input', () => {
        document.getElementById('blurValue').textContent = blurSlider.value;
    });

    // Sharpen Slider
    const sharpenSlider = document.getElementById('sharpenFactor');
    sharpenSlider.addEventListener('input', () => {
        document.getElementById('sharpenValue').textContent = sharpenSlider.value;
    });

    // Brightness Slider
    const brightnessSlider = document.getElementById('brightness');
    brightnessSlider.addEventListener('input', () => {
        document.getElementById('brightnessValue').textContent = parseFloat(brightnessSlider.value).toFixed(1);
    });

    // Contrast Slider
    const contrastSlider = document.getElementById('contrast');
    contrastSlider.addEventListener('input', () => {
        document.getElementById('contrastValue').textContent = parseFloat(contrastSlider.value).toFixed(1);
    });

    // Saturation Slider
    const saturationSlider = document.getElementById('saturation');
    saturationSlider.addEventListener('input', () => {
        document.getElementById('saturationValue').textContent = parseFloat(saturationSlider.value).toFixed(1);
    });

    // Quality Slider
    const qualitySlider = document.getElementById('downloadQuality');
    qualitySlider.addEventListener('input', () => {
        document.getElementById('qualityValue').textContent = qualitySlider.value;
    });
    
    // Scale Percent Slider
    const scalePercentSlider = document.getElementById('scalePercent');
    if (scalePercentSlider) {
        scalePercentSlider.addEventListener('input', () => {
            document.getElementById('scalePercentValue').textContent = scalePercentSlider.value;
        });
    }
    
    // Max Size Quality Slider
    const maxSizeQualitySlider = document.getElementById('maxSizeQuality');
    if (maxSizeQualitySlider) {
        maxSizeQualitySlider.addEventListener('input', () => {
            document.getElementById('maxSizeQualityValue').textContent = maxSizeQualitySlider.value;
        });
    }
}

// Seitenverhältnis beibehalten
function setupAspectRatio() {
    const widthInput = document.getElementById('resizeWidth');
    const heightInput = document.getElementById('resizeHeight');
    const keepAspect = document.getElementById('keepAspect');

    widthInput.addEventListener('input', () => {
        if (keepAspect.checked && originalWidth > 0) {
            const ratio = originalHeight / originalWidth;
            heightInput.value = Math.round(parseInt(widthInput.value) * ratio);
        }
    });

    heightInput.addEventListener('input', () => {
        if (keepAspect.checked && originalHeight > 0) {
            const ratio = originalWidth / originalHeight;
            widthInput.value = Math.round(parseInt(heightInput.value) * ratio);
        }
    });
}

// Dateien hochladen (mehrere)
async function uploadFiles(files, append = false) {
    // Nur Bilddateien filtern
    const imageFiles = Array.from(files).filter(f => f.type.startsWith('image/'));
    
    if (imageFiles.length === 0) {
        showToast('Bitte nur Bilddateien hochladen!', 'error');
        return;
    }

    showLoading(true);

    const formData = new FormData();
    imageFiles.forEach(file => {
        formData.append('files[]', file);
    });

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            if (append) {
                // Neue Bilder zu bestehenden hinzufügen
                uploadedImages = [...uploadedImages, ...data.images];
                updateGallery();
                showToast(`${data.images.length} Bild(er) hinzugefügt!`, 'success');
            } else {
                // Neue Upload-Session
                uploadedImages = data.images;
                showEditor(data.current);
            }
        } else {
            showToast(data.error || 'Fehler beim Hochladen', 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler: ' + error.message, 'error');
    }

    showLoading(false);
}

// Editor anzeigen
function showEditor(data) {
    dropzone.classList.add('hidden');
    editor.classList.remove('hidden');

    currentImageId = data.id;
    previewImage.src = data.image;
    document.getElementById('imageName').textContent = data.filename;
    updateDimensions(data.width, data.height);

    // Originalgrößen speichern
    originalWidth = data.width;
    originalHeight = data.height;

    // Resize-Felder setzen
    document.getElementById('resizeWidth').value = data.width;
    document.getElementById('resizeHeight').value = data.height;

    // Crop-Felder setzen
    document.getElementById('cropRight').value = data.width;
    document.getElementById('cropBottom').value = data.height;
    
    // Galerie aktualisieren
    updateGallery();
}

// Galerie aktualisieren
function updateGallery() {
    const gallery = document.getElementById('gallery');
    gallery.innerHTML = '';
    
    uploadedImages.forEach(img => {
        const item = document.createElement('div');
        item.className = 'gallery-item' + (img.id === currentImageId ? ' active' : '');
        item.onclick = () => selectImage(img.id);
        
        item.innerHTML = `
            <img src="${img.thumbnail}" alt="${img.filename}">
            <button class="remove-btn" onclick="event.stopPropagation(); removeImage('${img.id}')">×</button>
            <span class="filename">${img.filename}</span>
        `;
        
        gallery.appendChild(item);
    });
}

// Bild aus Galerie auswählen
async function selectImage(imageId) {
    if (imageId === currentImageId) return;
    
    showLoading(true);
    
    try {
        const response = await fetch(`/select/${imageId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentImageId = data.id;
            previewImage.src = data.image;
            document.getElementById('imageName').textContent = data.filename;
            updateDimensions(data.width, data.height);
            
            originalWidth = data.width;
            originalHeight = data.height;
            document.getElementById('resizeWidth').value = data.width;
            document.getElementById('resizeHeight').value = data.height;
            
            updateGallery();
            resetSliders();
        } else {
            showToast(data.error || 'Fehler beim Auswählen', 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler: ' + error.message, 'error');
    }
    
    showLoading(false);
}

// Bild entfernen
async function removeImage(imageId) {
    try {
        const response = await fetch(`/remove/${imageId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Aus lokaler Liste entfernen
            uploadedImages = uploadedImages.filter(img => img.id !== imageId);
            
            if (data.newCurrent) {
                // Neues aktuelles Bild anzeigen
                currentImageId = data.newCurrent.id;
                previewImage.src = data.newCurrent.image;
                document.getElementById('imageName').textContent = data.newCurrent.filename;
                updateDimensions(data.newCurrent.width, data.newCurrent.height);
                originalWidth = data.newCurrent.width;
                originalHeight = data.newCurrent.height;
            } else if (uploadedImages.length === 0) {
                // Keine Bilder mehr - zurück zur Dropzone
                newImage();
                return;
            }
            
            updateGallery();
            showToast('Bild entfernt', 'success');
        }
    } catch (error) {
        showToast('Fehler: ' + error.message, 'error');
    }
}

// Slider zurücksetzen
function resetSliders() {
    document.getElementById('brightness').value = 1;
    document.getElementById('brightnessValue').textContent = '1.0';
    document.getElementById('contrast').value = 1;
    document.getElementById('contrastValue').textContent = '1.0';
    document.getElementById('saturation').value = 1;
    document.getElementById('saturationValue').textContent = '1.0';
    document.getElementById('blurRadius').value = 2;
    document.getElementById('blurValue').textContent = '2';
    document.getElementById('sharpenFactor').value = 2;
    document.getElementById('sharpenValue').textContent = '2';
}

// Dimensionen aktualisieren
function updateDimensions(width, height) {
    currentWidth = width;
    currentHeight = height;
    document.getElementById('imageDimensions').textContent = `${width} × ${height} px`;
    
    // Crop-Felder aktualisieren
    document.getElementById('cropRight').value = width;
    document.getElementById('cropBottom').value = height;
}

// Bildoperation ausführen
async function processImage(operation, params = {}) {
    showLoading(true);

    try {
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ operation, params })
        });

        const data = await response.json();

        if (data.success) {
            previewImage.src = data.image;
            updateDimensions(data.width, data.height);
            showToast('Erfolgreich angewendet!', 'success');
        } else {
            showToast(data.error || 'Fehler bei der Verarbeitung', 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler: ' + error.message, 'error');
    }

    showLoading(false);
}

// Größe ändern
function resize() {
    const width = parseInt(document.getElementById('resizeWidth').value);
    const height = parseInt(document.getElementById('resizeHeight').value);
    const keepAspect = document.getElementById('keepAspect').checked;

    if (width <= 0 || height <= 0) {
        showToast('Bitte gültige Werte eingeben!', 'error');
        return;
    }

    processImage('resize', { width, height, keep_aspect: keepAspect });
}

// Resize Tab wechseln
function switchResizeTab(tab) {
    // Alle Tabs deaktivieren
    document.querySelectorAll('.resize-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.resize-content').forEach(c => c.classList.remove('active'));
    
    // Ausgewählten Tab aktivieren
    event.target.classList.add('active');
    
    if (tab === 'pixel') {
        document.getElementById('resizePixel').classList.add('active');
    } else if (tab === 'percent') {
        document.getElementById('resizePercent').classList.add('active');
    } else if (tab === 'maxsize') {
        document.getElementById('resizeMaxSize').classList.add('active');
    }
}

// Prozent Preset setzen
function setScalePercent(value) {
    document.getElementById('scalePercent').value = value;
    document.getElementById('scalePercentValue').textContent = value;
}

// Resize nach Prozent
function resizeByPercent() {
    const percent = parseInt(document.getElementById('scalePercent').value);
    
    if (percent <= 0) {
        showToast('Bitte gültigen Prozentwert eingeben!', 'error');
        return;
    }
    
    processImage('resize_percent', { percent });
}

// Resize auf maximale Dateigröße
async function resizeToMaxSize() {
    const maxSizeMB = parseFloat(document.getElementById('maxFileSizeMB').value);
    const format = document.getElementById('maxSizeFormat').value;
    const quality = parseInt(document.getElementById('maxSizeQuality').value);
    
    if (maxSizeMB <= 0) {
        showToast('Bitte gültige Dateigröße eingeben!', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                operation: 'resize_max_size', 
                params: { 
                    max_size_mb: maxSizeMB,
                    format: format,
                    quality: quality
                } 
            })
        });

        const data = await response.json();

        if (data.success) {
            previewImage.src = data.image;
            updateDimensions(data.width, data.height);
            
            // Info anzeigen
            const infoEl = document.getElementById('currentSizeInfo');
            if (data.file_size_kb) {
                infoEl.textContent = `Neue Größe: ${data.width}×${data.height} px, ~${data.file_size_kb.toFixed(1)} KB`;
            }
            
            showToast('Erfolgreich komprimiert!', 'success');
        } else {
            showToast(data.error || 'Fehler bei der Verarbeitung', 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler: ' + error.message, 'error');
    }
    
    showLoading(false);
}

// Drehen
function rotate(angle) {
    processImage('rotate', { angle });
}

// Spiegeln
function flip(direction) {
    const operation = direction === 'horizontal' ? 'flip_horizontal' : 'flip_vertical';
    processImage(operation);
}

// Filter anwenden
function applyFilter(filter) {
    processImage(filter);
}

// Weichzeichnen
function blur() {
    const radius = parseFloat(document.getElementById('blurRadius').value);
    processImage('blur', { radius });
}

// Schärfen
function sharpen() {
    const factor = parseFloat(document.getElementById('sharpenFactor').value);
    processImage('sharpen', { factor });
}

// Helligkeit
function adjustBrightness() {
    const factor = parseFloat(document.getElementById('brightness').value);
    processImage('brightness', { factor });
}

// Kontrast
function adjustContrast() {
    const factor = parseFloat(document.getElementById('contrast').value);
    processImage('contrast', { factor });
}

// Sättigung
function adjustSaturation() {
    const factor = parseFloat(document.getElementById('saturation').value);
    processImage('saturation', { factor });
}

// Zuschneiden
function crop() {
    const left = parseInt(document.getElementById('cropLeft').value) || 0;
    const top = parseInt(document.getElementById('cropTop').value) || 0;
    const right = parseInt(document.getElementById('cropRight').value) || currentWidth;
    const bottom = parseInt(document.getElementById('cropBottom').value) || currentHeight;

    if (left >= right || top >= bottom) {
        showToast('Ungültige Zuschnittswerte!', 'error');
        return;
    }

    processImage('crop', { left, top, right, bottom });
}

// Zurücksetzen
function resetImage() {
    processImage('reset');
    resetSliders();
}

// Neues Bild
function newImage() {
    editor.classList.add('hidden');
    dropzone.classList.remove('hidden');
    fileInput.value = '';
    uploadedImages = [];
    currentImageId = null;
}

// Bild herunterladen
function downloadImage() {
    const format = document.getElementById('downloadFormat').value;
    const quality = document.getElementById('downloadQuality').value;
    
    window.location.href = `/download?format=${format}&quality=${quality}&id=${currentImageId}`;
}

// Loading anzeigen/verstecken
function showLoading(show) {
    if (show) {
        loading.classList.remove('hidden');
    } else {
        loading.classList.add('hidden');
    }
}

// Toast-Nachricht anzeigen
function showToast(message, type = 'error') {
    toast.textContent = message;
    toast.className = 'toast';
    if (type === 'success') {
        toast.classList.add('success');
    }
    
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}
