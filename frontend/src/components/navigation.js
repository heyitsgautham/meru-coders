/**
 * Navigation Component
 * Handles view switching and navigation
 */

class Navigation {
    constructor() {
        this.currentView = 'text';
        this.init();
    }
    
    init() {
        // Get all navigation buttons
        const navButtons = document.querySelectorAll('.nav-btn');
        
        // Add click listeners
        navButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.dataset.view;
                this.switchView(view);
            });
        });
    }
    
    switchView(viewName) {
        // Hide all views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        
        // Show selected view
        const targetView = document.getElementById(`view-${viewName}`);
        if (targetView) {
            targetView.classList.add('active');
        }
        
        // Update nav buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.view === viewName) {
                btn.classList.add('active');
            }
        });
        
        this.currentView = viewName;
        
        // Load examples if switching to examples view
        if (viewName === 'examples' && window.examplesComponent) {
            window.examplesComponent.loadExamples();
        }
    }
}

// Initialize navigation
window.navigation = new Navigation();
