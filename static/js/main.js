// Main JavaScript for Job Application Automation

// Global variables
let isLoading = false;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize application
function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize auto-save functionality
    initializeAutoSave();
    
    // Initialize notification system
    initializeNotifications();
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
    
    console.log('Job Application Automation initialized');
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
}

// Initialize auto-save functionality
function initializeAutoSave() {
    const autoSaveInputs = document.querySelectorAll('[data-auto-save]');
    
    autoSaveInputs.forEach(function(input) {
        let timeout;
        
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            
            timeout = setTimeout(function() {
                autoSaveField(input);
            }, 1000); // Save after 1 second of inactivity
        });
    });
}

// Auto-save field value
function autoSaveField(input) {
    const fieldName = input.name;
    const fieldValue = input.value;
    
    // Save to localStorage
    localStorage.setItem(`autosave_${fieldName}`, fieldValue);
    
    // Show save indicator
    showSaveIndicator(input);
}

// Show save indicator
function showSaveIndicator(input) {
    const indicator = document.createElement('small');
    indicator.className = 'text-muted';
    indicator.textContent = 'Saved';
    indicator.style.position = 'absolute';
    indicator.style.right = '10px';
    indicator.style.top = '50%';
    indicator.style.transform = 'translateY(-50%)';
    
    const parent = input.parentElement;
    parent.style.position = 'relative';
    parent.appendChild(indicator);
    
    setTimeout(function() {
        indicator.remove();
    }, 2000);
}

// Initialize notifications
function initializeNotifications() {
    // Check for saved notifications
    const savedNotifications = localStorage.getItem('notifications');
    if (savedNotifications) {
        const notifications = JSON.parse(savedNotifications);
        notifications.forEach(function(notification) {
            showNotification(notification.message, notification.type);
        });
        localStorage.removeItem('notifications');
    }
}

// Show notification
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove notification
    setTimeout(function() {
        if (notification.parentElement) {
            notification.remove();
        }
    }, duration);
}

// Initialize keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Ctrl+S to save (prevent default browser save)
        if (event.ctrlKey && event.key === 's') {
            event.preventDefault();
            const activeForm = document.activeElement.closest('form');
            if (activeForm) {
                activeForm.submit();
            }
        }
        
        // Ctrl+/ to show help
        if (event.ctrlKey && event.key === '/') {
            event.preventDefault();
            showHelpModal();
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(function(modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });
}

// Show help modal
function showHelpModal() {
    const helpModal = document.getElementById('helpModal');
    if (helpModal) {
        const modal = new bootstrap.Modal(helpModal);
        modal.show();
    }
}

// Loading state management
function setLoading(element, isLoading) {
    if (isLoading) {
        element.classList.add('loading');
        element.disabled = true;
        
        // Add spinner to button
        if (element.tagName === 'BUTTON') {
            const spinner = document.createElement('span');
            spinner.className = 'spinner-border spinner-border-sm me-2';
            spinner.setAttribute('data-loading-spinner', 'true');
            element.insertBefore(spinner, element.firstChild);
        }
    } else {
        element.classList.remove('loading');
        element.disabled = false;
        
        // Remove spinner
        const spinner = element.querySelector('[data-loading-spinner]');
        if (spinner) {
            spinner.remove();
        }
    }
}

// AJAX helper functions
function makeAjaxRequest(url, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.open(method, url);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        // Add CSRF token if available
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            xhr.setRequestHeader('X-CSRFToken', csrfToken.getAttribute('content'));
        }
        
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (e) {
                    resolve(xhr.responseText);
                }
            } else {
                reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
            }
        };
        
        xhr.onerror = function() {
            reject(new Error('Network error'));
        };
        
        if (data) {
            xhr.send(JSON.stringify(data));
        } else {
            xhr.send();
        }
    });
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Format currency
function formatCurrency(amount, currency = 'INR') {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Format date
function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    const formatOptions = { ...defaultOptions, ...options };
    return new Date(date).toLocaleDateString('en-IN', formatOptions);
}

// Validate email
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validate phone number (Indian format)
function validatePhoneNumber(phone) {
    const re = /^[6-9]\d{9}$/;
    return re.test(phone.replace(/\D/g, ''));
}

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function() {
            showNotification('Copied to clipboard!', 'success', 2000);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showNotification('Copied to clipboard!', 'success', 2000);
        } catch (err) {
            showNotification('Failed to copy to clipboard', 'error', 3000);
        }
        
        document.body.removeChild(textArea);
    }
}

// Smooth scroll to element
function smoothScrollTo(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// Check if element is in viewport
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Local storage helpers
function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
        console.error('Error saving to localStorage:', e);
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
        console.error('Error loading from localStorage:', e);
        return defaultValue;
    }
}

// Export functions for use in other scripts
window.JobAutomation = {
    showNotification,
    setLoading,
    makeAjaxRequest,
    debounce,
    throttle,
    formatCurrency,
    formatDate,
    validateEmail,
    validatePhoneNumber,
    copyToClipboard,
    smoothScrollTo,
    isInViewport,
    saveToLocalStorage,
    loadFromLocalStorage
};

// Analytics tracking (placeholder)
function trackEvent(eventName, eventData = {}) {
    // This would integrate with your analytics service
    console.log('Event tracked:', eventName, eventData);
}

// Error handling
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    // You could send this to an error tracking service
});

// Unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    // You could send this to an error tracking service
});

// Service Worker registration (if needed)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js').then(function(registration) {
            console.log('ServiceWorker registration successful');
        }).catch(function(error) {
            console.log('ServiceWorker registration failed');
        });
    });
}