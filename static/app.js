import interact from 'https://cdn.interactjs.io/v1.10.11/interactjs/index.js';

let scaling_factor_w;
let scaling_factor_h;
let origW;
let origH;
let currentPointsOnDisplayedImage = []; // Stores [x1,y1,x2,y2,x3,y3,x4,y4] for displayed image

const imageElement = document.getElementById('imageToCrop');
const wrapperElement = document.getElementById('wrapper');
const svgOverlayElement = document.getElementById('svgOverlay');
// console.log('DEBUG: svgOverlayElement right after declaration:', svgOverlayElement); 
const fogPathElement = document.getElementById('fogPath');
// console.log('DEBUG: fogPathElement right after declaration:', fogPathElement); 
const imageUploadElement = document.getElementById('imageUpload');
const submitBtn = document.getElementById('submitBtn');
const exportPdfBtn = document.getElementById('exportPdfBtn');
const layoutControls = document.getElementById('layoutControls');
const layoutSelect = document.getElementById('layoutSelect');
const orientationSelect = document.getElementById('orientationSelect');
const arrangeSelect = document.getElementById('arrangeSelect');
const scaleMode = document.getElementById('scaleMode');
const scalePercent = document.getElementById('scalePercent');
const processedImageElement = document.getElementById('processedImage');
const processedGallery = document.getElementById('processedGallery');
const statusMessageElement = document.getElementById('statusMessage');
const imageModal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');
const closeModal = document.getElementById('closeModal');
const langSelect = document.getElementById('langSelect');
const layoutPreview = document.getElementById('layoutPreview');
const licenseInfo = document.getElementById('licenseInfo');
const paymentBox = document.getElementById('paymentBox');
const loginArea = document.getElementById('loginArea');
const brandBox = document.getElementById('brandBox');

let isLicensed = false;
let licenseName = '';
const DEV_KEY = 'ILTUOCONSULENTEIT-DEV';
const DEV_KEY_UPPER = DEV_KEY.toUpperCase();
let userInfo = null;

let files = [];
let currentFileIndex = 0;
let processedImages = [];
let processedFiles = [];
let editingIndex = null;

let translations = {};
let currentLang = 'en';
let currentSettings = {};

async function loadSettings() {
    const url = userInfo ? '/user-settings/' : '/settings/';
    try {
        const resp = await fetch(url);
        if (resp.ok) {
            return await resp.json();
        }
    } catch (e) {
        console.error('Failed to load settings', e);
    }
    return {};
}

function saveSettings(data) {
    const url = userInfo ? '/user-settings/' : '/settings/';
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).catch(e => console.error('Save settings error', e));
}

function applySettings(cfg) {
    currentSettings = cfg;
    if (cfg.language) {
        currentLang = cfg.language;
        langSelect.value = cfg.language;
    }
    if (cfg.layout) {
        layoutSelect.value = cfg.layout;
    }
    if (cfg.orientation) {
        orientationSelect.value = cfg.orientation;
    }
    if (cfg.arrangement) {
        arrangeSelect.value = cfg.arrangement;
    }
    if (cfg.scale_mode) {
        scaleMode.value = cfg.scale_mode;
        scalePercent.style.display = scaleMode.value === 'percent' ? 'inline-block' : 'none';
    }
    if (cfg.scale_percent !== undefined) {
        scalePercent.value = cfg.scale_percent;
    }
    isLicensed = false;
    licenseName = '';
    if (cfg.license_key && cfg.license_key.trim()) {
        isLicensed = true;
    }
    if ((cfg.license_key || '').toUpperCase() === DEV_KEY_UPPER) {
        licenseName = 'Developer';
    } else if (cfg.license_name) {
        licenseName = cfg.license_name;
    }
    if (brandBox) {
        brandBox.innerHTML = cfg.brand_html || '';
    }
}

async function loadTranslations(lang) {
    try {
        const resp = await fetch(`/static/lang/${lang}.json`);
        translations = await resp.json();
    } catch (e) {
        translations = {};
    }
}

function t(key) {
    return translations[key] || key;
}

