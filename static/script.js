// Global variables
let currentPredictionId = null;

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializePredictionForm();
    initializeFlashMessages();
    initializeSearchFunctionality();
});

// Initialize prediction form
function initializePredictionForm() {
    const form = document.getElementById('predictionForm');
    if (form) {
        form.addEventListener('submit', handlePrediction);
    }
}

// Handle prediction form submission
async function handlePrediction(e) {
    e.preventDefault();
    
    const headline = document.getElementById('headline').value.trim();
    const resultContainer = document.getElementById('result');
    const resultIcon = document.getElementById('resultIcon');
    const resultText = document.getElementById('resultText');
    const confidenceText = document.getElementById('confidenceText');
    const feedbackSection = document.querySelector('.feedback-section');
    
    if (!headline) {
        showFlashMessage('Please enter a headline to analyze', 'error');
        return;
    }
    
    // Show loading state
    resultContainer.style.display = 'block';
    resultIcon.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    resultText.textContent = 'Analyzing...';
    confidenceText.textContent = 'Please wait while we process your request';
    feedbackSection.style.display = 'none';
    
    try {
        const formData = new FormData();
        formData.append('headline', headline);
        
        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Display results
            const isReal = data.result === 'REAL';
            const iconClass = isReal ? 'fas fa-check-circle' : 'fas fa-times-circle';
            const resultClass = isReal ? 'real' : 'fake';
            
            resultIcon.innerHTML = `<i class="${iconClass}"></i>`;
            resultIcon.className = `result-icon ${resultClass}`;
            resultText.textContent = data.result;
            confidenceText.textContent = `Confidence: ${data.confidence}`;
            
            // Store prediction ID and show feedback section
            currentPredictionId = data.prediction_id;
            feedbackSection.style.display = 'block';
            
            // Animate result
            resultContainer.classList.add('animate-result');
            
        } else {
            throw new Error(data.error || 'An error occurred during prediction');
        }
        
    } catch (error) {
        console.error('Prediction error:', error);
        resultIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
        resultIcon.className = 'result-icon error';
        resultText.textContent = 'Error';
        confidenceText.textContent = error.message || 'Failed to analyze the headline. Please try again.';
        feedbackSection.style.display = 'none';
        
        showFlashMessage('Failed to analyze headline. Please try again.', 'error');
    }
}

// Submit feedback
async function submitFeedback(feedbackType) {
    if (!currentPredictionId) {
        showFlashMessage('No prediction to provide feedback for', 'error');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('prediction_id', currentPredictionId);
        formData.append('feedback', feedbackType);
        
        const response = await fetch('/feedback', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showFlashMessage('Thank you for your feedback!', 'success');
            
            // Hide feedback section
            const feedbackSection = document.querySelector('.feedback-section');
            if (feedbackSection) {
                feedbackSection.style.display = 'none';
            }
            
            // Reset prediction ID
            currentPredictionId = null;
            
        } else {
            throw new Error(data.error || 'Failed to submit feedback');
        }
        
    } catch (error) {
        console.error('Feedback error:', error);
        showFlashMessage('Failed to submit feedback. Please try again.', 'error');
    }
}

// Initialize flash messages
function initializeFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        // Auto-hide flash messages after 5 seconds
        setTimeout(() => {
            if (message.parentNode) {
                message.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.parentNode.removeChild(message);
                    }
                }, 300);
            }
        }, 5000);
        
        // Allow manual closing by clicking
        message.addEventListener('click', () => {
            message.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (message.parentNode) {
                    message.parentNode.removeChild(message);
                }
            }, 300);
        });
    });
}

// Show flash message programmatically
function showFlashMessage(message, category) {
    const flashContainer = document.querySelector('.flash-messages') || createFlashContainer();
    
    const messageElement = document.createElement('div');
    messageElement.className = `flash-message ${category}`;
    messageElement.textContent = message;
    
    flashContainer.appendChild(messageElement);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (messageElement.parentNode) {
            messageElement.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (messageElement.parentNode) {
                    messageElement.parentNode.removeChild(messageElement);
                }
            }, 300);
        }
    }, 5000);
    
    // Allow manual closing
    messageElement.addEventListener('click', () => {
        messageElement.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 300);
    });
}

