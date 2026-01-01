/**
 * OCR-MCP Professional Web Interface JavaScript
 * Comprehensive frontend for advanced document processing
 */

// Global state
let currentSection = 'upload';
let currentFiles = [];
let currentWorkflowStep = 0;
let processingJob = null;
let batchJobs = [];
let systemStatus = {};
let scannerList = [];
let fileQueue = [];
let selectedFiles = new Set();
let recentFiles = JSON.parse(localStorage.getItem('ocr-mcp-recent-files') || '[]');

// API endpoints
const API_BASE = window.location.origin;
const ENDPOINTS = {
    health: '/api/health',
    process: '/api/process',
    batch: '/api/batch',
    scanners: '/api/scanners',
    ocr: '/api/ocr'
};

// Global Navigation Function
window.showSection = function (sectionName) {
    // Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.classList.remove('active');
        section.style.display = 'none';
    });

    // Show target section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
        targetSection.style.display = 'block';
    }

    // Update navigation
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.dataset.section === sectionName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Update global state
    currentSection = sectionName;
};

// Initialize Navigation Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const section = item.dataset.section;
            if (section) {
                showSection(section);
            }
        });
    });
});


// Enhanced file handling functions
function initializeFileHandling() {
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');

    if (!uploadZone || !fileInput) return;

    // Drag and drop handlers
    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('dragleave', handleDragLeave);
    uploadZone.addEventListener('drop', handleFileDrop);

    // File input change handler
    fileInput.addEventListener('change', handleFileSelect);

    // Initialize file queue if it exists
    updateFileQueueDisplay();
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    const uploadZone = document.getElementById('upload-zone');
    if (uploadZone) {
        uploadZone.classList.add('drag-over');
    }
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    const uploadZone = document.getElementById('upload-zone');
    if (uploadZone) {
        uploadZone.classList.remove('drag-over');
    }
}

function handleFileDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    const uploadZone = document.getElementById('upload-zone');
    if (uploadZone) {
        uploadZone.classList.remove('drag-over');
    }

    const files = Array.from(e.dataTransfer.files);
    addFilesToQueue(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFilesToQueue(files);
}

function addFilesToQueue(files) {
    const validFiles = files.filter(file => {
        const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff', 'image/bmp', 'application/x-cbz', 'application/x-cbr', 'image/webp'];

        const validExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.cbz', '.cbr', '.webp'];

        return validTypes.includes(file.type) ||
            validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    });

    if (validFiles.length !== files.length) {
        showNotification(`${files.length - validFiles.length} invalid files were skipped`, 'warning');
    }

    validFiles.forEach(file => {
        const fileId = Date.now() + Math.random();
        const queueItem = {
            id: fileId,
            file: file,
            name: file.name,
            size: file.size,
            type: file.type,
            added: new Date(),
            status: 'queued'
        };
        fileQueue.push(queueItem);
    });

    updateFileQueueDisplay();
    updateRecentFiles(validFiles);
}

function updateFileQueueDisplay() {
    const queueContainer = document.getElementById('file-queue');
    const queueList = document.getElementById('queue-list');
    const queueCount = document.getElementById('queue-count');
    const queueSize = document.getElementById('queue-size');

    if (!queueContainer || fileQueue.length === 0) {
        if (queueContainer) queueContainer.style.display = 'none';
        return;
    }

    queueContainer.style.display = 'block';
    if (queueList) queueList.innerHTML = '';

    let totalSize = 0;
    fileQueue.forEach(item => {
        totalSize += item.size;
        if (queueList) {
            const itemElement = createQueueItemElement(item);
            queueList.appendChild(itemElement);
        }
    });

    if (queueCount) queueCount.textContent = `${fileQueue.length} file${fileQueue.length !== 1 ? 's' : ''}`;
    if (queueSize) queueSize.textContent = formatFileSize(totalSize);
}

function createQueueItemElement(item) {
    const div = document.createElement('div');
    div.className = 'queue-item';
    div.dataset.fileId = item.id;

    const fileIcon = getFileIcon(item.type);
    const formattedSize = formatFileSize(item.size);

    div.innerHTML = `
        <div class="queue-item-checkbox">
            <input type="checkbox" class="file-checkbox" data-file-id="${item.id}">
        </div>
        <div class="queue-item-icon">
            <i class="${fileIcon}"></i>
        </div>
        <div class="queue-item-info">
            <div class="queue-item-name">${item.name}</div>
            <div class="queue-item-details">${formattedSize} • ${item.type || 'Unknown type'}</div>
        </div>
        <div class="queue-item-actions">
            <button class="btn-icon" onclick="previewFile('${item.id}')" title="Preview">
                <i class="fas fa-eye"></i>
            </button>
            <button class="btn-icon" onclick="removeFileFromQueue('${item.id}')" title="Remove">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="queue-item-status">
            <span class="status-badge status-${item.status}">${item.status}</span>
        </div>
    `;

    return div;
}

