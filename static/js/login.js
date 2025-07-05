/**
 * Login Page JavaScript
 * Handles form switching, validation, and theme integration
 */

class LoginManager {
    constructor() {
        this.currentForm = 'login';
        this.isLoading = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupFormValidation();
        this.initializeTheme();
    }

    bindEvents() {
        // Tab button events
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const formType = e.target.textContent.toLowerCase().trim();
                this.showForm(formType);
            });
        });

        // Form submission events
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        });

        // Input events for real-time validation
        document.querySelectorAll('.form-input').forEach(input => {
            input.addEventListener('input', (e) => this.validateInput(e.target));
            input.addEventListener('blur', (e) => this.validateInput(e.target));
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboardNavigation(e));
    }

    showForm(formType) {
        this.currentForm = formType;
        
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            const isActive = btn.textContent.toLowerCase().trim() === formType;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-selected', isActive);
        });

        // Update forms
        document.querySelectorAll('.form').forEach(form => {
            const isActive = form.id === `${formType}-form`;
            form.classList.toggle('active', isActive);
            
            if (isActive) {
                // Focus first input in active form
                const firstInput = form.querySelector('.form-input');
                if (firstInput) {
                    setTimeout(() => firstInput.focus(), 100);
                }
            }
        });

        // Update page title
        document.title = `${formType.charAt(0).toUpperCase() + formType.slice(1)} - Enigma AI Bot`;
        
        // Announce change for screen readers
        this.announceFormChange(formType);
    }

    handleFormSubmit(event) {
        const form = event.target;
        const formData = new FormData(form);
        const action = formData.get('action');

        // Prevent submission if already loading
        if (this.isLoading) {
            event.preventDefault();
            return;
        }

        // Validate form before submission
        if (!this.validateForm(form)) {
            event.preventDefault();
            return;
        }

        // Set loading state
        this.setLoadingState(true);
        
        // Form will submit normally, but we show loading state
        // The server will handle the redirect or show errors
    }

    validateForm(form) {
        const inputs = form.querySelectorAll('.form-input[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!this.validateInput(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    validateInput(input) {
        const value = input.value.trim();
        const type = input.type;
        const name = input.name;
        let isValid = true;
        let errorMessage = '';

        // Remove existing error styling
        this.clearInputError(input);

        // Required field validation
        if (input.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = `${this.getFieldLabel(name)} is required`;
        }
        // Username validation
        else if (name === 'username' && value.length < 3) {
            isValid = false;
            errorMessage = 'Username must be at least 3 characters long';
        }
        // Password validation
        else if (name === 'password' && value.length < 6) {
            isValid = false;
            errorMessage = 'Password must be at least 6 characters long';
        }
        // Email validation (if provided)
        else if (type === 'email' && value && !this.isValidEmail(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }

        // Show error if validation failed
        if (!isValid) {
            this.showInputError(input, errorMessage);
        }

        return isValid;
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    getFieldLabel(fieldName) {
        const labels = {
            'username': 'Username',
            'password': 'Password',
            'email': 'Email'
        };
        return labels[fieldName] || fieldName;
    }

    showInputError(input, message) {
        input.classList.add('error');
        input.setAttribute('aria-invalid', 'true');
        
        // Create or update error message
        let errorElement = input.parentNode.querySelector('.error-message');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'error-message';
            errorElement.setAttribute('role', 'alert');
            input.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
        errorElement.style.cssText = `
            color: var(--error-color);
            font-size: 0.75rem;
            margin-top: 0.25rem;
            animation: slideDown 0.2s ease;
        `;
    }

    clearInputError(input) {
        input.classList.remove('error');
        input.removeAttribute('aria-invalid');
        
        const errorElement = input.parentNode.querySelector('.error-message');
        if (errorElement) {
            errorElement.remove();
        }
    }

    setLoadingState(loading) {
        this.isLoading = loading;
        
        const activeForm = document.querySelector('.form.active');
        const submitBtn = activeForm.querySelector('.submit-btn');
        
        if (loading) {
            activeForm.classList.add('form-loading');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        } else {
            activeForm.classList.remove('form-loading');
            submitBtn.disabled = false;
            
            // Restore original button text
            const action = this.currentForm === 'login' ? 'Sign In' : 'Create Account';
            const icon = this.currentForm === 'login' ? 'fa-sign-in-alt' : 'fa-user-plus';
            submitBtn.innerHTML = `<i class="fas ${icon}"></i> ${action}`;
        }
    }

    handleKeyboardNavigation(event) {
        // Tab navigation between forms
        if (event.key === 'Tab' && event.altKey) {
            event.preventDefault();
            const newForm = this.currentForm === 'login' ? 'register' : 'login';
            this.showForm(newForm);
        }
        
        // Enter key on tab buttons
        if (event.key === 'Enter' && event.target.classList.contains('tab-button')) {
            event.preventDefault();
            event.target.click();
        }
    }

    announceFormChange(formType) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Switched to ${formType} form`;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            announcement.remove();
        }, 1000);
    }

    initializeTheme() {
        // Ensure theme switcher works on login page
        if (window.themeSwitcher) {
            // Theme is already initialized by theme-switcher.js
            return;
        }
        
        // Fallback if theme switcher isn't loaded yet
        document.addEventListener('DOMContentLoaded', () => {
            if (window.themeSwitcher) {
                console.log('Theme switcher initialized for login page');
            }
        });
    }

    setupFormValidation() {
        // Add CSS for validation states
        const style = document.createElement('style');
        style.textContent = `
            .form-input.error {
                border-color: var(--error-color);
                box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
            }
            
            .form-input.error:focus {
                border-color: var(--error-color);
                box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
            }
            
            .error-message {
                display: block;
                margin-top: 0.25rem;
                font-size: 0.75rem;
                color: var(--error-color);
                animation: slideDown 0.2s ease;
            }
            
            @keyframes slideDown {
                from {
                    opacity: 0;
                    transform: translateY(-5px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Public methods for external access
    switchToLogin() {
        this.showForm('login');
    }

    switchToRegister() {
        this.showForm('register');
    }

    getCurrentForm() {
        return this.currentForm;
    }
}

// Auto-hide alerts after 5 seconds
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
}

// Initialize login manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.loginManager = new LoginManager();
    
    // Auto-hide alerts
    autoHideAlerts();
    
    // Global function for HTML onclick handlers
    window.showForm = (formType) => window.loginManager.showForm(formType);
    
    // Focus management
    const firstInput = document.querySelector('.form.active .form-input');
    if (firstInput) {
        firstInput.focus();
    }
    
    // Handle browser back/forward
    window.addEventListener('popstate', () => {
        // Reset to login form if navigating back
        window.loginManager.showForm('login');
    });
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoginManager;
}