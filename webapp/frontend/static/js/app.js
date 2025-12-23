/**
 * OCR-MCP Web Interface JavaScript
 * Handles frontend interactions with the FastAPI backend
 */

// Global state
let currentJobId = null;
let selectedFiles = [];
let currentResult = null;
let statusCheckInterval = null;

// DOM elements
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const batchFileInput = document.getElementById('batch-file-input');
const batchFileList = document.getElementById('batch-file-list');
const processingStatus = document.getElementById('processing-status');
const resultsSection = document.getElementById('results-section');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    checkHealth();
});

// Initialize event listeners
function initializeEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('onclick').match(/'([^']+)'/)[1];
            showTab(tabName);
        });
    });

    // File upload drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });

    uploadArea.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', handleFileSelect, false);

    // Batch file handling
    batchFileInput.addEventListener('change', handleBatchFileSelect, false);

    // Results tabs
    document.querySelectorAll('.results-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            const tabType = this.getAttribute('onclick').match(/'([^']+)'/)[1];
            showResultTab(tabType);
        });
    });
}

// Tab switching functions
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
}

function showResultTab(tabType) {
    // Hide all result panels
    document.querySelectorAll('.result-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.querySelectorAll('.results-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected result panel
    document.getElementById(tabType + '-results').classList.add('active');
    event.target.classList.add('active');
}

// File upload handling
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    uploadArea.classList.add('dragover');
}

function unhighlight(e) {
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        displaySelectedFile(file);
    }
}

function displaySelectedFile(file) {
    const uploadContent = uploadArea.querySelector('.upload-content');
    uploadContent.innerHTML = `
        <i class="fas fa-file-alt upload-icon" style="color: var(--success-color);"></i>
        <p><strong>${file.name}</strong></p>
        <p class="upload-subtitle">${formatFileSize(file.size)} • ${file.type || 'Unknown type'}</p>
        <button class="btn btn-secondary" onclick="clearFile()">
            <i class="fas fa-times"></i> Clear
        </button>
    `;

    // Store the file for processing
    window.selectedFile = file;
}

// Batch file handling
function handleBatchFileSelect(e) {
    const files = Array.from(e.target.files);
    selectedFiles = files;
    displayBatchFiles();
}

function displayBatchFiles() {
    batchFileList.innerHTML = '';

    if (selectedFiles.length === 0) {
        batchFileList.innerHTML = '<p class="text-center mt-20">No files selected</p>';
        return;
    }

    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div>
                <span class="file-name">${file.name}</span>
                <span class="file-size">${formatFileSize(file.size)}</span>
            </div>
            <button class="remove-btn" onclick="removeBatchFile(${index})">
                <i class="fas fa-times"></i>
            </button>
        `;
        batchFileList.appendChild(fileItem);
    });
}

function removeBatchFile(index) {
    selectedFiles.splice(index, 1);
    displayBatchFiles();
}

function clearFile() {
    window.selectedFile = null;
    const uploadContent = uploadArea.querySelector('.upload-content');
    uploadContent.innerHTML = `
        <i class="fas fa-cloud-upload-alt upload-icon"></i>
        <p>Drag & drop files here or click to browse</p>
        <p class="upload-subtitle">Supports PDF, PNG, JPG, CBZ, and other image formats</p>
        <button class="btn btn-primary" onclick="document.getElementById('file-input').click()">
            <i class="fas fa-folder-open"></i> Choose Files
        </button>
    `;
}

// File processing
async function processFile() {
    if (!window.selectedFile) {
        showAlert('Please select a file first', 'danger');
        return;
    }

    const ocrMode = document.getElementById('ocr-mode').value;
    const backend = document.getElementById('backend').value;

    const formData = new FormData();
    formData.append('file', window.selectedFile);
    formData.append('ocr_mode', ocrMode);
    formData.append('backend', backend);

    try {
        showProcessingStatus(window.selectedFile.name);
        document.getElementById('process-btn').disabled = true;
        document.getElementById('process-btn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            currentJobId = result.job_id;
            monitorJobStatus();
        } else {
            throw new Error(result.detail || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showAlert('Upload failed: ' + error.message, 'danger');
        hideProcessingStatus();
        document.getElementById('process-btn').disabled = false;
        document.getElementById('process-btn').innerHTML = '<i class="fas fa-play"></i> Process Document';
    }
}

async function processBatch() {
    if (selectedFiles.length === 0) {
        showAlert('Please select files first', 'danger');
        return;
    }

    const ocrMode = document.getElementById('batch-ocr-mode').value;
    const backend = document.getElementById('batch-backend').value;

    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });
    formData.append('ocr_mode', ocrMode);
    formData.append('backend', backend);

    try {
        showProcessingStatus(`${selectedFiles.length} files`);
        document.getElementById('batch-process-btn').disabled = true;
        document.getElementById('batch-process-btn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

        const response = await fetch('/api/process_batch', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            currentJobId = result.job_id;
            monitorJobStatus();
        } else {
            throw new Error(result.detail || 'Batch processing failed');
        }
    } catch (error) {
        console.error('Batch processing error:', error);
        showAlert('Batch processing failed: ' + error.message, 'danger');
        hideProcessingStatus();
        document.getElementById('batch-process-btn').disabled = false;
        document.getElementById('batch-process-btn').innerHTML = '<i class="fas fa-play-circle"></i> Process Batch';
    }
}

// Job monitoring
function monitorJobStatus() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }

    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/job/${currentJobId}`);
            const job = await response.json();

            updateProcessingStatus(job);

            if (job.status === 'completed') {
                clearInterval(statusCheckInterval);
                showResults(job.result);
                hideProcessingStatus();
                resetButtons();
            } else if (job.status === 'failed') {
                clearInterval(statusCheckInterval);
                showAlert('Processing failed: ' + (job.error || 'Unknown error'), 'danger');
                hideProcessingStatus();
                resetButtons();
            }
        } catch (error) {
            console.error('Status check error:', error);
        }
    }, 2000);
}