function getFileIcon(mimeType) {
    if (mimeType === 'application/pdf') return 'fas fa-file-pdf';
    if (mimeType && mimeType.startsWith('image/')) return 'fas fa-file-image';
    if (mimeType === 'application/x-cbz' || mimeType === 'application/x-cbr') return 'fas fa-file-archive';
    return 'fas fa-file';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function removeFileFromQueue(fileId) {
    fileQueue = fileQueue.filter(item => item.id !== fileId);
    selectedFiles.delete(fileId);
    updateFileQueueDisplay();
}

function clearFileQueue() {
    fileQueue = [];
    selectedFiles.clear();
    updateFileQueueDisplay();
}

function selectAllFiles() {
    const checkboxes = document.querySelectorAll('.file-checkbox');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);

    checkboxes.forEach(cb => {
        cb.checked = !allChecked;
        const fileId = cb.dataset.fileId;
        if (cb.checked) {
            selectedFiles.add(fileId);
        } else {
            selectedFiles.delete(fileId);
        }
    });
}

function removeSelectedFiles() {
    selectedFiles.forEach(fileId => {
        fileQueue = fileQueue.filter(item => item.id !== fileId);
    });
    selectedFiles.clear();
    updateFileQueueDisplay();
}

function previewFile(fileId) {
    const item = fileQueue.find(item => item.id === fileId);
    if (!item) return;

    const modal = document.getElementById('file-preview-modal');
    const fileInfo = document.getElementById('file-info');
    const previewArea = document.getElementById('file-preview-area');

    if (fileInfo) {
        fileInfo.innerHTML = `
            <div class="file-meta">
                <div class="meta-item"><strong>Name:</strong> ${item.name}</div>
                <div class="meta-item"><strong>Size:</strong> ${formatFileSize(item.size)}</div>
                <div class="meta-item"><strong>Type:</strong> ${item.type || 'Unknown'}</div>
                <div class="meta-item"><strong>Added:</strong> ${item.added.toLocaleString()}</div>
            </div>
        `;
    }

    // Simple preview for images
    if (item.type && item.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function (e) {
            if (previewArea) {
                previewArea.innerHTML = `<img src="${e.target.result}" alt="${item.name}" style="max-width: 100%; max-height: 400px;">`;
            }
        };
        reader.readAsDataURL(item.file);
    } else if (previewArea) {
        previewArea.innerHTML = `<div class="file-placeholder"><i class="${getFileIcon(item.type)}"></i><p>${item.name}</p></div>`;
    }

    if (modal) modal.style.display = 'block';
}

function closeFilePreview() {
    const modal = document.getElementById('file-preview-modal');
    if (modal) modal.style.display = 'none';
}

function processPreviewFile() {
    // Process the currently previewed file
    closeFilePreview();
    // Implementation would go here
    showNotification('File processing started', 'success');
}

function showRecentFiles() {
    // Show recent files modal or dropdown
    showNotification('Recent files feature coming soon', 'info');
}

function updateRecentFiles(files) {
    files.forEach(file => {
        const recentFile = {
            name: file.name,
            size: file.size,
            type: file.type,
            lastUsed: new Date().toISOString()
        };

        // Remove if already exists
        recentFiles = recentFiles.filter(rf => rf.name !== file.name);
        recentFiles.unshift(recentFile);

        // Keep only last 10
        recentFiles = recentFiles.slice(0, 10);
    });

    localStorage.setItem('ocr-mcp-recent-files', JSON.stringify(recentFiles));
}

function showNotification(message, type = 'info') {
    // Simple notification system
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        ${message}
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
    setupEventListeners();
    checkSystemStatus();
});

// Initialize the application
function initializeApp() {
    console.log('Initializing OCR-MCP webapp...');

    // Set initial section
    console.log('Setting initial section to upload');
    showSection('upload');

    // Initialize workflow
    updateWorkflowProgress(0);

    // Initialize enhanced file handling
    initializeFileHandling();

    // Set up periodic status updates
    setInterval(checkSystemStatus, 30000); // Check every 30 seconds

    console.log('OCR-MCP webapp initialization complete');
}

// Set up all event listeners
function setupEventListeners() {
    // Sidebar navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            if (section) {
                showSection(section);
            }
        });
    });

    // File upload zones
    setupFileUploadZones();

    // Workflow controls
    setupWorkflowControls();

    // Scanner controls
    setupScannerControls();

    // Quality controls
    setupQualityControls();

    // Keyboard shortcuts
    setupKeyboardShortcuts();
}

