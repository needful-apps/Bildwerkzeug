// Bildwerkzeug - JavaScript mit Server-Speicherung

// ==================== DOM ELEMENTE ====================
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const editor = document.getElementById('editor');
const previewImage = document.getElementById('previewImage');
const loading = document.getElementById('loading');
const toast = document.getElementById('toast');

// ==================== STATUS ====================
let currentWidth = 0;
let currentHeight = 0;
let originalWidth = 0;
let originalHeight = 0;
let uploadedImages = [];  // {id, filename, width, height}
let currentImageId = null;
let currentImageData = null;  // Base64 des aktuellen Bildes (vom Server geladen)

// ==================== SERVER API ====================

async function loadImagesFromServer() {
    try {
        const response = await fetch('/api/images');
        const data = await response.json();
        
        if (data.success && data.images && data.images.length > 0) {
            return {
                images: data.images,
                currentId: data.current_id
            };
        }
    } catch (e) {
        console.error('Error loading from server:', e);
    }
    return null;
}

async function uploadImageToServer(imageData, filename) {
    const response = await fetch('/api/images', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData, filename })
    });
    return await response.json();
}

async function getImageFromServer(imageId) {
    const response = await fetch(`/api/images/${imageId}`);
    return await response.json();
}

async function deleteImageFromServer(imageId) {
    const response = await fetch(`/api/images/${imageId}`, {
        method: 'DELETE'
    });
    return await response.json();
}

async function clearAllImagesFromServer() {
    const response = await fetch('/api/images/clear', {
        method: 'DELETE'
    });
    return await response.json();
}

async function setCurrentImageOnServer(imageId) {
    const response = await fetch('/api/images/current', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_id: imageId })
    });
    return await response.json();
}

// ==================== INITIALISIERUNG ====================

async function checkForSavedImages() {
    // Erst alles verstecken während wir laden
    const welcomeScreen = document.getElementById('welcomeScreen');
    const dropzoneEl = document.getElementById('dropzone');
    const editorEl = document.getElementById('editor');
    
    welcomeScreen.classList.add('hidden');
    dropzoneEl.classList.add('hidden');
    editorEl.classList.add('hidden');
    
    showLoading(true);
    
    try {
        const serverData = await loadImagesFromServer();
        
        showLoading(false);
        
        if (serverData && serverData.images.length > 0) {
            // Es gibt gespeicherte Bilder - Welcome Screen anzeigen
            showWelcomeScreen(serverData.images);
            return true;
        } else {
            // Keine gespeicherten Bilder - Dropzone anzeigen
            showDropzone();
            return false;
        }
    } catch (e) {
        console.error('Error checking for saved images:', e);
        showLoading(false);
        showDropzone();
        return false;
    }
}

function showWelcomeScreen(savedImages) {
    const welcomeScreen = document.getElementById('welcomeScreen');
    const dropzoneEl = document.getElementById('dropzone');
    const editorEl = document.getElementById('editor');
    
    welcomeScreen.classList.remove('hidden');
    dropzoneEl.classList.add('hidden');
    editorEl.classList.add('hidden');
    
    // Vorschau der gespeicherten Bilder anzeigen
    const previewContainer = document.getElementById('savedImagesPreview');
    previewContainer.innerHTML = '';
    
    const maxPreview = 4;
    const imagesToShow = savedImages.slice(0, maxPreview);
    
    imagesToShow.forEach(img => {
        const imgEl = document.createElement('img');
        imgEl.src = `/api/images/${img.id}/thumbnail`;
        imgEl.alt = img.filename;
        imgEl.title = img.filename;
        previewContainer.appendChild(imgEl);
    });
    
    // Wenn mehr Bilder vorhanden sind, "+X weitere" anzeigen
    if (savedImages.length > maxPreview) {
        const moreEl = document.createElement('div');
        moreEl.className = 'saved-images-count';
        moreEl.textContent = `+${savedImages.length - maxPreview} ${t('moreImages')}`;
        previewContainer.appendChild(moreEl);
    }
    
    // Übersetzungen auf den Welcome-Screen anwenden
    applyTranslations();
}