// Create flash container if it doesn't exist
function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

// Initialize search functionality
function initializeSearchFunctionality() {
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        // Add real-time search functionality
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // You can implement live search here if needed
                // For now, we'll just use the form submission
            }, 300);
        });
    }
}

// Utility functions
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

// Copy text to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        return new Promise((resolve, reject) => {
            if (document.execCommand('copy')) {
                textArea.remove();
                resolve();
            } else {
                textArea.remove();
                reject();
            }
        });
    }
}

// Format timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Smooth scroll to element
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Add loading animation to buttons
function addLoadingToButton(button, originalText) {
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    
    return function removeLoading() {
        button.disabled = false;
        button.innerHTML = originalText;
    };
}

// Validate form data
function validateForm(formData) {
    const errors = [];
    
    // Add your validation rules here
    for (const [key, value] of formData.entries()) {
        if (!value || value.trim() === '') {
            errors.push(`${key} is required`);
        }
    }
    
    return errors;
}

// Handle form submission with validation
function handleFormSubmission(form, submitHandler) {
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const errors = validateForm(formData);
        
        if (errors.length > 0) {
            errors.forEach(error => showFlashMessage(error, 'error'));
            return;
        }
        
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        const removeLoading = addLoadingToButton(submitButton, originalText);
        
        try {
            await submitHandler(formData);
        } catch (error) {
            showFlashMessage(error.message, 'error');
        } finally {
            removeLoading();
        }
    });
}

// Add animation to elements when they come into view
function addScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    });
    
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}

// Initialize scroll animations when DOM is loaded
document.addEventListener('DOMContentLoaded', addScrollAnimations);

// Add CSS for slide out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100px);
        }
    }
    
    .animate-result {
        animation: pulse 0.6s ease;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .animate-on-scroll {
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.6s ease;
    }
    
    .animate-on-scroll.animate-in {
        opacity: 1;
        transform: translateY(0);
    }
`;
document.head.appendChild(style);

// Hamburger Menu Functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeHamburgerMenu();
});

function initializeHamburgerMenu() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    const navLinks = document.querySelectorAll('.nav-menu a');
    
    if (!hamburger || !navMenu) return;
    
    // Create overlay for mobile
    const overlay = document.createElement('div');
    overlay.classList.add('nav-overlay');
    overlay.id = 'navOverlay';
    document.body.appendChild(overlay);
    
    // Toggle menu function
    function toggleMenu() {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
        overlay.classList.toggle('active');
        
        // Prevent body scroll when menu is open
        if (navMenu.classList.contains('active')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'auto';
        }
    }
    
    // Close menu function
    function closeMenu() {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
    
    // Event listeners
    hamburger.addEventListener('click', toggleMenu);
    overlay.addEventListener('click', closeMenu);
    
    // Close menu when clicking on navigation links
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Add small delay for better UX
            setTimeout(closeMenu, 150);
        });
    });
    
    // Close menu on window resize (if desktop)
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            closeMenu();
        }
    });
    
    // Close menu on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && navMenu.classList.contains('active')) {
            closeMenu();
        }
    });
    
    // Add smooth transitions
    navMenu.addEventListener('transitionend', () => {
        if (!navMenu.classList.contains('active')) {
            navMenu.style.visibility = 'visible';
        }
    });
}

// Enhanced menu animations
function addMenuAnimations() {
    const navLinks = document.querySelectorAll('.nav-menu a');
    
    navLinks.forEach((link, index) => {
        link.addEventListener('mouseenter', () => {
            link.style.transform = 'translateX(5px) scale(1.02)';
        });
        
        link.addEventListener('mouseleave', () => {
            link.style.transform = 'translateX(0) scale(1)';
        });
        
        // Stagger animation for mobile menu
        if (window.innerWidth <= 768) {
            link.style.animationDelay = `${index * 0.1}s`;
        }
    });
}

// Initialize animations
document.addEventListener('DOMContentLoaded', addMenuAnimations);