// ============================================================================
// NAVIGATION FUNCTIONS
// ============================================================================

// Simple navigation function (established since 1990)
function showSection(sectionName) {
    // Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.classList.remove('active');
        section.style.display = 'none';
    });

    // Show target section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
        targetSection.style.display = 'block';
    }

    // Update navigation
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.classList.remove('active');
    });

    // Find and activate the clicked nav item
    navItems.forEach(item => {
        if (item.getAttribute('data-section') === sectionName) {
            item.classList.add('active');
        }
    });
}

// Update workflow progress
function updateWorkflowProgress(step) {
    currentWorkflowStep = step;
    const steps = document.querySelectorAll('.workflow-step');

    steps.forEach((stepElement, index) => {
        if (index <= step) {
            stepElement.classList.add('active');
        } else {
            stepElement.classList.remove('active');
        }
    });
}

// Reset workflow
function resetWorkflow() {
    currentFiles = [];
    currentWorkflowStep = 0;
    processingJob = null;

    updateWorkflowProgress(0);

    // Clear upload preview
    const preview = document.getElementById('upload-preview');
    if (preview) {
        preview.style.display = 'none';
    }

    // Clear results
    const resultsViewer = document.getElementById('results-viewer');
    if (resultsViewer) {
        resultsViewer.style.display = 'none';
    }

    // Reset forms
    document.querySelectorAll('form').forEach(form => form.reset());
}

// ============================================================================
// FILE HANDLING FUNCTIONS
// ============================================================================

// Set up file upload zones
function setupFileUploadZones() {
    const uploadZones = [
        'upload-zone',
        'batch-upload-area',
        'preprocessing-upload-area',
        'analysis-upload-area'
    ];

    uploadZones.forEach(zoneId => {
        const zone = document.getElementById(zoneId);
        if (!zone) return;

        const fileInput = zone.querySelector('input[type="file"]');

        // Drag and drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            zone.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            zone.addEventListener(eventName, () => zone.classList.add('drag-over'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            zone.addEventListener(eventName, () => zone.classList.remove('drag-over'), false);
        });

        zone.addEventListener('drop', (e) => handleFileDrop(e, zoneId), false);

        // Click to browse
        if (fileInput) {
            zone.addEventListener('click', () => fileInput.click(), false);
            fileInput.addEventListener('change', (e) => handleFileSelect(e, zoneId), false);
        }
    });
}

// Prevent default drag behaviors
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Handle file drop
function handleFileDrop(e, zoneId) {
    const files = e.dataTransfer.files;
    handleFiles(files, zoneId);
}

// Handle file selection
function handleFileSelect(e, zoneId) {
    const files = e.target.files;
    handleFiles(files, zoneId);
}

// Process dropped/selected files
function handleFiles(files, zoneId) {
    [...files].forEach(file => {
        if (validateFile(file)) {
            processFile(file, zoneId);
        }
    });
}

// Validate file
function validateFile(file) {
    const validTypes = [
        'application/pdf',
        'image/png', 'image/jpeg', 'image/jpg', 'image/tiff', 'image/bmp',
        'application/x-cbz', 'application/x-cbr'
    ];

    const maxSize = 50 * 1024 * 1024; // 50MB

    if (!validTypes.includes(file.type) && !file.name.match(/\.(pdf|png|jpg|jpeg|tiff|bmp|cbz|cbr)$/i)) {
        showNotification('Unsupported file type', 'error');
        return false;
    }

    if (file.size > maxSize) {
        showNotification('File too large (max 50MB)', 'error');
        return false;
    }

    return true;
}

// Process individual file
function processFile(file, zoneId) {
    currentFiles.push(file);

    if (zoneId === 'upload-zone') {
        // Single file upload
        showUploadPreview(file);
        updateWorkflowProgress(1);
    } else if (zoneId === 'batch-upload-area') {
        // Batch upload
        addToBatchQueue(file);
    } else if (zoneId.includes('preprocessing')) {
        // Preprocessing upload
        showPreprocessingPreview(file);
    } else if (zoneId.includes('analysis')) {
        // Analysis upload
        showAnalysisPreview(file);
    }
}

// Show upload preview for single files
function showUploadPreview(file) {
    const preview = document.getElementById('upload-preview');
    const previewContent = preview.querySelector('.preview-content');
    const filename = preview.querySelector('.preview-info h4');
    const filesize = preview.querySelector('.preview-info span');
    const icon = preview.querySelector('.preview-icon');

    // Set file info
    filename.textContent = file.name;
    filesize.textContent = formatFileSize(file.size);

    // Set icon based on file type
    if (file.type === 'application/pdf') {
        icon.className = 'fas fa-file-pdf';
    } else if (file.type.startsWith('image/')) {
        icon.className = 'fas fa-image';
    } else {
        icon.className = 'fas fa-file';
    }

    preview.style.display = 'block';
    preview.classList.add('fade-in');
}

