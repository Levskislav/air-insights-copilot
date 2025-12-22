/**
 * Air & Insights Copilot - Frontend JavaScript
 * =============================================
 * Handles API calls and UI interactions for the web demo.
 * 
 * Features:
 * - Form submission for /analyze endpoint
 * - Quick location buttons
 * - NASA APOD loading
 * - Error handling with toast notifications
 * - Smooth animations and loading states
 */

// Configuration - API base URL
// Change this if running on a different host/port
const API_BASE_URL = 'http://127.0.0.1:8000';

// DOM Elements
const analyzeForm = document.getElementById('analyze-form');
const submitBtn = document.getElementById('submit-btn');
const resultsSection = document.getElementById('results-section');
const pm25Value = document.getElementById('pm25-value');
const pm10Value = document.getElementById('pm10-value');
const tempValue = document.getElementById('temp-value');
const guidanceText = document.getElementById('guidance-text');
const quickBtns = document.querySelectorAll('.quick-btn');
const apodBtn = document.getElementById('apod-btn');
const apodContent = document.getElementById('apod-content');
const errorToast = document.getElementById('error-toast');
const toastMessage = document.getElementById('toast-message');

/**
 * Show error toast notification
 * @param {string} message - Error message to display
 */
function showError(message) {
    toastMessage.textContent = message;
    errorToast.classList.add('visible');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorToast.classList.remove('visible');
    }, 5000);
}

/**
 * Format number for display
 * @param {number|null} value - Value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted value or '--' if null
 */
function formatValue(value, decimals = 1) {
    if (value === null || value === undefined) {
        return '--';
    }
    return Number(value).toFixed(decimals);
}

/**
 * Handle analyze form submission
 * Calls POST /analyze and displays results
 */
async function handleAnalyze(event) {
    event.preventDefault();
    
    // Get form values
    const latitude = parseFloat(document.getElementById('latitude').value);
    const longitude = parseFloat(document.getElementById('longitude').value);
    const hours = parseInt(document.getElementById('hours').value);
    
    // Validate inputs
    if (isNaN(latitude) || latitude < -90 || latitude > 90) {
        showError('Invalid latitude. Must be between -90 and 90.');
        return;
    }
    if (isNaN(longitude) || longitude < -180 || longitude > 180) {
        showError('Invalid longitude. Must be between -180 and 180.');
        return;
    }
    if (isNaN(hours) || hours < 1 || hours > 168) {
        showError('Invalid hours. Must be between 1 and 168.');
        return;
    }
    
    // Set loading state
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    
    try {
        // Make API request
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                latitude: latitude,
                longitude: longitude,
                hours: hours
            })
        });
        
        // Handle errors
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Parse response
        const data = await response.json();
        
        // Update UI with results
        displayResults(data);
        
    } catch (error) {
        console.error('Analyze error:', error);
        showError(`Failed to analyze: ${error.message}`);
    } finally {
        // Remove loading state
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    }
}

/**
 * Display analysis results in the UI
 * @param {Object} data - API response data
 */
function displayResults(data) {
    // Update metric values with animation
    animateValue(pm25Value, formatValue(data.pm25_avg, 1));
    animateValue(pm10Value, formatValue(data.pm10_avg, 1));
    animateValue(tempValue, formatValue(data.temp_avg, 1));
    
    // Update guidance text
    guidanceText.textContent = data.guidance_text || 'No guidance available.';
    
    // Show results section with animation
    resultsSection.classList.add('visible');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Animate value change in metric card
 * @param {HTMLElement} element - Target element
 * @param {string} newValue - New value to display
 */
function animateValue(element, newValue) {
    element.style.opacity = '0';
    element.style.transform = 'translateY(10px)';
    
    setTimeout(() => {
        element.textContent = newValue;
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
    }, 150);
}

/**
 * Handle quick location button click
 * Sets latitude and longitude from button data attributes
 */
function handleQuickLocation(event) {
    const btn = event.target;
    const lat = parseFloat(btn.dataset.lat);
    const lon = parseFloat(btn.dataset.lon);
    
    document.getElementById('latitude').value = lat;
    document.getElementById('longitude').value = lon;
    
    // Visual feedback
    btn.style.transform = 'scale(0.95)';
    setTimeout(() => {
        btn.style.transform = '';
    }, 100);
}

/**
 * Load NASA Astronomy Picture of the Day
 * Calls GET /apod/today and displays the image
 */
async function loadApod() {
    // Set loading state
    apodBtn.textContent = 'Loading...';
    apodBtn.classList.add('loading');
    apodBtn.disabled = true;
    
    try {
        // Make API request
        const response = await fetch(`${API_BASE_URL}/apod/today`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Build APOD content HTML
        const html = `
            <img src="${data.url}" alt="${data.title}" class="apod-image" loading="lazy">
            <h4 class="apod-title">${data.title}</h4>
            <p class="apod-explanation">${data.explanation}</p>
        `;
        
        // Update UI
        apodContent.innerHTML = html;
        apodContent.classList.add('visible');
        
        // Hide button after loading
        apodBtn.style.display = 'none';
        
    } catch (error) {
        console.error('APOD error:', error);
        showError(`Failed to load APOD: ${error.message}`);
        
        // Reset button
        apodBtn.textContent = 'Load APOD';
        apodBtn.classList.remove('loading');
        apodBtn.disabled = false;
    }
}

/**
 * Initialize event listeners
 */
function init() {
    // Form submission
    analyzeForm.addEventListener('submit', handleAnalyze);
    
    // Quick location buttons
    quickBtns.forEach(btn => {
        btn.addEventListener('click', handleQuickLocation);
    });
    
    // NASA APOD button
    apodBtn.addEventListener('click', loadApod);
    
    // Close toast on click
    errorToast.addEventListener('click', () => {
        errorToast.classList.remove('visible');
    });
    
    // Add transition styles for metric values
    [pm25Value, pm10Value, tempValue].forEach(el => {
        el.style.transition = 'opacity 0.15s ease, transform 0.15s ease';
    });
    
    console.log('🌬️ Air & Insights Copilot initialized');
    console.log(`📡 API: ${API_BASE_URL}`);
}

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', init);