async function startNewSession() {
    showLoading(true);
    await clearAllImagesFromServer();
    uploadedImages = [];
    currentImageId = null;
    currentImageData = null;
    showLoading(false);
    showDropzone();
}

async function continueSession() {
    showLoading(true);
    
    const serverData = await loadImagesFromServer();
    
    if (serverData && serverData.images.length > 0) {
        uploadedImages = serverData.images;
        currentImageId = serverData.currentId || serverData.images[0].id;
        
        // Aktuelles Bild laden
        const imageData = await getImageFromServer(currentImageId);
        if (imageData.success) {
            currentImageData = imageData.image;
            const currentImg = uploadedImages.find(img => img.id === currentImageId);
            if (currentImg) {
                currentImg.imageData = imageData.image;
                showEditor(currentImg);
            }
        }
        console.log(t('loaded'), uploadedImages.length, t('imagesFromStorage'));
    } else {
        showDropzone();
    }
    
    showLoading(false);
}

function showDropzone() {
    const welcomeScreen = document.getElementById('welcomeScreen');
    const dropzoneEl = document.getElementById('dropzone');
    const editorEl = document.getElementById('editor');
    
    welcomeScreen.classList.add('hidden');
    dropzoneEl.classList.remove('hidden');
    editorEl.classList.add('hidden');
}

// ==================== INITIALISIERUNG ====================

document.addEventListener('DOMContentLoaded', () => {
    loadLanguage();
    applyTranslations();
    updateLanguageButtons();
    setupDropzone();
    setupSliders();
    setupAspectRatio();
    setupAddMoreInput();
    
    // Prüfen ob gespeicherte Bilder vorhanden sind
    checkForSavedImages().then(hasSaved => {
        if (!hasSaved) {
            console.log(t('noSavedImages'));
        }
    });
});

// ==================== DROPZONE ====================

function setupDropzone() {
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
        
        if (e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    });

    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFiles(e.target.files);
        }
    });
}

function setupAddMoreInput() {
    const addInput = document.getElementById('addFileInput');
    if (addInput) {
        addInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFiles(e.target.files, true);
            }
        });
    }
}

function addMoreImages() {
    document.getElementById('addFileInput').click();
}

// ==================== DATEI-HANDLING ====================

async function handleFiles(files, append = false) {
    const imageFiles = Array.from(files).filter(f => f.type.startsWith('image/'));
    
    if (imageFiles.length === 0) {
        showToast(t('onlyImageFiles'), 'error');
        return;
    }

    showLoading(true);

    try {
        const newImages = [];
        
        for (const file of imageFiles) {
            try {
                const imageData = await readFileAsBase64(file);
                
                // Bild auf Server hochladen
                const result = await uploadImageToServer(imageData, file.name);
                
                if (result.success) {
                    newImages.push({
                        ...result.image,
                        imageData: imageData  // Für sofortige Anzeige
                    });
                }
            } catch (e) {
                console.error('Fehler bei Datei:', file.name, e);
            }
        }
        
        if (newImages.length === 0) {
            showToast(t('noValidImages'), 'error');
            showLoading(false);
            return;
        }
        
        if (append) {
            uploadedImages = [...uploadedImages, ...newImages];
            updateGallery();
            showToast(`${newImages.length} ${t('imagesAdded')}`, 'success');
        } else {
            uploadedImages = newImages;
            currentImageId = newImages[0].id;
            currentImageData = newImages[0].imageData;
            showEditor(newImages[0]);
        }
        
    } catch (error) {
        showToast(t('uploadError') + error.message, 'error');
    }

    showLoading(false);
}

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// ==================== EDITOR ====================