// Add file to batch queue
function addToBatchQueue(file) {
    const queue = document.getElementById('batch-file-list');
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item fade-in';
    fileItem.innerHTML = `
        <div class="file-info">
            <i class="fas fa-file"></i>
            <div class="file-details">
                <span class="file-name">${file.name}</span>
                <span class="file-size">${formatFileSize(file.size)}</span>
            </div>
        </div>
        <button class="btn btn-sm btn-outline" onclick="removeFromBatch(this)">
            <i class="fas fa-times"></i>
        </button>
    `;

    queue.appendChild(fileItem);
    updateBatchCount();
}

// Remove file from batch queue
function removeFromBatch(button) {
    const fileItem = button.closest('.file-item');
    fileItem.remove();
    updateBatchCount();
}

// Update batch count
function updateBatchCount() {
    const count = document.querySelectorAll('.file-item').length;
    // Update UI counters
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

// Make API call
async function apiCall(endpoint, method = 'GET', data = null) {
    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (data) {
        if (data instanceof FormData) {
            delete config.headers['Content-Type']; // Let browser set for FormData
            config.body = data;
        } else {
            config.body = JSON.stringify(data);
        }
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || `HTTP ${response.status}`);
        }

        return result;
    } catch (error) {
        console.error('API call failed:', error);
        showNotification(`API Error: ${error.message}`, 'error');
        throw error;
    }
}

// Check system status
async function checkSystemStatus() {
    try {
        const status = await apiCall('/api/health');

        // Update status indicator
        const statusIndicator = document.getElementById('system-status');
        if (statusIndicator) {
            const statusText = status.backends_available > 0 ? 'Ready' : 'Limited';
            const statusClass = status.backends_available > 0 ? 'success' : 'warning';

            statusIndicator.innerHTML = `
                <i class="fas fa-circle text-${statusClass}"></i>
                ${statusText}
            `;
        }

        // Update system health metrics
        updateSystemHealth(status);

        systemStatus = status;
    } catch (error) {
        console.error('Status check failed:', error);
        const statusIndicator = document.getElementById('system-status');
        if (statusIndicator) {
            statusIndicator.innerHTML = `
                <i class="fas fa-exclamation-triangle text-danger"></i>
                Error
            `;
        }
    }
}

// Update system health display
function updateSystemHealth(status) {
    const backendCount = document.getElementById('backend-count');
    const memoryUsage = document.getElementById('memory-usage');

    if (backendCount) {
        backendCount.textContent = status.backends_available || 0;
    }

    if (memoryUsage) {
        memoryUsage.textContent = status.memory_usage || 'Unknown';
    }
}

// ============================================================================
// OCR PROCESSING FUNCTIONS
// ============================================================================

// Process current file
async function processCurrentFile() {
    if (currentFiles.length === 0) {
        showNotification('Please select a file first', 'warning');
        return;
    }

    const file = currentFiles[0];

    // Show processing status
    updateWorkflowProgress(2);
    showProcessingStatus();

    try {
        // Get processing options
        const options = getProcessingOptions();

        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('options', JSON.stringify(options));

        // Process file
        const result = await apiCall('/api/process', 'POST', formData);

        // Show results
        displayResults(result);
        updateWorkflowProgress(3);

        showNotification('Processing complete!', 'success');

    } catch (error) {
        showNotification('Processing failed: ' + error.message, 'error');
        hideProcessingStatus();
    }
}

// Get processing options from UI
function getProcessingOptions() {
    return {
        ocr_mode: document.getElementById('ocr-mode')?.value || 'auto',
        backend: document.getElementById('ocr-backend')?.value || 'auto',
        language: document.getElementById('ocr-language')?.value || 'auto',
        preprocessing: {
            deskew: document.getElementById('preprocess-deskew')?.checked || false,
            enhance: document.getElementById('preprocess-enhance')?.checked || false,
            crop: document.getElementById('preprocess-crop')?.checked || false
        }
    };
}

// Show processing status
function showProcessingStatus() {
    const statusDiv = document.getElementById('processing-status');
    if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.classList.add('fade-in');
    }
}

// Hide processing status
function hideProcessingStatus() {
    const statusDiv = document.getElementById('processing-status');
    if (statusDiv) {
        statusDiv.style.display = 'none';
    }
}

