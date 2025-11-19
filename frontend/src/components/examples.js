/**
 * Examples Component
 * Loads and displays example verses
 */

class Examples {
    constructor() {
        this.examples = [];
        this.loaded = false;
    }
    
    /**
     * Load examples from API
     */
    async loadExamples() {
        if (this.loaded) return;
        
        const container = document.getElementById('examples-list');
        container.innerHTML = '<div class="empty-state">Loading examples...</div>';
        
        try {
            const response = await APIService.getExamples();
            
            if (response.success && response.examples) {
                this.examples = response.examples;
                this.renderExamples();
                this.loaded = true;
            } else {
                container.innerHTML = '<div class="empty-state">No examples available</div>';
            }
        } catch (error) {
            container.innerHTML = `
                <div class="alert alert-error">
                    Failed to load examples: ${error.message}
                </div>
            `;
        }
    }
    
    /**
     * Render examples grid
     */
    renderExamples() {
        const container = document.getElementById('examples-list');
        
        if (this.examples.length === 0) {
            container.innerHTML = '<div class="empty-state">No examples available</div>';
            return;
        }
        
        let html = '';
        
        this.examples.forEach((example, index) => {
            // Handle new format: {meter: string, lines: array}
            const meterName = example.meter || example.metre || example.title || 'Unknown';
            const text = Array.isArray(example.lines) 
                ? example.lines.filter(line => line.trim()).join('\n')
                : (example.text || example.verse || '');
            
            html += '<div class="example-card" data-index="' + index + '">';
            html += `<div class="example-title">${this.escapeHtml(meterName)}</div>`;
            html += `<div class="example-text">${this.escapeHtml(text)}</div>`;
            html += '<div class="example-meta">';
            html += '<span class="example-action">Try this →</span>';
            html += '</div>';
            html += '</div>';
        });
        
        container.innerHTML = html;
        
        // Add click handlers
        container.querySelectorAll('.example-card').forEach(card => {
            card.addEventListener('click', () => {
                const index = parseInt(card.dataset.index);
                this.useExample(index);
            });
        });
    }
    
    /**
     * Use an example in the text input
     */
    useExample(index) {
        const example = this.examples[index];
        if (!example) return;
        
        // Handle new format: {meter: string, lines: array}
        const text = Array.isArray(example.lines) 
            ? example.lines.filter(line => line.trim()).join('\n')
            : (example.text || example.verse || '');
        
        // Switch to text view
        window.navigation.switchView('text');
        
        // Fill in the text
        document.getElementById('input-text').value = text;
        
        // Scroll to the form
        document.getElementById('view-text').scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize examples component
window.examplesComponent = new Examples();