function showEditor(imgData) {
    // Alle anderen Ansichten verstecken
    const welcomeScreen = document.getElementById('welcomeScreen');
    if (welcomeScreen) welcomeScreen.classList.add('hidden');
    dropzone.classList.add('hidden');
    editor.classList.remove('hidden');

    currentImageId = imgData.id;
    
    // Bild anzeigen
    if (imgData.imageData) {
        previewImage.src = imgData.imageData;
        currentImageData = imgData.imageData;
    } else if (currentImageData) {
        previewImage.src = currentImageData;
    }
    
    document.getElementById('imageName').textContent = imgData.filename;
    updateDimensions(imgData.width, imgData.height);

    originalWidth = imgData.width;
    originalHeight = imgData.height;

    document.getElementById('resizeWidth').value = imgData.width;
    document.getElementById('resizeHeight').value = imgData.height;
    document.getElementById('cropRight').value = imgData.width;
    document.getElementById('cropBottom').value = imgData.height;
    
    updateGallery();
}

function updateGallery() {
    const gallery = document.getElementById('gallery');
    gallery.innerHTML = '';
    
    uploadedImages.forEach(img => {
        const item = document.createElement('div');
        item.className = 'gallery-item' + (img.id === currentImageId ? ' active' : '');
        item.onclick = () => selectImage(img.id);
        
        item.innerHTML = `
            <img src="/api/images/${img.id}/thumbnail" alt="${img.filename}">
            <button class="remove-btn" onclick="event.stopPropagation(); removeImage('${img.id}')">×</button>
            <span class="filename">${img.filename}</span>
        `;
        
        gallery.appendChild(item);
    });
}

async function selectImage(imageId) {
    if (imageId === currentImageId) return;
    
    showLoading(true);
    
    const imgData = uploadedImages.find(img => img.id === imageId);
    if (imgData) {
        // Bild vom Server laden
        const imageData = await getImageFromServer(imageId);
        if (imageData.success) {
            currentImageId = imageId;
            currentImageData = imageData.image;
            imgData.imageData = imageData.image;
            imgData.width = imageData.width;
            imgData.height = imageData.height;
            
            previewImage.src = imageData.image;
            document.getElementById('imageName').textContent = imgData.filename;
            updateDimensions(imageData.width, imageData.height);
            
            originalWidth = imageData.width;
            originalHeight = imageData.height;
            document.getElementById('resizeWidth').value = imageData.width;
            document.getElementById('resizeHeight').value = imageData.height;
            
            updateGallery();
            resetSliders();
            
            // Aktuelles Bild auf Server setzen
            await setCurrentImageOnServer(imageId);
        }
    }
    
    showLoading(false);
}

async function removeImage(imageId) {
    showLoading(true);
    
    const result = await deleteImageFromServer(imageId);
    
    if (result.success) {
        uploadedImages = uploadedImages.filter(img => img.id !== imageId);
        
        if (uploadedImages.length === 0) {
            showLoading(false);
            newImage();
            return;
        }
        
        if (currentImageId === imageId) {
            // Neues aktuelles Bild laden
            const newCurrentId = result.current_id || uploadedImages[0].id;
            await selectImage(newCurrentId);
        } else {
            updateGallery();
        }
        
        showToast(t('imageRemoved'), 'success');
    }
    
    showLoading(false);
}

function updateDimensions(width, height) {
    currentWidth = width;
    currentHeight = height;
    document.getElementById('imageDimensions').textContent = `${width} × ${height} px`;
    document.getElementById('cropRight').value = width;
    document.getElementById('cropBottom').value = height;
}

// ==================== BILDBEARBEITUNG ====================