function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const k = el.getAttribute('data-i18n');
        if (translations[k]) {
            el.textContent = translations[k];
        }
    });
    // also update dynamic option labels
    orientationSelect.querySelectorAll('option').forEach(opt => {
        const k = opt.getAttribute('data-i18n');
        if (translations[k]) {
            opt.textContent = translations[k];
        }
    });
    scaleMode.querySelectorAll('option').forEach(opt => {
        const k = opt.getAttribute('data-i18n');
        if (translations[k]) {
            opt.textContent = translations[k];
        }
    });
    langSelect.querySelectorAll('option').forEach(opt => {
        const k = opt.getAttribute('data-i18n');
        if (translations[k]) {
            opt.textContent = translations[k];
        }
    });
    arrangeSelect.querySelectorAll('option').forEach(opt => {
        const k = opt.getAttribute('data-i18n');
        if (translations[k]) {
            opt.textContent = translations[k];
        }
    });
    processedGallery.querySelectorAll('.thumbButtons button').forEach(btn => {
        const key = btn.dataset.key;
        if (translations[key]) {
            btn.textContent = translations[key];
        }
    });
}

function calculateGrid() {
    const layout = parseInt(layoutSelect.value || '1');
    const orientation = orientationSelect.value || 'portrait';
    const arrangement = arrangeSelect.value || 'auto';
    let cols = 1, rows = 1;
    if (layout === 2) {
        if (arrangement === 'horizontal') {
            cols = 2; rows = 1;
        } else if (arrangement === 'vertical') {
            cols = 1; rows = 2;
        } else if (arrangement === 'auto') {
            if (orientation === 'landscape') { cols = 2; rows = 1; } else { cols = 1; rows = 2; }
        }
    } else if (layout === 4) {
        if (arrangement === 'horizontal') {
            cols = 4; rows = 1;
        } else if (arrangement === 'vertical') {
            cols = 1; rows = 4;
        } else { // grid or auto
            cols = 2; rows = 2;
        }
    }
    return {cols, rows};
}

function updateLayoutPreview() {
    const {cols, rows} = calculateGrid();
    layoutPreview.innerHTML = '';
    const orientation = orientationSelect.value || 'portrait';
    layoutPreview.style.display = 'block';
    layoutPreview.style.width = orientation === 'portrait' ? '200px' : '250px';
    layoutPreview.style.height = orientation === 'portrait' ? '250px' : '200px';
    layoutPreview.style.display = 'grid';
    layoutPreview.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    layoutPreview.style.gridTemplateRows = `repeat(${rows}, 1fr)`;
    const total = cols * rows;
    for (let i = 0; i < total; i++) {
        const cell = document.createElement('div');
        cell.className = 'cell';
        layoutPreview.appendChild(cell);
    }
}

function openModal(src) {
    modalImage.src = src;
    imageModal.style.display = 'block';
}

function rotateImage(index) {
    const img = new Image();
    img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.height;
        canvas.height = img.width;
        const ctx = canvas.getContext('2d');
        ctx.translate(canvas.width / 2, canvas.height / 2);
        ctx.rotate(Math.PI / 2);
        ctx.drawImage(img, -img.width / 2, -img.height / 2);
        const rotatedData = canvas.toDataURL('image/png');
        processedImages[index] = rotatedData;
        const container = processedGallery.children[index];
        container.querySelector('img').src = rotatedData;
        if (imageModal.style.display === 'block') {
            openModal(rotatedData);
        }
    };
    img.src = processedImages[index];
}

function deleteImage(index) {
    processedImages.splice(index, 1);
    processedFiles.splice(index, 1);
    processedGallery.removeChild(processedGallery.children[index]);
    if (processedImages.length === 0) {
        exportPdfBtn.style.display = 'none';
        layoutControls.style.display = 'none';
    }
}

function editImage(index) {
    editingIndex = index;
    const file = processedFiles[index];
    const reader = new FileReader();
    reader.onload = (e) => {
        setupImage(e.target.result);
    };
    reader.readAsDataURL(file);
    exportPdfBtn.style.display = 'none';
    layoutControls.style.display = 'none';
    statusMessageElement.textContent = 'Edit image and press Process Image to save.';
}

