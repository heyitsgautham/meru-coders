/**
 * API Service
 * Handles all communication with the backend REST API
 */

// API_BASE_URL is loaded from config.js
const API_BASE_URL = typeof Config !== 'undefined' ? Config.API_BASE_URL : 'http://localhost:5000/api';

class APIService {
    /**
     * Make an API request
     */
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options.headers,
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    /**
     * Identify meter from text
     */
    static async identifyFromText(text, mode = 'verse', outputScheme = 'devanagari') {
        return this.request('/identify/text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text,
                text_mode: mode,
                output_scheme: outputScheme,
            }),
        });
    }

    /**
     * Identify meter from image
     */
    static async identifyFromImage(file, ocrEngine = 'tesseract', mode = 'line', outputScheme = 'devanagari') {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('ocr_engine', ocrEngine);
        formData.append('mode', mode);
        formData.append('output_scheme', outputScheme);

        return this.request('/identify/image', {
            method: 'POST',
            body: formData,
        });
    }

    /**
     * Identify meter from file
     */
    static async identifyFromFile(file, mode = 'line', outputScheme = 'devanagari') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('mode', mode);
        formData.append('output_scheme', outputScheme);

        return this.request('/identify/file', {
            method: 'POST',
            body: formData,
        });
    }

    /**
     * Get available transliteration schemes
     */
    static async getSchemes() {
        return this.request('/schemes');
    }

    /**
     * Get example verses
     */
    static async getExamples() {
        return this.request('/examples');
    }

    /**
     * Get API info
     */
    static async getAPIInfo() {
        return this.request('/info');
    }

    /**
     * Download result file
     */
    static getDownloadURL(filename) {
        return `${API_BASE_URL}/download/${filename}`;
    }
}