async function processImage(operation, params = {}) {
    if (!currentImageId) {
        showToast(t('uploadFirst'), 'error');
        return;
    }
    
    showLoading(true);

    try {
        if (operation === 'reset') {
            // Reset über Server-API
            const response = await fetch(`/api/images/${currentImageId}/reset`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                currentImageData = data.image;
                previewImage.src = data.image;
                updateDimensions(data.width, data.height);
                
                // Lokale Daten aktualisieren
                const currentImg = uploadedImages.find(img => img.id === currentImageId);
                if (currentImg) {
                    currentImg.width = data.width;
                    currentImg.height = data.height;
                    currentImg.imageData = data.image;
                }
                
                updateGallery();
                showToast(t('resetSuccess'), 'success');
            } else {
                showToast(data.error || t('processingError'), 'error');
            }
        } else {
            // Normale Operation mit image_id an Server senden
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    image_id: currentImageId,
                    operation, 
                    params 
                })
            });

            const data = await response.json();

            if (data.success) {
                currentImageData = data.image;
                previewImage.src = data.image;
                updateDimensions(data.width, data.height);
                
                // Lokale Daten aktualisieren
                const currentImg = uploadedImages.find(img => img.id === currentImageId);
                if (currentImg) {
                    currentImg.width = data.width;
                    currentImg.height = data.height;
                    currentImg.imageData = data.image;
                }
                
                updateGallery();
                
                let message = t('applySuccess');
                if (data.file_size_kb) {
                    message = `${t('compressedTo')}${data.file_size_kb.toFixed(1)} KB`;
                    document.getElementById('currentSizeInfo').textContent = 
                        `${t('newSize')} ${data.width}×${data.height} px, ~${data.file_size_kb.toFixed(1)} KB`;
                }
                showToast(message, 'success');
            } else {
                showToast(data.error || t('processingError'), 'error');
            }
        }
    } catch (error) {
        showToast(t('networkError') + error.message, 'error');
    }

    showLoading(false);
}

// ==================== BATCH-VERARBEITUNG ====================

async function applyToAllImages(operation, params = {}) {
    if (uploadedImages.length === 0) {
        showToast(t('noImagesLoaded'), 'error');
        return;
    }
    
    if (uploadedImages.length === 1) {
        processImage(operation, params);
        return;
    }
    
    showLoading(true);
    
    try {
        const imageIds = uploadedImages.map(img => img.id);
        
        const response = await fetch('/api/process_batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image_ids: imageIds, operation, params })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Lokale Daten aktualisieren
            data.results.forEach(result => {
                const img = uploadedImages.find(i => i.id === result.id);
                if (img) {
                    img.width = result.width;
                    img.height = result.height;
                    // imageData wird beim nächsten Laden aktualisiert
                    delete img.imageData;
                }
            });
            
            // Aktuelles Bild neu laden
            const imageData = await getImageFromServer(currentImageId);
            if (imageData.success) {
                currentImageData = imageData.image;
                previewImage.src = imageData.image;
                updateDimensions(imageData.width, imageData.height);
            }
            
            updateGallery();
            showToast(`${data.processed} ${t('batchSuccess')}`, 'success');
        } else {
            showToast(data.error || t('batchError'), 'error');
        }
    } catch (error) {
        showToast(t('networkError') + error.message, 'error');
    }
    
    showLoading(false);
}

// ==================== AKTIONEN ====================

function resize() {
    const width = parseInt(document.getElementById('resizeWidth').value);
    const height = parseInt(document.getElementById('resizeHeight').value);
    const keepAspect = document.getElementById('keepAspect').checked;

    if (width <= 0 || height <= 0) {
        showToast(t('invalidValues'), 'error');
        return;
    }

    processImage('resize', { width, height, keep_aspect: keepAspect });
}

function resizeByPercent() {
    const percent = parseInt(document.getElementById('scalePercent').value);
    
    if (percent <= 0) {
        showToast(t('invalidPercent'), 'error');
        return;
    }
    
    processImage('resize_percent', { percent });
}

function resizeToMaxSize() {
    const maxSizeMB = parseFloat(document.getElementById('maxFileSizeMB').value);
    const format = document.getElementById('maxSizeFormat').value;
    const quality = parseInt(document.getElementById('maxSizeQuality').value);
    
    if (maxSizeMB <= 0) {
        showToast(t('invalidFileSize'), 'error');
        return;
    }
    
    processImage('resize_max_size', { max_size_mb: maxSizeMB, format, quality });
}

