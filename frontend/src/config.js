/**
 * Configuration
 * Environment-specific settings
 */

// Get API URL from environment or use default
const getAPIBaseURL = () => {
    // Check if window.CONFIG is set (from config.js in production)
    if (typeof window.CONFIG !== 'undefined' && window.CONFIG.API_URL) {
        return window.CONFIG.API_URL;
    }
    
    // Check if we're in production (deployed on Cloud Run)
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        // In production but no config found - should not happen, but fallback gracefully
        console.error('Production config not found! Defaulting to localhost.');
        return 'http://localhost:5000/api';
    }
    
    // Local development
    return 'http://localhost:5000/api';
};

const Config = {
    API_BASE_URL: getAPIBaseURL(),
    VERSION: '2.0.0',
    APP_NAME: 'Sanskrit Meter Identification System',
};

// Log configuration
console.log('App Configuration:', Config);
console.log('Current hostname:', window.location.hostname);
console.log('Window.CONFIG:', window.CONFIG);
