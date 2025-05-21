// DuoDesk Main JavaScript

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add meta tag for CSRF if not present
    if (!document.querySelector('meta[name="csrf-token"]')) {
        const meta = document.createElement('meta');
        meta.name = 'csrf-token';
        meta.content = document.querySelector('[name="csrf_token"]')?.value || '';
        document.head.appendChild(meta);
    }
    
    // Auto-close alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            // Create a Bootstrap alert instance and close it
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add active class to current nav item based on URL
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(function(link) {
        const linkHref = link.getAttribute('href');
        if (linkHref && currentLocation.startsWith(linkHref) && linkHref !== '/') {
            link.classList.add('active');
        }
    });
    
    // Handle resource bookmark toggle
    const bookmarkButtons = document.querySelectorAll('.bookmark-toggle');
    bookmarkButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const resourceId = this.getAttribute('data-resource-id');
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            
            // Create FormData object
            const formData = new FormData();
            formData.append('csrf_token', csrfToken);
            
            fetch(`/resources/${resourceId}/bookmark`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.is_bookmarked) {
                        this.classList.remove('btn-outline-warning');
                        this.classList.add('btn-warning');
                        this.querySelector('span').textContent = 'Bookmarked';
                    } else {
                        this.classList.remove('btn-warning');
                        this.classList.add('btn-outline-warning');
                        this.querySelector('span').textContent = 'Bookmark';
                    }
                    showToast('Bookmark updated successfully!', 'success');
                } else {
                    showToast(data.message || 'Failed to update bookmark.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('An error occurred while updating bookmark.', 'danger');
            });
        });
    });
    
    // Handle form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Handle file input custom text
    const fileInputs = document.querySelectorAll('.custom-file-input');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const fileName = this.files[0].name;
            const nextSibling = e.target.nextElementSibling;
            nextSibling.innerText = fileName;
        });
    });
    
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea.auto-resize');
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Trigger once on load
        textarea.dispatchEvent(new Event('input'));
    });
});

// Function to add markdown-like formatting to textareas
function addFormatting(textareaId, formatType) {
    const textarea = document.getElementById(textareaId);
    if (!textarea) return;
    
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    let selectedText = text.substring(start, end);
    let replacement = '';
    
    switch (formatType) {
        case 'bold':
            replacement = `**${selectedText}**`;
            break;
        case 'italic':
            replacement = `*${selectedText}*`;
            break;
        case 'code':
            replacement = `\`${selectedText}\``;
            break;
        case 'link':
            const url = prompt('Enter URL:', 'https://');
            if (url) {
                replacement = `[${selectedText || 'Link text'}](${url})`;
            } else {
                return;
            }
            break;
        case 'list':
            if (selectedText) {
                // Split by new line and add list marker
                const lines = selectedText.split('\n');
                replacement = lines.map(line => `- ${line}`).join('\n');
            } else {
                replacement = '- List item';
            }
            break;
    }
    
    // Replace the selected text with the formatted text
    textarea.value = text.substring(0, start) + replacement + text.substring(end);
    
    // Restore focus and selection
    textarea.focus();
    const newCursorPos = start + replacement.length;
    textarea.setSelectionRange(newCursorPos, newCursorPos);
}

// Toast utility
function showToast(message, category = 'info') {
    const toastId = 'toast-' + Date.now();
    const categoryClass = {
        'success': 'bg-success text-white',
        'danger': 'bg-danger text-white',
        'warning': 'bg-warning text-dark',
        'info': 'bg-info text-dark',
        'primary': 'bg-primary text-white',
        'secondary': 'bg-secondary text-white'
    }[category] || 'bg-info text-dark';
    
    // Create toast container if not exists
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
    }
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center ${categoryClass} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="4000">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>`;
    
    container.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

// AJAX for query response submission
const responseForm = document.querySelector('form[data-ajax-response]');
if (responseForm) {
    responseForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(responseForm);
        const action = responseForm.getAttribute('action');
        fetch(action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast('Response added successfully!', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showToast(data.message || 'Failed to add response.', 'danger');
            }
        })
        .catch(() => showToast('Error submitting response.', 'danger'));
    });
}