function rotate(angle) {
    processImage('rotate', { angle });
}

function flip(direction) {
    processImage(direction === 'horizontal' ? 'flip_horizontal' : 'flip_vertical');
}

function applyFilter(filter) {
    processImage(filter);
}

function blur() {
    const radius = parseFloat(document.getElementById('blurRadius').value);
    processImage('blur', { radius });
}

function sharpen() {
    const factor = parseFloat(document.getElementById('sharpenFactor').value);
    processImage('sharpen', { factor });
}

function adjustBrightness() {
    const factor = parseFloat(document.getElementById('brightness').value);
    processImage('brightness', { factor });
}

function adjustContrast() {
    const factor = parseFloat(document.getElementById('contrast').value);
    processImage('contrast', { factor });
}

function adjustSaturation() {
    const factor = parseFloat(document.getElementById('saturation').value);
    processImage('saturation', { factor });
}

function crop() {
    const left = parseInt(document.getElementById('cropLeft').value) || 0;
    const top = parseInt(document.getElementById('cropTop').value) || 0;
    const right = parseInt(document.getElementById('cropRight').value) || currentWidth;
    const bottom = parseInt(document.getElementById('cropBottom').value) || currentHeight;

    if (left >= right || top >= bottom) {
        showToast(t('invalidCropValues'), 'error');
        return;
    }

    processImage('crop', { left, top, right, bottom });
}

function resetImage() {
    processImage('reset');
    resetSliders();
}

async function newImage() {
    showLoading(true);
    await clearAllImagesFromServer();
    uploadedImages = [];
    currentImageId = null;
    currentImageData = null;
    editor.classList.add('hidden');
    dropzone.classList.remove('hidden');
    fileInput.value = '';
    showLoading(false);
}

// ==================== BATCH-AKTIONEN ====================

function batchResize() {
    const width = parseInt(document.getElementById('resizeWidth').value);
    const height = parseInt(document.getElementById('resizeHeight').value);
    const keepAspect = document.getElementById('keepAspect').checked;
    if (width <= 0 || height <= 0) { showToast(t('invalidValues'), 'error'); return; }
    applyToAllImages('resize', { width, height, keep_aspect: keepAspect });
}

function batchResizeByPercent() {
    const percent = parseInt(document.getElementById('scalePercent').value);
    if (percent <= 0) { showToast(t('invalidPercent'), 'error'); return; }
    applyToAllImages('resize_percent', { percent });
}

function batchResizeToMaxSize() {
    const maxSizeMB = parseFloat(document.getElementById('maxFileSizeMB').value);
    const format = document.getElementById('maxSizeFormat').value;
    const quality = parseInt(document.getElementById('maxSizeQuality').value);
    if (maxSizeMB <= 0) { showToast(t('invalidFileSize'), 'error'); return; }
    applyToAllImages('resize_max_size', { max_size_mb: maxSizeMB, format, quality });
}

function batchRotate(angle) { applyToAllImages('rotate', { angle }); }
function batchFlip(direction) { applyToAllImages(direction === 'horizontal' ? 'flip_horizontal' : 'flip_vertical'); }
function batchApplyFilter(filter) { applyToAllImages(filter); }
function batchBlur() { applyToAllImages('blur', { radius: parseFloat(document.getElementById('blurRadius').value) }); }
function batchSharpen() { applyToAllImages('sharpen', { factor: parseFloat(document.getElementById('sharpenFactor').value) }); }
function batchAdjustBrightness() { applyToAllImages('brightness', { factor: parseFloat(document.getElementById('brightness').value) }); }
function batchAdjustContrast() { applyToAllImages('contrast', { factor: parseFloat(document.getElementById('contrast').value) }); }
function batchAdjustSaturation() { applyToAllImages('saturation', { factor: parseFloat(document.getElementById('saturation').value) }); }

