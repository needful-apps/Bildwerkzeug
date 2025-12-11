/**
 * Bildwerkzeug - Zentrale Übersetzungen
 * 
 * Diese Datei enthält alle Übersetzungen für die Anwendung.
 * Unterstützte Sprachen: Englisch (en), Deutsch (de)
 */

const LANG_KEY = 'bildwerkzeug_lang';

let currentLang = 'en';

const translations = {
    en: {
        // Header
        appTitle: 'Bildwerkzeug',
        appSubtitle: 'Edit images via Drag & Drop',
        admin: '⚙️ Admin',
        logout: '🚪 Logout',
        
        // Login
        loginSubtitle: 'Please log in',
        username: 'Username',
        password: 'Password',
        rememberMe: 'Remember me',
        loginBtn: 'Login',
        
        // Dropzone
        dropzoneText: 'Drag images here or click to select',
        dropzoneHint: 'Multiple images possible',
        
        // Tools
        tools: 'Tools',
        resize: '📐 Resize',
        pixel: 'Pixel',
        percent: 'Percent',
        maxMB: 'Max MB',
        widthPx: 'Width (px):',
        heightPx: 'Height (px):',
        keepAspectRatio: 'Keep aspect ratio',
        apply: 'Apply',
        applyAll: '🔄 All',
        scaling: 'Scaling:',
        scale: 'Scale',
        maxFileSize: 'Maximum file size (MB):',
        format: 'Format:',
        quality: 'Quality:',
        compress: 'Compress',
        
        // Rotate & Flip
        rotateFlip: '🔄 Rotate & Flip',
        horizontal: '↔ Horizontal',
        vertical: '↕ Vertical',
        allImages: 'All images:',
        
        // Filters
        filters: '🎨 Filters',
        grayscale: 'Grayscale',
        blur: 'Blur:',
        blurBtn: 'Blur',
        sharpness: 'Sharpness:',
        sharpen: 'Sharpen',
        
        // Adjustments
        adjustments: '⚡ Adjustments',
        brightness: 'Brightness:',
        contrast: 'Contrast:',
        saturation: 'Saturation:',
        
        // Crop
        crop: '✂️ Crop',
        left: 'Left:',
        top: 'Top:',
        right: 'Right:',
        bottom: 'Bottom:',
        cropBtn: 'Crop',
        
        // Actions
        actions: '💾 Actions',
        reset: '↩ Reset',
        newImage: '📁 New Image',
        download: '⬇ Download',
        downloadAllZip: '📦 All as ZIP',
        
        // Gallery
        uploadedImages: '🖼️ Uploaded Images',
        addMore: '➕ Add more',
        
        // Welcome Screen
        newImagesTitle: 'Edit new images',
        newImagesDesc: 'Start fresh with new images',
        continueImagesTitle: 'Continue editing',
        continueImagesDesc: 'Resume with your saved images',
        moreImages: 'more',
        
        // Loading & Messages
        processing: 'Processing...',
        
        // Toast messages
        onlyImageFiles: 'Please upload only image files!',
        noValidImages: 'No valid images found',
        imagesAdded: 'image(s) added!',
        uploadError: 'Upload error: ',
        uploadFirst: 'Please upload an image first!',
        imageNotFound: 'Image not found!',
        resetSuccess: 'Reset!',
        applySuccess: 'Successfully applied!',
        compressedTo: 'Compressed to ~',
        newSize: 'New size:',
        processingError: 'Processing error',
        networkError: 'Network error: ',
        noImagesLoaded: 'No images loaded!',
        batchSuccess: 'of images processed!',
        batchError: 'Batch processing error',
        invalidValues: 'Please enter valid values!',
        invalidPercent: 'Please enter a valid percentage!',
        invalidFileSize: 'Please enter a valid file size!',
        invalidCropValues: 'Invalid crop values!',
        noImageToDownload: 'No image to download!',
        downloadError: 'Download error',
        imagesDownloaded: 'images downloaded!',
        imageRemoved: 'Image removed',
        storageFull: 'Storage full - older images will be removed',
        imagesNotSaved: 'Images could not be saved',
        saved: 'Saved:',
        images: 'images',
        loaded: 'Loaded:',
        imagesFromStorage: 'images from LocalStorage',
        noSavedImages: 'No saved images - showing dropzone',
        
        // Format options
        jpegSmallest: 'JPEG (smallest)',
        webpGood: 'WebP (good compression)',
        pngLossless: 'PNG (lossless)'
    },
    
    de: {
        // Header
        appTitle: 'Bildwerkzeug',
        appSubtitle: 'Bilder per Drag & Drop bearbeiten',
        admin: '⚙️ Admin',
        logout: '🚪 Abmelden',
        
        // Login
        loginSubtitle: 'Bitte melde dich an',
        username: 'Benutzername',
        password: 'Passwort',
        rememberMe: 'Angemeldet bleiben',
        loginBtn: 'Anmelden',
        
        // Dropzone
        dropzoneText: 'Bilder hierher ziehen oder klicken zum Auswählen',
        dropzoneHint: 'Mehrere Bilder möglich',
        
        // Tools
        tools: 'Werkzeuge',
        resize: '📐 Größe ändern',
        pixel: 'Pixel',
        percent: 'Prozent',
        maxMB: 'Max MB',
        widthPx: 'Breite (px):',
        heightPx: 'Höhe (px):',
        keepAspectRatio: 'Seitenverhältnis beibehalten',
        apply: 'Anwenden',
        applyAll: '🔄 Alle',
        scaling: 'Skalierung:',
        scale: 'Skalieren',
        maxFileSize: 'Maximale Dateigröße (MB):',
        format: 'Format:',
        quality: 'Qualität:',
        compress: 'Komprimieren',
        
        // Rotate & Flip
        rotateFlip: '🔄 Drehen & Spiegeln',
        horizontal: '↔ Horizontal',
        vertical: '↕ Vertikal',
        allImages: 'Alle Bilder:',
        
        // Filters
        filters: '🎨 Filter',
        grayscale: 'Graustufen',
        blur: 'Unschärfe:',
        blurBtn: 'Weichzeichnen',
        sharpness: 'Schärfe:',
        sharpen: 'Schärfen',
        
        // Adjustments
        adjustments: '⚡ Anpassungen',
        brightness: 'Helligkeit:',
        contrast: 'Kontrast:',
        saturation: 'Sättigung:',
        
        // Crop
        crop: '✂️ Zuschneiden',
        left: 'Links:',
        top: 'Oben:',
        right: 'Rechts:',
        bottom: 'Unten:',
        cropBtn: 'Zuschneiden',
        
        // Actions
        actions: '💾 Aktionen',
        reset: '↩ Zurücksetzen',
        newImage: '📁 Neues Bild',
        download: '⬇ Herunterladen',
        downloadAllZip: '📦 Alle als ZIP',
        
        // Gallery
        uploadedImages: '🖼️ Hochgeladene Bilder',
        addMore: '➕ Mehr hinzufügen',
        
        // Welcome Screen
        newImagesTitle: 'Neue Bilder bearbeiten',
        newImagesDesc: 'Mit neuen Bildern starten',
        continueImagesTitle: 'Vorhandene Bilder weiterbearbeiten',
        continueImagesDesc: 'Mit gespeicherten Bildern fortfahren',
        moreImages: 'weitere',
        
        // Loading & Messages
        processing: 'Verarbeite...',
        
        // Toast messages
        onlyImageFiles: 'Bitte nur Bilddateien hochladen!',
        noValidImages: 'Keine gültigen Bilder gefunden',
        imagesAdded: 'Bild(er) hinzugefügt!',
        uploadError: 'Fehler beim Hochladen: ',
        uploadFirst: 'Bitte zuerst ein Bild hochladen!',
        imageNotFound: 'Bild nicht gefunden!',
        resetSuccess: 'Zurückgesetzt!',
        applySuccess: 'Erfolgreich angewendet!',
        compressedTo: 'Komprimiert auf ~',
        newSize: 'Neue Größe:',
        processingError: 'Fehler bei der Verarbeitung',
        networkError: 'Netzwerkfehler: ',
        noImagesLoaded: 'Keine Bilder geladen!',
        batchSuccess: 'von Bildern bearbeitet!',
        batchError: 'Fehler bei der Batch-Verarbeitung',
        invalidValues: 'Bitte gültige Werte eingeben!',
        invalidPercent: 'Bitte gültigen Prozentwert eingeben!',
        invalidFileSize: 'Bitte gültige Dateigröße eingeben!',
        invalidCropValues: 'Ungültige Zuschnittswerte!',
        noImageToDownload: 'Kein Bild zum Herunterladen!',
        downloadError: 'Fehler beim Download',
        imagesDownloaded: 'Bilder heruntergeladen!',
        imageRemoved: 'Bild entfernt',
        storageFull: 'Speicherplatz voll - ältere Bilder werden entfernt',
        imagesNotSaved: 'Bilder konnten nicht gespeichert werden',
        saved: 'Gespeichert:',
        images: 'Bilder',
        loaded: 'Geladen:',
        imagesFromStorage: 'Bilder aus LocalStorage',
        noSavedImages: 'Keine gespeicherten Bilder - Dropzone anzeigen',
        
        // Format options
        jpegSmallest: 'JPEG (kleinste Größe)',
        webpGood: 'WebP (gute Kompression)',
        pngLossless: 'PNG (verlustfrei)'
    }
};