function addThumbnail(src, index) {
    const container = document.createElement('div');
    container.className = 'thumbContainer';

    const imgEl = document.createElement('img');
    imgEl.src = src;
    imgEl.addEventListener('click', () => {
        const idx = Array.from(processedGallery.children).indexOf(container);
        openModal(processedImages[idx]);
    });
    container.appendChild(imgEl);

    const btns = document.createElement('div');
    btns.className = 'thumbButtons';

    const rotateBtn = document.createElement('button');
    rotateBtn.dataset.key = 'rotate';
    rotateBtn.textContent = t('rotate');
    rotateBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const idx = Array.from(processedGallery.children).indexOf(container);
        rotateImage(idx);
    });
    btns.appendChild(rotateBtn);

    const editBtn = document.createElement('button');
    editBtn.dataset.key = 'edit';
    editBtn.textContent = t('edit');
    editBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const idx = Array.from(processedGallery.children).indexOf(container);
        editImage(idx);
    });
    btns.appendChild(editBtn);

    const delBtn = document.createElement('button');
    delBtn.dataset.key = 'delete';
    delBtn.textContent = t('delete');
    delBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const idx = Array.from(processedGallery.children).indexOf(container);
        deleteImage(idx);
    });
    btns.appendChild(delBtn);

    container.appendChild(btns);
    processedGallery.appendChild(container);
}

closeModal.addEventListener('click', () => {
    imageModal.style.display = 'none';
});

imageModal.addEventListener('click', (e) => {
    if (e.target === imageModal) {
        imageModal.style.display = 'none';
    }
});

const draggableElements = {
    p1: document.getElementById('p1'),
    p2: document.getElementById('p2'),
    p3: document.getElementById('p3'),
    p4: document.getElementById('p4'),
};

function updatePolygonAndPoints() {
    const displayedPoints = [];
    // Order: p1 (TL), p2 (TR), p3 (BR), p4 (BL)
    console.log("--- Updating Polygon ---"); // General log to see if function is called

    ['p1', 'p2', 'p3', 'p4'].forEach((id, index) => {
        const dragEl = draggableElements[id];

        // Detailed logging for the first point (p1) for clarity during debugging
        if (index === 0) { // Only log verbosely for p1 to avoid console spam
            console.log(`--- Debug Point ${id} ---`);
            console.log(`Element style.left: '${dragEl.style.left}', style.top: '${dragEl.style.top}'`);
        }

        const initialLeft = parseFloat(dragEl.style.left || "0"); // Ensure string "0" if style is empty
        const initialTop = parseFloat(dragEl.style.top || "0");  // Ensure string "0" if style is empty
        
        const dataX = dragEl.getAttribute('data-x');
        const dataY = dragEl.getAttribute('data-y');
        const translateX = parseFloat(dataX || "0");
        const translateY = parseFloat(dataY || "0");

        if (index === 0) {
            console.log(`InitialLeft: ${initialLeft}, InitialTop: ${initialTop}`);
            console.log(`Attribute data-x: '${dataX}', data-y: '${dataY}'`);
            console.log(`TranslateX: ${translateX}, TranslateY: ${translateY}`);
            console.log(`OffsetWidth: ${dragEl.offsetWidth}, OffsetHeight: ${dragEl.offsetHeight}`);
        }

        const x = initialLeft + translateX + (dragEl.offsetWidth / 2);
        const y = initialTop + translateY + (dragEl.offsetHeight / 2);
        
        if (index === 0) {
            console.log(`Calculated center x: ${x}, y: ${y}`);
        }
        
        displayedPoints.push(x, y);
    });
    currentPointsOnDisplayedImage = displayedPoints;
    // console.log("Displayed Points for SVG:", JSON.stringify(currentPointsOnDisplayedImage));


    const imgWidth = imageElement.offsetWidth;
    const imgHeight = imageElement.offsetHeight;

    if (!fogPathElement) {
        console.error("ERROR: fogPathElement is null in updatePolygonAndPoints. Cannot draw fog.");
        return;
    }

    if (imgWidth > 0 && imgHeight > 0 && currentPointsOnDisplayedImage.length === 8) {
        const p = currentPointsOnDisplayedImage;
        const pathData = `M0,0 H${imgWidth} V${imgHeight} H0 Z ` +
                         `M${p[0]},${p[1]} L${p[2]},${p[3]} L${p[4]},${p[5]} L${p[6]},${p[7]} Z`;
        // console.log("SVG Path Data:", pathData);
        fogPathElement.setAttribute('d', pathData);
    } else {
        // console.log("Skipping fog path update (imgWidth/Height or points invalid)");
        fogPathElement.setAttribute('d', '');
    }
}

