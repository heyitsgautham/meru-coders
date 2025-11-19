/**
 * Forms Component
 * Handles form submissions and file uploads
 */

class Forms {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupTextForm();
        this.setupImageForm();
        this.setupFileForm();
        this.setupFileInputs();
    }
    
    /**
     * Setup text input form
     */
    setupTextForm() {
        const form = document.getElementById('form-text');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const text = document.getElementById('input-text').value;
            const mode = document.getElementById('text-mode').value;
            const scheme = document.getElementById('text-scheme').value;
            
            const btn = form.querySelector('.btn-primary');
            this.setLoading(btn, true);
            
            try {
                const result = await APIService.identifyFromText(text, mode, scheme);
                window.resultsComponent.displayResults('text', result);
            } catch (error) {
                this.showError('text-results', error.message);
            } finally {
                this.setLoading(btn, false);
            }
        });
    }
    
    /**
     * Setup image upload form
     */
    setupImageForm() {
        const form = document.getElementById('form-image');
        const imageInput = document.getElementById('input-image');
        const preview = document.getElementById('image-preview');
        
        // Image preview
        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    preview.querySelector('img').src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
        
        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const file = imageInput.files[0];
            if (!file) {
                this.showError('image-results', 'Please select an image');
                return;
            }
            
            const ocrEngine = document.getElementById('ocr-engine').value;
            const mode = document.getElementById('image-mode').value;
            const scheme = document.getElementById('image-scheme').value;
            
            const btn = form.querySelector('.btn-primary');
            this.setLoading(btn, true);
            
            try {
                const result = await APIService.identifyFromImage(file, ocrEngine, mode, scheme);
                window.resultsComponent.displayResults('image', result);
            } catch (error) {
                this.showError('image-results', error.message);
            } finally {
                this.setLoading(btn, false);
            }
        });
    }
    
    /**
     * Setup file upload form
     */
    setupFileForm() {
        const form = document.getElementById('form-file');
        const fileInput = document.getElementById('input-file');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const file = fileInput.files[0];
            if (!file) {
                this.showError('file-results', 'Please select a file');
                return;
            }
            
            const mode = document.getElementById('file-mode').value;
            const scheme = document.getElementById('file-scheme').value;
            
            const btn = form.querySelector('.btn-primary');
            this.setLoading(btn, true);
            
            try {
                const result = await APIService.identifyFromFile(file, mode, scheme);
                window.resultsComponent.displayResults('file', result);
            } catch (error) {
                this.showError('file-results', error.message);
            } finally {
                this.setLoading(btn, false);
            }
        });
    }
    
    /**
     * Setup custom file input styling
     */
    setupFileInputs() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const label = e.target.parentElement.querySelector('.file-name');
                if (label) {
                    const fileName = e.target.files[0]?.name || '';
                    label.textContent = fileName;
                }
            });
        });
    }
    
    /**
     * Set button loading state
     */
    setLoading(btn, loading) {
        if (loading) {
            btn.classList.add('loading');
            btn.disabled = true;
        } else {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }
    
    /**
     * Show error message
     */
    showError(containerId, message) {
        const container = document.getElementById(containerId);
        container.style.display = 'block';
        container.innerHTML = `
            <div class="card">
                <div class="alert alert-error">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="15" y1="9" x2="9" y2="15"></line>
                        <line x1="9" y1="9" x2="15" y2="15"></line>
                    </svg>
                    <span>${message}</span>
                </div>
            </div>
        `;
    }
}

// Initialize forms
window.formsComponent = new Forms();