function updateProcessingStatus(job) {
    const statusBadge = document.getElementById('status-badge');
    const progressFill = document.getElementById('progress-fill');
    const statusDetails = document.getElementById('status-details');

    statusBadge.textContent = job.status.charAt(0).toUpperCase() + job.status.slice(1);
    statusBadge.className = 'status-badge ' + job.status;

    // Simulate progress (in a real app, this would come from the backend)
    let progress = 0;
    if (job.status === 'processing') {
        progress = 60;
    } else if (job.status === 'completed') {
        progress = 100;
    }
    progressFill.style.width = progress + '%';

    statusDetails.innerHTML = `
        <p><strong>Status:</strong> ${job.status}</p>
        <p><strong>File:</strong> ${job.filename || 'Processing...'}</p>
        ${job.result ? '<p><strong>Backend:</strong> ' + (job.result.backend || 'Unknown') + '</p>' : ''}
    `;
}

function showProcessingStatus(filename) {
    document.getElementById('status-filename').textContent = filename;
    processingStatus.style.display = 'block';
    resultsSection.style.display = 'none';
}

function hideProcessingStatus() {
    processingStatus.style.display = 'none';
}

function showResults(result) {
    currentResult = result;
    resultsSection.style.display = 'block';

    // Populate text results
    document.getElementById('text-content').textContent = result.text || 'No text extracted';

    // Populate JSON results
    document.getElementById('json-content').textContent = JSON.stringify(result, null, 2);

    // Populate HTML results
    document.getElementById('html-content').innerHTML = result.html || '<p>No HTML content available</p>';
}

function resetButtons() {
    document.getElementById('process-btn').disabled = false;
    document.getElementById('process-btn').innerHTML = '<i class="fas fa-play"></i> Process Document';

    document.getElementById('batch-process-btn').disabled = false;
    document.getElementById('batch-process-btn').innerHTML = '<i class="fas fa-play-circle"></i> Process Batch';
}

// Scanner functions
async function discoverScanners() {
    try {
        const response = await fetch('/api/scanners');
        const data = await response.json();

        const scannerList = document.getElementById('scanner-list');
        scannerList.innerHTML = '';

        if (data.length === 0) {
            scannerList.innerHTML = '<p>No scanners found. Make sure your scanner is connected and powered on.</p>';
            return;
        }

        data.forEach(scanner => {
            const scannerItem = document.createElement('div');
            scannerItem.className = 'scanner-item';
            scannerItem.innerHTML = `
                <div>
                    <h4>${scanner.name || scanner.id}</h4>
                    <p>ID: ${scanner.id}</p>
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
    document.getElementById('scanner-controls').style.display = 'block';
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

// Health and diagnostics
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();

        const statusDiv = document.getElementById('system-status');
        statusDiv.innerHTML = `
            <p><strong>Server:</strong> ${data.status === 'healthy' ? '✅ Running' : '❌ Issues'}</p>
            <p><strong>MCP Connection:</strong> ${data.mcp_connected ? '✅ Connected' : '❌ Disconnected'}</p>
            <p><strong>Version:</strong> ${data.version}</p>
        `;
    } catch (error) {
        console.error('Health check error:', error);
        document.getElementById('system-status').innerHTML = '<p>❌ Unable to connect to server</p>';
    }
}

async function checkBackends() {
    try {
        const response = await fetch('/api/backends');
        const data = await response.json();

        const backendDiv = document.getElementById('backend-status');
        backendDiv.innerHTML = '<h4>Available OCR Backends:</h4>';

        data.forEach(backend => {
            const status = backend.available ? '✅ Available' : '❌ Unavailable';
            backendDiv.innerHTML += `<p><strong>${backend.name}:</strong> ${status}</p>`;
        });
    } catch (error) {
        console.error('Backend check error:', error);
        document.getElementById('backend-status').innerHTML = '<p>❌ Unable to check backends</p>';
    }
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function downloadResult(format) {
    if (!currentResult) return;

    let content, filename, mimeType;

    switch (format) {
        case 'text':
            content = currentResult.text || '';
            filename = 'ocr_result.txt';
            mimeType = 'text/plain';
            break;
        case 'json':
            content = JSON.stringify(currentResult, null, 2);
            filename = 'ocr_result.json';
            mimeType = 'application/json';
            break;
        default:
            return;
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function copyToClipboard() {
    if (!currentResult || !currentResult.text) return;

    navigator.clipboard.writeText(currentResult.text).then(() => {
        showAlert('Text copied to clipboard!', 'success');
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = currentResult.text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showAlert('Text copied to clipboard!', 'success');
    });
}

function showAlert(message, type) {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;

    // Set colors based on type
    const colors = {
        success: '#059669',
        danger: '#dc2626',
        warning: '#d97706',
        info: '#2563eb'
    };
    alert.style.backgroundColor = colors[type] || colors.info;

    alert.textContent = message;
    document.body.appendChild(alert);

    // Remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}

// Initialize on page load
checkHealth();
checkBackends();