function initializeDraggablePoints(imgDisplayWidth, imgDisplayHeight) {
    const pointSize = draggableElements.p1.offsetWidth;

    Object.values(draggableElements).forEach(el => {
        el.style.transform = 'translate(0px, 0px)';
        el.setAttribute('data-x', '0');
        el.setAttribute('data-y', '0');
    });
    
    draggableElements.p1.style.top = `0px`;
    draggableElements.p1.style.left = `0px`;
    draggableElements.p2.style.top = `0px`;
    draggableElements.p2.style.left = `${imgDisplayWidth - pointSize}px`;
    draggableElements.p3.style.top = `${imgDisplayHeight - pointSize}px`;
    draggableElements.p3.style.left = `${imgDisplayWidth - pointSize}px`;
    draggableElements.p4.style.top = `${imgDisplayHeight - pointSize}px`;
    draggableElements.p4.style.left = `0px`;

    updatePolygonAndPoints();
}

function setupImage(imageUrl) {
    imageElement.src = imageUrl;
    imageElement.style.display = 'block';
    wrapperElement.style.display = 'block';
    processedImageElement.style.display = 'none';
    statusMessageElement.textContent = 'Loading image...';

    imageElement.onload = () => {
        origW = imageElement.naturalWidth;
        origH = imageElement.naturalHeight;

        if (origW === 0 || origH === 0) {
            console.error("Image natural dimensions are zero. Image might be invalid or not loaded.");
            statusMessageElement.textContent = "Error: Image data is invalid or not fully loaded.";
            wrapperElement.style.display = 'none';
            return;
        }

        let displayWidthForWrapper;
        let displayHeightForWrapper;
        const MAX_DISPLAY_WIDTH = Math.min(window.innerWidth * 0.9, 800);
        const MAX_DISPLAY_HEIGHT = Math.min(window.innerHeight * 0.8, 700);

        if (origW > MAX_DISPLAY_WIDTH || origH > MAX_DISPLAY_HEIGHT) {
            const widthRatio = MAX_DISPLAY_WIDTH / origW;
            const heightRatio = MAX_DISPLAY_HEIGHT / origH;
            const scale = Math.min(widthRatio, heightRatio); 
            displayWidthForWrapper = origW * scale;
            displayHeightForWrapper = origH * scale;
        } else {
            displayWidthForWrapper = origW;
            displayHeightForWrapper = origH;
        }
        
        wrapperElement.style.width = `${displayWidthForWrapper}px`;
        wrapperElement.style.height = `${displayHeightForWrapper}px`;

        setTimeout(() => {
            const actualDisplayedWidth = imageElement.offsetWidth;
            const actualDisplayedHeight = imageElement.offsetHeight;

            // console.log(`Image Loaded: Natural WxH: ${origW}x${origH}`);
            // console.log(`Wrapper target WxH: ${displayWidthForWrapper.toFixed(2)}x${displayHeightForWrapper.toFixed(2)}`);
            // console.log(`Image actual displayed WxH: ${actualDisplayedWidth}x${actualDisplayedHeight}`);
            
            // console.log('DEBUG: svgOverlayElement inside setTimeout, before setAttribute:', svgOverlayElement);
            if (!svgOverlayElement) {
                console.error('ERROR: svgOverlayElement is NULL or UNDEFINED at the point of setAttribute!');
                statusMessageElement.textContent = "Critical Error: SVG Overlay element not found. Cannot draw fog.";
                return; 
            }
            if (!fogPathElement) {
                 console.error('ERROR: fogPathElement is NULL or UNDEFINED before initializeDraggablePoints!');
                 statusMessageElement.textContent = "Critical Error: SVG Fog Path element not found.";
                 return;
            }

            if (actualDisplayedWidth === 0 || actualDisplayedHeight === 0) {
                console.error("Image displayed dimensions are zero even after setting wrapper. Check CSS or layout timing.");
                statusMessageElement.textContent = "Error: Image failed to render with correct dimensions.";
                return;
            }

            scaling_factor_w = origW / actualDisplayedWidth;
            scaling_factor_h = origH / actualDisplayedHeight;

            // console.log(`Scaling factors: W=${scaling_factor_w}, H=${scaling_factor_h}`);

            svgOverlayElement.setAttribute('viewBox', `0 0 ${actualDisplayedWidth} ${actualDisplayedHeight}`);
            svgOverlayElement.setAttribute('width', actualDisplayedWidth);
            svgOverlayElement.setAttribute('height', actualDisplayedHeight);
            
            initializeDraggablePoints(actualDisplayedWidth, actualDisplayedHeight);
            statusMessageElement.textContent = 'Image loaded. Adjust points.';
        }, 50); 

    };

    imageElement.onerror = () => {
        console.error("Error loading image source.");
        statusMessageElement.textContent = "Error: Could not load the selected image file.";
        wrapperElement.style.display = 'none';
    };
}