/**
 * Übersetzung für einen Schlüssel abrufen
 * @param {string} key - Der Übersetzungsschlüssel
 * @returns {string} - Die übersetzte Zeichenkette
 */
function t(key) {
    return translations[currentLang]?.[key] || translations['en']?.[key] || key;
}

/**
 * Sprache setzen und speichern
 * @param {string} lang - Der Sprachcode (z.B. 'en', 'de')
 */
function setLanguage(lang) {
    if (translations[lang]) {
        currentLang = lang;
        localStorage.setItem(LANG_KEY, lang);
        applyTranslations();
        updateLanguageButtons();
    }
}

/**
 * Gespeicherte oder Browser-Sprache laden
 */
function loadLanguage() {
    const savedLang = localStorage.getItem(LANG_KEY);
    if (savedLang && translations[savedLang]) {
        currentLang = savedLang;
    } else {
        // Browser-Sprache prüfen
        const browserLang = navigator.language.split('-')[0];
        currentLang = translations[browserLang] ? browserLang : 'en';
    }
}

/**
 * Übersetzungen auf alle Elemente mit data-i18n Attributen anwenden
 */
function applyTranslations() {
    // Text-Inhalt
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const translation = translations[currentLang]?.[key];
        if (translation) {
            el.textContent = translation;
        }
    });
    
    // Placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const translation = translations[currentLang]?.[key];
        if (translation) {
            el.placeholder = translation;
        }
    });
    
    // Title/Tooltip
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        const translation = translations[currentLang]?.[key];
        if (translation) {
            el.title = translation;
        }
    });
}

/**
 * Sprach-Buttons aktualisieren
 */
function updateLanguageButtons() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === currentLang);
    });
}

/**
 * Liste der verfügbaren Sprachen
 * @returns {string[]} - Array der Sprachcodes
 */
function getAvailableLanguages() {
    return Object.keys(translations);
}

/**
 * Aktuelle Sprache abrufen
 * @returns {string} - Der aktuelle Sprachcode
 */
function getCurrentLanguage() {
    return currentLang;
}