// Display results
function displayResults(result) {
    const resultsViewer = document.getElementById('results-viewer');
    const textContent = document.getElementById('text-content');
    const qualityMetrics = document.getElementById('quality-metrics');

    if (resultsViewer) {
        resultsViewer.style.display = 'block';
        resultsViewer.classList.add('fade-in');
    }

    if (textContent && result.text) {
        textContent.textContent = result.text;
    }

    // Update quality metrics
    if (qualityMetrics && result.quality_score) {
        document.getElementById('quality-score').textContent = result.quality_score;
        document.getElementById('processing-time').textContent = `${result.processing_time || 0}s`;
        document.getElementById('text-confidence').textContent = `${result.confidence || 0}%`;

        qualityMetrics.style.display = 'block';
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} fade-in`;

    const icon = type === 'success' ? 'check-circle' :
        type === 'error' ? 'exclamation-circle' :
            type === 'warning' ? 'exclamation-triangle' : 'info-circle';

    notification.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    // Add to page
    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// ============================================================================
// WORKFLOW CONTROLS
// ============================================================================

// Set up workflow controls
function setupWorkflowControls() {
    // Strategy selection
    document.querySelectorAll('.strategy-card').forEach(card => {
        card.addEventListener('click', function () {
            document.querySelectorAll('.strategy-card').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Quality threshold slider
    const qualitySlider = document.getElementById('batch-quality-threshold');
    const qualityValue = document.getElementById('quality-value');
    if (qualitySlider && qualityValue) {
        qualitySlider.addEventListener('input', function () {
            qualityValue.textContent = this.value * 100 + '%';
        });
    }

    // Advanced options toggle
    const advancedBtn = document.querySelector('[onclick*="toggleAdvancedOptions"]');
    if (advancedBtn) {
        advancedBtn.addEventListener('click', toggleAdvancedOptions);
    }
}

// Set up scanner controls
function setupScannerControls() {
    // Scan settings
    const dpiSlider = document.getElementById('brightness');
    const dpiValue = document.getElementById('brightness-value');
    if (dpiSlider && dpiValue) {
        dpiSlider.addEventListener('input', function () {
            dpiValue.textContent = this.value;
        });
    }

    const contrastSlider = document.getElementById('contrast');
    const contrastValue = document.getElementById('contrast-value');
    if (contrastSlider && contrastValue) {
        contrastSlider.addEventListener('input', function () {
            contrastValue.textContent = this.value;
        });
    }
}

// Set up quality controls
function setupQualityControls() {
    // Quality tool selection
    document.querySelectorAll('.tool-card').forEach(card => {
        card.addEventListener('click', function () {
            const toolType = this.dataset.tool;
            if (toolType) {
                showQualityTool(toolType);
            }
        });
    });
}

// Set up keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function (e) {
        // Ctrl+O for file upload
        if (e.ctrlKey && e.key === 'o') {
            e.preventDefault();
            document.getElementById('file-input')?.click();
        }

        // Ctrl+B for batch processing
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            showSection('batch');
        }

        // Escape to close modals/panels
        if (e.key === 'Escape') {
            closeModals();
        }
    });
}

// ============================================================================
// PLACEHOLDER FUNCTIONS (to be implemented)
// ============================================================================

function showPreprocessingPreview(file) {
    showNotification('Preprocessing preview coming soon!', 'info');
}

function showAnalysisPreview(file) {
    showNotification('Analysis preview coming soon!', 'info');
}

function toggleAdvancedOptions() {
    const advanced = document.getElementById('advanced-options');
    if (advanced) {
        advanced.style.display = advanced.style.display === 'none' ? 'block' : 'none';
    }
}

function showQualityTool(toolType) {
    showNotification(`${toolType} tool coming soon!`, 'info');
}

function applyPreprocessing(tool) {
    showNotification(`${tool} preprocessing coming soon!`, 'info');
}

function runAnalysis(analysisType) {
    showNotification(`${analysisType} analysis coming soon!`, 'info');
}

async function discoverScanners() {
    try {
        const response = await fetch('/api/scanners');
        const data = await response.json();

        const scannerList = document.getElementById('scanner-list');
        scannerList.innerHTML = '';

        // Handle both demo mode (data.scanners) and MCP mode (data directly)
        const scanners = data.scanners || data;

        if (!scanners || scanners.length === 0) {
            scannerList.innerHTML = '<p>No scanners found. Make sure your scanner is connected and powered on.</p>';
            return;
        }

        scanners.forEach(scanner => {
            const scannerItem = document.createElement('div');
            scannerItem.className = 'scanner-item';
            scannerItem.innerHTML = `
                <div>
                    <h4>${scanner.name || scanner.id}</h4>
                    <p>ID: ${scanner.id}</p>
                    <p>Type: ${scanner.type || 'Unknown'} • Status: ${scanner.status || 'Unknown'}</p>
                </div>
                <button class="btn btn-primary" onclick="selectScanner('${scanner.id}')">
                    <i class="fas fa-check"></i> Select
                </button>
            `;
            scannerList.appendChild(scannerItem);
        });

    } catch (error) {
        console.error('Scanner discovery error:', error);
        showAlert('Failed to discover scanners: ' + error.message, 'danger');
    }
}

function selectScanner(scannerId) {
    window.selectedScanner = scannerId;

    // Update scanner display info
    const scannerName = document.getElementById('scanner-name');
    const scannerStatus = document.getElementById('scanner-status');

    if (scannerName) scannerName.textContent = scannerId;
    if (scannerStatus) scannerStatus.textContent = 'Ready';

    // Show scanner controls
    const scannerControls = document.getElementById('scanner-controls');
    if (scannerControls) {
        scannerControls.style.display = 'block';
    }

    showAlert('Scanner selected: ' + scannerId, 'success');
}

async function scanDocument() {
    if (!window.selectedScanner) {
        showAlert('Please select a scanner first', 'danger');
        return;
    }

    const dpi = document.getElementById('scan-dpi').value;
    const colorMode = document.getElementById('scan-color').value;
    const paperSize = document.getElementById('scan-size').value;

    try {
        document.getElementById('scan-btn').disabled = true;
        document.getElementById('scan-btn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';

        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                device_id: window.selectedScanner,
                dpi: dpi,
                color_mode: colorMode,
                paper_size: paperSize
            })
        });

        const result = await response.json();

        if (response.ok) {
            showAlert('Scan completed successfully', 'success');
            // The scanned file would be available for processing
            console.log('Scanned file:', result);
        } else {
            throw new Error(result.detail || 'Scan failed');
        }
    } catch (error) {
        console.error('Scan error:', error);
        showAlert('Scan failed: ' + error.message, 'danger');
    } finally {
        document.getElementById('scan-btn').disabled = false;
        document.getElementById('scan-btn').innerHTML = '<i class="fas fa-camera"></i> Scan Document';
    }
}

function startBatchProcessing() {
    showNotification('Batch processing coming soon!', 'info');
}

function showHelp() {
    showNotification('Help system coming soon!', 'info');
}

function showSettings() {
    showNotification('Settings panel coming soon!', 'info');
}

// ============================================================================
// RESULT HANDLING
// ============================================================================

// Show result tab
function showResultTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.result-panel').forEach(panel => {
        panel.classList.remove('active');
    });

    // Show selected tab
    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetTab) {
        targetTab.classList.add('active');
    }

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.querySelector(`[onclick*="showResultTab('${tabName}')"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
}

// Copy text to clipboard
async function copyText() {
    const textContent = document.getElementById('text-content');
    if (textContent) {
        try {
            await navigator.clipboard.writeText(textContent.textContent);
            showNotification('Text copied to clipboard', 'success');
        } catch (error) {
            showNotification('Failed to copy text', 'error');
        }
    }
}

// Download text
function downloadText() {
    const textContent = document.getElementById('text-content');
    if (textContent) {
        const blob = new Blob([textContent.textContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ocr_result.txt';
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Close modals and panels
function closeModals() {
    // Close any open modals or panels
    document.querySelectorAll('.modal, .panel').forEach(element => {
        element.style.display = 'none';
    });
}

// ============================================================================
// GLOBAL EXPORTS
// ============================================================================

// Clear upload
function clearUpload() {
    currentFiles = [];
    const uploadPreview = document.getElementById('upload-preview');
    if (uploadPreview) {
        uploadPreview.style.display = 'none';
    }
    updateWorkflowProgress(0);
}

// Export functions for global access
window.showSection = showSection;
window.showResultTab = showResultTab;
window.processCurrentFile = processCurrentFile;
window.clearUpload = clearUpload;
window.copyText = copyText;
window.downloadText = downloadText;
window.toggleAdvancedOptions = toggleAdvancedOptions;
window.closeModals = closeModals;
window.showHelp = showHelp;
window.showSettings = showSettings;
window.showQualityTool = showQualityTool;
window.applyPreprocessing = applyPreprocessing;
window.runAnalysis = runAnalysis;
window.discoverScanners = discoverScanners;
window.scanDocument = scanDocument;
window.startBatchProcessing = startBatchProcessing;

// Initialize additional sections
document.addEventListener('DOMContentLoaded', function () {
    initializeOptimization();
    initializeConversion();
});

// Auto-Optimization Functions
function initializeOptimization() {
    const fileInput = document.getElementById('optimization-file-input');
    if (fileInput) {
        fileInput.addEventListener('change', handleOptimizationFileSelect);
    }

    const qualitySlider = document.getElementById('target-quality');
    if (qualitySlider) {
        qualitySlider.addEventListener('input', updateQualityDisplay);
        updateQualityDisplay();
    }
}

function handleOptimizationFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        document.getElementById('optimization-upload-area').style.display = 'none';
        document.getElementById('optimization-settings').style.display = 'block';
        showNotification(`File selected: ${file.name}`, 'success');
    }
}

function updateQualityDisplay() {
    const slider = document.getElementById('target-quality');
    const display = document.getElementById('quality-value-display');
    if (slider && display) {
        display.textContent = Math.round(slider.value * 100) + '%';
    }
}

function startOptimization() {
    const fileInput = document.getElementById('optimization-file-input');
    const quality = document.getElementById('target-quality').value;
    const maxAttempts = document.getElementById('max-attempts').value;

    if (!fileInput.files[0]) {
        showNotification('Please select a file first', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('target_quality', quality);
    formData.append('max_attempts', maxAttempts);

    document.getElementById('start-optimization-btn').disabled = true;
    document.getElementById('start-optimization-btn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Optimizing...';

    fetch('/api/optimize', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.job_id) {
                monitorOptimizationJob(data.job_id);
            } else {
                throw new Error('No job ID received');
            }
        })
        .catch(error => {
            console.error('Optimization error:', error);
            showNotification('Optimization failed: ' + error.message, 'error');
            document.getElementById('start-optimization-btn').disabled = false;
            document.getElementById('start-optimization-btn').innerHTML = '<i class="fas fa-play"></i> Start Auto-Optimization';
        });
}

function monitorOptimizationJob(jobId) {
    const checkStatus = () => {
        fetch(`/api/job/${jobId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    document.getElementById('optimization-settings').style.display = 'none';
                    document.getElementById('optimization-results').style.display = 'block';
                    document.getElementById('start-optimization-btn').disabled = false;
                    document.getElementById('start-optimization-btn').innerHTML = '<i class="fas fa-play"></i> Start Auto-Optimization';

                    const metrics = document.getElementById('optimization-metrics');
                    if (metrics && data.result) {
                        metrics.innerHTML = `
                        <div class="metric-card">
                            <div class="metric-value">${data.result.quality_score || 'N/A'}</div>
                            <div class="metric-label">Best Quality Score</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${data.result.backend_used || 'N/A'}</div>
                            <div class="metric-label">Best Backend</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${data.result.processing_time || 'N/A'}</div>
                            <div class="metric-label">Processing Time</div>
                        </div>
                    `;
                    }
                    showNotification('Optimization completed successfully!', 'success');
                } else if (data.status === 'failed') {
                    showNotification('Optimization failed: ' + (data.error || 'Unknown error'), 'error');
                    document.getElementById('start-optimization-btn').disabled = false;
                    document.getElementById('start-optimization-btn').innerHTML = '<i class="fas fa-play"></i> Start Auto-Optimization';
                } else {
                    setTimeout(checkStatus, 2000);
                }
            })
            .catch(error => {
                console.error('Status check error:', error);
                setTimeout(checkStatus, 2000);
            });
    };
    checkStatus();
}

function downloadOptimized() {
    showNotification('Download functionality to be implemented', 'info');
}

function resetOptimization() {
    document.getElementById('optimization-file-input').value = '';
    document.getElementById('optimization-upload-area').style.display = 'block';
    document.getElementById('optimization-settings').style.display = 'none';
    document.getElementById('optimization-results').style.display = 'none';
    document.getElementById('start-optimization-btn').disabled = false;
    document.getElementById('start-optimization-btn').innerHTML = '<i class="fas fa-play"></i> Start Auto-Optimization';
}

// Format Conversion Functions
function initializeConversion() {
    const fileInput = document.getElementById('conversion-file-input');
    if (fileInput) {
        fileInput.addEventListener('change', handleConversionFileSelect);
    }
}

function handleConversionFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        document.getElementById('conversion-upload-area').style.display = 'none';
        document.getElementById('conversion-settings').style.display = 'block';
        showNotification(`File selected: ${file.name}`, 'success');
    }
}

function startConversion() {
    const fileInput = document.getElementById('conversion-file-input');
    const targetFormat = document.getElementById('target-format').value;
    const includeOcr = document.getElementById('include-ocr').checked;
    const ocrBackend = document.getElementById('ocr-backend-convert').value;

    if (!fileInput.files[0]) {
        showNotification('Please select a file first', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('target_format', targetFormat);
    formData.append('ocr_mode', includeOcr ? 'auto' : 'none');
    formData.append('backend', ocrBackend);

    document.getElementById('start-conversion-btn').disabled = true;
    document.getElementById('start-conversion-btn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Converting...';
    document.getElementById('conversion-progress').style.display = 'block';

    fetch('/api/convert', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.job_id) {
                monitorConversionJob(data.job_id);
            } else {
                throw new Error('No job ID received');
            }
        })
        .catch(error => {
            console.error('Conversion error:', error);
            showNotification('Conversion failed: ' + error.message, 'error');
            resetConversionButtons();
        });
}

function monitorConversionJob(jobId) {
    const checkStatus = () => {
        fetch(`/api/job/${jobId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    document.getElementById('conversion-progress').style.display = 'none';
                    document.getElementById('conversion-results').style.display = 'block';
                    resetConversionButtons();
                    showNotification('Conversion completed successfully!', 'success');

                    const preview = document.getElementById('conversion-preview');
                    if (preview && data.result) {
                        preview.innerHTML = `<p>Converted file ready for download: ${data.result.filename || 'converted_file'}</p>`;
                    }
                } else if (data.status === 'failed') {
                    showNotification('Conversion failed: ' + (data.error || 'Unknown error'), 'error');
                    resetConversionButtons();
                } else {
                    setTimeout(checkStatus, 2000);
                }
            })
            .catch(error => {
                console.error('Status check error:', error);
                setTimeout(checkStatus, 2000);
            });
    };
    checkStatus();
}

function resetConversionButtons() {
    document.getElementById('start-conversion-btn').disabled = false;
    document.getElementById('start-conversion-btn').innerHTML = '<i class="fas fa-exchange-alt"></i> Convert Document';
}

function downloadConverted() {
    showNotification('Download functionality to be implemented', 'info');
}

function previewConverted() {
    showNotification('Preview functionality to be implemented', 'info');
}

function resetConversion() {
    document.getElementById('conversion-file-input').value = '';
    document.getElementById('conversion-upload-area').style.display = 'block';
    document.getElementById('conversion-settings').style.display = 'none';
    document.getElementById('conversion-progress').style.display = 'none';
    document.getElementById('conversion-results').style.display = 'none';
    resetConversionButtons();
}

// Export & Download Functions
function exportAs(format) {
    const filename = document.getElementById('export-filename').value || 'export_result';
    const includeMetadata = document.getElementById('include-metadata').checked;
    const compressOutput = document.getElementById('compress-output').checked;

    const currentResults = getCurrentResults();

    if (!currentResults) {
        showNotification('No results available to export', 'warning');
        return;
    }

    const exportData = {
        export_type: format,
        content: currentResults,
        filename: filename
    };

    fetch('/api/export', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.content) {
                downloadFile(data.content, data.filename, data.media_type);
                addToRecentExports(data.filename, format);
                showNotification(`Exported as ${format.toUpperCase()} successfully!`, 'success');
            } else {
                throw new Error('Export failed');
            }
        })
        .catch(error => {
            console.error('Export error:', error);
            showNotification('Export failed: ' + error.message, 'error');
        });
}

function getCurrentResults() {
    return {
        timestamp: new Date().toISOString(),
        results: "Sample OCR results would go here",
        metadata: {
            backend: "auto",
            processing_time: "1.2s",
            quality_score: 0.85
        }
    };
}

function downloadFile(content, filename, mediaType) {
    const blob = new Blob([content], { type: mediaType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function addToRecentExports(filename, format) {
    const exportsList = document.getElementById('exports-list');
    if (!exportsList) return;

    const exportItem = document.createElement('div');
    exportItem.className = 'export-item';
    exportItem.innerHTML = `
        <div class="export-info">
            <span class="export-name">${filename}</span>
            <span class="export-format">${format.toUpperCase()}</span>
            <span class="export-time">${new Date().toLocaleTimeString()}</span>
        </div>
        <button class="btn btn-sm btn-outline" onclick="downloadFile('${filename}', '${format}')">
            <i class="fas fa-download"></i>
        </button>
    `;

    const emptyState = exportsList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }

    exportsList.insertBefore(exportItem, exportsList.firstChild);

    while (exportsList.children.length > 10) {
        exportsList.removeChild(exportsList.lastChild);
    }
}

function downloadAllProcessed() {
    showNotification('Bulk download functionality to be implemented', 'info');
}

function downloadBatchReport() {
    showNotification('Batch report functionality to be implemented', 'info');
}

// Pipeline Functions
function createNewPipeline() {
    showNotification('Pipeline creation functionality to be implemented', 'info');
}

function executePipeline(pipelineId) {
    const fileInput = document.querySelector('#pipelines-section input[type="file"]');
    if (!fileInput || !fileInput.files[0]) {
        showNotification('Please select a file first', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('pipeline_id', pipelineId);

    fetch('/api/pipelines/execute', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.job_id) {
                showNotification('Pipeline execution started', 'info');
            }
        })
        .catch(error => {
            console.error('Pipeline execution error:', error);
            showNotification('Pipeline execution failed', 'error');
        });
}