imageUploadElement.addEventListener('change', (event) => {
    files = Array.from(event.target.files);
    currentFileIndex = 0;
    processedImages = [];
    processedFiles = [];
    editingIndex = null;
    processedGallery.innerHTML = '';
    exportPdfBtn.style.display = 'none';
    layoutControls.style.display = 'none';
    if (files.length > 0) {
        const reader = new FileReader();
        reader.onload = (e) => {
            setupImage(e.target.result);
        };
        reader.readAsDataURL(files[0]);
    }
});

interact('.draggable').draggable({
    modifiers: [
        interact.modifiers.restrictRect({
            restriction: 'parent',
            endOnly: false,
            elementRect: { left: 0.5, top: 0.5, right: 0.5, bottom: 0.5 }
        })
    ],
    listeners: {
        move(event) {
            const target = event.target;
            let x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
            let y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

            target.style.transform = `translate(${x}px, ${y}px)`;
            target.setAttribute('data-x', x);
            target.setAttribute('data-y', y);

            updatePolygonAndPoints();
        }
    }
});


submitBtn.addEventListener('click', () => {
    if (!imageUploadElement.files || imageUploadElement.files.length === 0) {
        statusMessageElement.textContent = 'Please upload an image first.';
        return;
    }
    if (currentPointsOnDisplayedImage.length !== 8) {
        statusMessageElement.textContent = 'Points not initialized correctly or image not fully loaded.';
        return;
    }
     if (!origW || !origH || !scaling_factor_w || !scaling_factor_h ) {
        statusMessageElement.textContent = 'Image properties (origW, origH, scaling factors) not set. Please re-upload.';
        return;
    }

    statusMessageElement.textContent = 'Processing...';

    const pointsForBackend = currentPointsOnDisplayedImage.map((coord, index) => {
        const scale = index % 2 === 0 ? Number(scaling_factor_w) : Number(scaling_factor_h);
        return coord * scale;
    });

    // console.log("--- Frontend Data for Backend ---");
    // console.log("currentPointsOnDisplayedImage (displayed GUI coords):", JSON.stringify(currentPointsOnDisplayedImage));
    // console.log(`scaling_factor_w: ${scaling_factor_w}, scaling_factor_h: ${scaling_factor_h}`);
    // console.log(`origW (natural): ${origW}, origH (natural): ${origH}`);
    // console.log("pointsForBackend (scaled to original image):", JSON.stringify(pointsForBackend));

    const currentFile = editingIndex !== null ? processedFiles[editingIndex] : files[currentFileIndex];
    const formData = new FormData();
    formData.append('image_file', currentFile);
    formData.append('points', JSON.stringify(pointsForBackend));
    formData.append('original_width', Math.round(origW));
    formData.append('original_height', Math.round(origH));

    fetch('/process-image/', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.detail || err.message || `HTTP error! status: ${response.status}`) });
        }
        return response.json();
    })
    .then(data => {
        if (data.processed_image) {
            processedImageElement.src = data.processed_image;
            openModal(data.processed_image);
            if (editingIndex !== null) {
                processedImages[editingIndex] = data.processed_image;
                const container = processedGallery.children[editingIndex];
                container.querySelector('img').src = data.processed_image;
                editingIndex = null;
                statusMessageElement.textContent = 'Image reprocessed.';
                wrapperElement.style.display = 'none';
                exportPdfBtn.style.display = 'inline-block';
                layoutControls.style.display = 'block';
                updateLayoutPreview();
            } else {
                processedImages.push(data.processed_image);
                processedFiles.push(currentFile);
                addThumbnail(data.processed_image, processedImages.length - 1);
                currentFileIndex++;
                if (currentFileIndex < files.length) {
                    statusMessageElement.textContent = 'Image processed. Load next...';
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        setupImage(e.target.result);
                    };
                    reader.readAsDataURL(files[currentFileIndex]);
                } else {
                    statusMessageElement.textContent = 'All images processed.';
                    wrapperElement.style.display = 'none';
                    exportPdfBtn.style.display = 'inline-block';
                    layoutControls.style.display = 'block';
                    updateLayoutPreview();
                }
            }
        } else {
            statusMessageElement.textContent = data.message || 'Failed to process image.';
        }
    })
    .catch(error => {
        console.error('Error submitting for processing:', error);
        statusMessageElement.textContent = `Error: ${error.message}`;
    });
});

