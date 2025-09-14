// Document Toolkit - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupEventListeners();
    setupFormValidation();
    addLoadingStyles();
}

function setupEventListeners() {
    // Form submissions
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
    
    // Button clicks
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', handleButtonClick);
    });
    
    // File inputs
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', handleFileInput);
    });
}

function handleFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    
    if (!validateForm(form)) {
        return;
    }
    
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
    submitBtn.disabled = true;
    
    const formData = new FormData(form);
    
    fetch(form.action, {
        method: form.method,
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message || 'Success!');
            if (data.redirect) {
                setTimeout(() => window.location.href = data.redirect, 1000);
            }
        } else {
            showAlert('danger', data.message || 'Error occurred');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Network error');
    })
    .finally(() => {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    });
}

function handleButtonClick(e) {
    const btn = e.target.closest('.btn');
    if (!btn) return;
    
    const action = btn.dataset.action;
    
    switch (action) {
        case 'generate':
            handleGenerate(btn);
            break;
        case 'download':
            handleDownload(btn);
            break;
        case 'delete':
            handleDelete(btn);
            break;
    }
}

function handleGenerate(btn) {
    const form = btn.closest('form');
    if (!form) return;
    
    btn.innerHTML = '<span class="spinner"></span> Generating...';
    btn.disabled = true;
    
    const formData = new FormData(form);
    
    fetch('/generate', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Document generated!');
            if (data.download_url) {
                showDownloadButton(data.download_url, data.filename);
            }
        } else {
            showAlert('danger', data.message || 'Generation failed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Network error');
    })
    .finally(() => {
        btn.innerHTML = 'Generate Document';
        btn.disabled = false;
    });
}

function handleDownload(btn) {
    const url = btn.dataset.url;
    const filename = btn.dataset.filename || 'document';
    
    if (!url) return;
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showAlert('success', 'Download started!');
}

function handleDelete(btn) {
    if (!confirm('Are you sure?')) return;
    
    const documentId = btn.dataset.documentId;
    
    fetch('/delete-document', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ document_id: documentId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Deleted!');
            btn.closest('.card').remove();
        } else {
            showAlert('danger', data.message || 'Delete failed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Network error');
    });
}

function handleFileInput(e) {
    const input = e.target;
    const file = input.files[0];
    
    if (!file) return;
    
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        showAlert('danger', 'File too large (max 5MB)');
        input.value = '';
        return;
    }
    
    previewFile(file, input);
}

function previewFile(file, input) {
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const preview = input.parentNode.querySelector('.file-preview');
        if (preview) {
            if (file.type.startsWith('image/')) {
                preview.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width: 200px;">`;
            } else {
                preview.innerHTML = `<p>File: ${file.name}</p>`;
            }
            preview.style.display = 'block';
        }
    };
    
    reader.readAsDataURL(file);
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    let errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        field.parentNode.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} fade-in`;
    alertDiv.innerHTML = `
        <div class="d-flex justify-between align-center">
            <span>${message}</span>
            <button class="btn btn-sm" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    const container = document.querySelector('.alerts-container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function showDownloadButton(url, filename) {
    const downloadBtn = document.createElement('a');
    downloadBtn.href = url;
    downloadBtn.download = filename;
    downloadBtn.className = 'btn btn-success mt-3';
    downloadBtn.innerHTML = 'Download Document';
    
    const container = document.querySelector('.download-container') || document.body;
    container.appendChild(downloadBtn);
}

function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                validateField(input);
            });
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    if (field.type === 'email' && value && !isValidEmail(value)) {
        showFieldError(field, 'Invalid email address');
        return false;
    }
    
    clearFieldError(field);
    return true;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function addLoadingStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .file-preview {
            margin-top: 1rem;
            padding: 1rem;
            border: 1px solid #e5e7eb;
            border-radius: 0.5rem;
            background: #f8fafc;
        }
    `;
    document.head.appendChild(style);
}

// Export for global access
window.DocumentToolkit = {
    showAlert,
    validateForm
};