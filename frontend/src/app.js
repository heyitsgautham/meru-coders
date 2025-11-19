/**
 * Main Application
 * Initializes the application and loads schemes
 */

class App {
    constructor() {
        this.init();
    }
    
    async init() {
        console.log('🚀 Sanskrit Meter Identification System - Frontend v2.0');
        
        // Load transliteration schemes
        await this.loadSchemes();
        
        // Check API connection
        await this.checkAPIConnection();
        
        // Setup textarea auto-resize
        this.setupTextareaAutoResize();
        
        console.log('✅ Application initialized successfully');
    }
    
    /**
     * Setup textarea auto-resize functionality
     */
    setupTextareaAutoResize() {
        const textarea = document.getElementById('input-text');
        if (!textarea) return;
        
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Trigger initial resize if there's content
        if (textarea.value) {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        }
    }
    
    /**
     * Load transliteration schemes from API
     */
    async loadSchemes() {
        try {
            const response = await APIService.getSchemes();
            
            if (response.success && response.schemes) {
                this.populateSchemeSelects(response.schemes);
            } else {
                console.warn('Failed to load schemes, using defaults');
                this.populateSchemeSelects(this.getDefaultSchemes());
            }
        } catch (error) {
            console.error('Error loading schemes:', error);
            this.populateSchemeSelects(this.getDefaultSchemes());
        }
    }
    
    /**
     * Populate all scheme select dropdowns
     */
    populateSchemeSelects(schemes) {
        const selects = [
            document.getElementById('text-scheme'),
            document.getElementById('image-scheme'),
            document.getElementById('file-scheme')
        ];
        
        selects.forEach(select => {
            select.innerHTML = '';
            schemes.forEach(scheme => {
                const option = document.createElement('option');
                option.value = scheme.value;
                option.textContent = scheme.label;
                select.appendChild(option);
            });
        });
    }
    
    /**
     * Get default schemes if API fails
     */
    getDefaultSchemes() {
        return [
            { value: 'devanagari', label: 'Devanagari (देवनागरी)' },
            { value: 'iast', label: 'IAST (International)' },
            { value: 'itrans', label: 'ITRANS' },
            { value: 'velthuis', label: 'Velthuis' },
            { value: 'slp1', label: 'SLP1' },
            { value: 'wx', label: 'WX Notation' }
        ];
    }
    
    /**
     * Check API connection
     */
    async checkAPIConnection() {
        try {
            const response = await APIService.getAPIInfo();
            console.log('API Info:', response);
            
            if (response.ocr_available) {
                console.log('OCR Engines Available:');
                console.log('  - Tesseract:', response.ocr_available.tesseract);
                console.log('  - Google:', response.ocr_available.google);
                
                // Disable Google OCR option if not available
                if (!response.ocr_available.google) {
                    const googleOption = document.querySelector('#ocr-engine option[value="google"]');
                    if (googleOption) {
                        googleOption.disabled = true;
                        googleOption.textContent += ' (Not Available)';
                    }
                }
            }
        } catch (error) {
            console.warn('Could not connect to API:', error.message);
            this.showAPIWarning();
        }
    }
    
    /**
     * Show API connection warning
     */
    showAPIWarning() {
        const warning = document.createElement('div');
        warning.className = 'alert alert-warning';
        warning.style.position = 'fixed';
        warning.style.top = '80px';
        warning.style.left = '50%';
        warning.style.transform = 'translateX(-50%)';
        warning.style.zIndex = '1000';
        warning.style.maxWidth = '600px';
        warning.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            <div>
                <strong>Backend API not connected</strong><br>
                Make sure the backend is running at <code>http://localhost:5000</code>
            </div>
        `;
        
        document.body.appendChild(warning);
        
        setTimeout(() => {
            warning.remove();
        }, 10000);
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new App();
    });
} else {
    window.app = new App();
}