exportPdfBtn.addEventListener('click', () => {
    if (processedImages.length === 0) {
        statusMessageElement.textContent = 'No processed images to export.';
        return;
    }
    statusMessageElement.textContent = 'Generating PDF...';
    const layout = parseInt(layoutSelect.value || '1');
    const orientation = orientationSelect.value || 'portrait';
    const arrangement = arrangeSelect.value || 'auto';
    const scale_mode = scaleMode.value || 'fit';
    const scale_percent = parseInt(scalePercent.value || '100');
    const payload = { images: processedImages, layout, orientation, arrangement, scale_mode, scale_percent };
    fetch('/create-pdf/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.detail || err.message || `HTTP error! status: ${response.status}`) });
        }
        return response.json();
    })
    .then(data => {
        if (data.pdf) {
            const link = document.createElement('a');
            link.href = data.pdf;
            link.download = 'documents.pdf';
            link.click();
            statusMessageElement.textContent = 'PDF generated.';
        } else {
            statusMessageElement.textContent = data.message || 'Failed to create PDF.';
        }
    })
    .catch(error => {
        console.error('Error creating PDF:', error);
        statusMessageElement.textContent = `Error: ${error.message}`;
    });
});

langSelect.addEventListener('change', async () => {
    currentLang = langSelect.value;
    await loadTranslations(currentLang);
    applyTranslations();
    renderPaymentBox(currentSettings);
    saveSettings({ language: currentLang });
});

layoutSelect.addEventListener('change', () => {
    updateLayoutPreview();
    saveSettings({ layout: parseInt(layoutSelect.value || '1') });
});

orientationSelect.addEventListener('change', () => {
    updateLayoutPreview();
    saveSettings({ orientation: orientationSelect.value });
});

arrangeSelect.addEventListener('change', () => {
    updateLayoutPreview();
    saveSettings({ arrangement: arrangeSelect.value });
});

scaleMode.addEventListener('change', () => {
    scalePercent.style.display = scaleMode.value === 'percent' ? 'inline-block' : 'none';
    saveSettings({ scale_mode: scaleMode.value, scale_percent: parseInt(scalePercent.value || '100') });
});

scalePercent.addEventListener('change', () => {
    saveSettings({ scale_percent: parseInt(scalePercent.value || '100') });
});