// ==================== DOWNLOAD ====================

async function downloadImage() {
    if (!currentImageId || !currentImageData) {
        showToast(t('noImageToDownload'), 'error');
        return;
    }
    
    const currentImg = uploadedImages.find(img => img.id === currentImageId);
    if (!currentImg) return;
    
    const format = document.getElementById('downloadFormat').value;
    const quality = document.getElementById('downloadQuality').value;
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image: currentImageData,
                filename: currentImg.filename,
                format,
                quality: parseInt(quality)
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentImg.filename.replace(/\.[^.]+$/, '') + '_edited.' + format;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else {
            showToast(t('downloadError'), 'error');
        }
    } catch (error) {
        showToast(t('networkError') + error.message, 'error');
    }
}

async function downloadAllImages() {
    if (uploadedImages.length === 0) {
        showToast(t('noImageToDownload'), 'error');
        return;
    }
    
    const format = document.getElementById('downloadFormat').value;
    const quality = document.getElementById('downloadQuality').value;
    
    showLoading(true);
    
    try {
        // Alle Bilder vom Server laden
        const imagesToDownload = [];
        for (const img of uploadedImages) {
            const imageData = await getImageFromServer(img.id);
            if (imageData.success) {
                imagesToDownload.push({
                    filename: img.filename,
                    image: imageData.image
                });
            }
        }
        
        const response = await fetch('/api/download_zip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                images: imagesToDownload,
                format,
                quality: parseInt(quality)
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'images_edited.zip';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast(`${uploadedImages.length} ${t('imagesDownloaded')}`, 'success');
        } else {
            showToast(t('downloadError'), 'error');
        }
    } catch (error) {
        showToast(t('networkError') + error.message, 'error');
    }
    
    showLoading(false);
}

// ==================== UI HELPERS ====================

function setupSliders() {
    const sliders = [
        { id: 'blurRadius', display: 'blurValue' },
        { id: 'sharpenFactor', display: 'sharpenValue' },
        { id: 'brightness', display: 'brightnessValue', decimals: 1 },
        { id: 'contrast', display: 'contrastValue', decimals: 1 },
        { id: 'saturation', display: 'saturationValue', decimals: 1 },
        { id: 'downloadQuality', display: 'qualityValue' },
        { id: 'scalePercent', display: 'scalePercentValue' },
        { id: 'maxSizeQuality', display: 'maxSizeQualityValue' }
    ];
    
    sliders.forEach(({ id, display, decimals }) => {
        const slider = document.getElementById(id);
        if (slider) {
            slider.addEventListener('input', () => {
                const value = decimals ? parseFloat(slider.value).toFixed(decimals) : slider.value;
                document.getElementById(display).textContent = value;
            });
        }
    });
}

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

function resetSliders() {
    const defaults = {
        'brightness': 1, 'contrast': 1, 'saturation': 1,
        'blurRadius': 2, 'sharpenFactor': 2
    };
    const displays = {
        'brightness': 'brightnessValue', 'contrast': 'contrastValue', 
        'saturation': 'saturationValue', 'blurRadius': 'blurValue', 
        'sharpenFactor': 'sharpenValue'
    };
    
    Object.entries(defaults).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.value = value;
        const disp = document.getElementById(displays[id]);
        if (disp) disp.textContent = value === 1 ? '1.0' : value;
    });
}

function switchResizeTab(tab) {
    document.querySelectorAll('.resize-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.resize-content').forEach(c => c.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('resize' + tab.charAt(0).toUpperCase() + tab.slice(1)).classList.add('active');
}

function setScalePercent(value) {
    document.getElementById('scalePercent').value = value;
    document.getElementById('scalePercentValue').textContent = value;
}

function showLoading(show) {
    loading.classList.toggle('hidden', !show);
}

function showToast(message, type = 'error') {
    toast.textContent = message;
    toast.className = 'toast' + (type === 'success' ? ' success' : '');
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}