function applyProStatus() {
    // In demo mode features remain usable but PDF pages beyond the first
    // will include a DEMO watermark. We simply update the button style
    // to reflect the license status without disabling functionality.
    if (!isLicensed) {
        exportPdfBtn.classList.remove('pro-disabled');
        imageUploadElement.multiple = true;
    } else {
        exportPdfBtn.classList.remove('pro-disabled');
        imageUploadElement.multiple = true;
    }
}

function renderPaymentBox(cfg) {
    if (!cfg || !cfg.payment_mode) {
        paymentBox.style.display = 'none';
        return;
    }
    const mode = cfg.payment_mode.toLowerCase();
    if (mode === 'none') {
        paymentBox.style.display = 'none';
        return;
    }
    paymentBox.style.display = 'block';
    let html = `<h3>${t('support')}</h3><ul>`;
    let hasItem = false;
    if (mode === 'donation') {
        if (cfg.paypal_link) {
            html += `<li><a href="${cfg.paypal_link}" target="_blank">${t('donatePaypal')}</a></li>`;
            hasItem = true;
        }
    } else if (mode === 'subscription') {
        if (cfg.paypal_link) {
            html += `<li><a href="${cfg.paypal_link}" target="_blank">${t('payPaypal')}</a></li>`;
            hasItem = true;
        }
        if (cfg.stripe_link) {
            html += `<li><a href="${cfg.stripe_link}" target="_blank">${t('payStripe')}</a></li>`;
            hasItem = true;
        }
        if (cfg.bank_info) {
            html += `<li>${t('bankInfo')}: ${cfg.bank_info}</li>`;
            hasItem = true;
        }
    }
    if (!hasItem) {
        html += `<li>${t('noPaymentInfo')}</li>`;
    }
    html += '</ul>';
    paymentBox.innerHTML = html;
}

function renderLogin(cfg) {
    if (!cfg || !cfg.google_client_id) {
        loginArea.style.display = 'block';
        loginArea.textContent = t('loginDisabled');
        return;
    }
    loginArea.style.display = 'block';
    function init() {
        google.accounts.id.initialize({
            client_id: cfg.google_client_id,
            callback: async (response) => {
                const res = await fetch('/google-login/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token: response.credential})
                });
                if (res.ok) {
                    const data = await res.json();
                    userInfo = data;
                    loginArea.innerHTML = `${t('loggedInAs')} ${data.name || data.email} <button id="signOutBtn">${t('signOut')}</button>`;
                    document.getElementById('signOutBtn').addEventListener('click', async () => {
                        google.accounts.id.disableAutoSelect();
                        userInfo = null;
                        loginArea.innerHTML = '';
                        renderLogin(cfg);
                        const baseCfg = await loadSettings();
                        applySettings(baseCfg);
                        await loadTranslations(currentLang);
                        applyTranslations();
                        renderPaymentBox(baseCfg);
                        licenseInfo.textContent = isLicensed ? `${t('licensedTo')} ${licenseName}` : t('demoVersion');
                        applyProStatus();
                        updateLayoutPreview();
                    });
                    const newCfg = await loadSettings();
                    applySettings(newCfg);
                    await loadTranslations(currentLang);
                    applyTranslations();
                    renderPaymentBox(newCfg);
                    licenseInfo.textContent = isLicensed ? `${t('licensedTo')} ${licenseName}` : t('demoVersion');
                    applyProStatus();
                    updateLayoutPreview();
                } else {
                    loginArea.textContent = t('signInFailed');
                }
            }
        });
        google.accounts.id.renderButton(loginArea, {theme: 'outline', size: 'medium'});
    }
    if (typeof google === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.onload = init;
        document.head.appendChild(script);
    } else {
        init();
    }
}

// initial load of settings and translations
loadSettings().then(async (cfg) => {
    applySettings(cfg);
    await loadTranslations(currentLang);
    applyTranslations();
    renderPaymentBox(cfg);
    renderLogin(cfg);
    licenseInfo.textContent = isLicensed ? `${t('licensedTo')} ${licenseName}` : t('demoVersion');
    applyProStatus();
    updateLayoutPreview();
});

if (window.safari) {
    history.pushState(null, null, location.href);
    window.onpopstate = function(event) {
        history.go(1);
    };
}
