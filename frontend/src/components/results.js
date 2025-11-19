/**
 * Results Component
 * Displays meter identification results
 */

class Results {
    /**
     * Get English transliteration for meter name
     */
    getMeterEnglish(meterName) {
        // Common meter name mappings
        const meterMap = {
            'इन्द्रवज्रा': 'Indravajrā',
            'उपेन्द्रवज्रा': 'Upendravajrā',
            'शालिनी': 'Śālinī',
            'वसन्ततिलका': 'Vasantatilakā',
            'मालिनी': 'Mālinī',
            'शार्दूलविक्रीडित': 'Śārdūlavikrīḍita',
            'मन्दाक्रान्ता': 'Mandākrāntā',
            'स्रग्धरा': 'Sragdharā',
            'भुजङ्गप्रयात': 'Bhujaṅgaprayāta',
            'पञ्चचामर': 'Pañcacāmara',
            'अनुष्टुभ्': 'Anuṣṭubh',
            'स्लोक': 'Śloka',
            'अर्या': 'Āryā',
            'गीति': 'Gīti',
            'उपजाति': 'Upajāti'
        };
        
        return meterMap[meterName] || this.simpleTransliterate(meterName);
    }
    
    /**
     * Simple transliteration fallback
     */
    simpleTransliterate(text) {
        // This is a basic fallback - in production you'd use a proper library
        return text;
    }
    
    /**
     * Display results for different input types
     */
    displayResults(type, data) {
        const containerId = `${type}-results`;
        const container = document.getElementById(containerId);
        
        if (!data.success) {
            this.showError(container, data.error || 'Analysis failed');
            return;
        }
        
        container.style.display = 'block';
        
        let html = '<div class="card">';
        
        // Header
        html += '<div class="results-header">';
        html += '<h2>Analysis Results</h2>';
        if (data.result_path) {
            html += `<a href="${APIService.getDownloadURL(data.result_path)}" class="download-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Download Results
            </a>`;
        }
        html += '</div>';
        
        // Meters Found - Show prominently first!
        if (data.summary && data.summary.line && data.summary.line.match && data.summary.line.match.chanda) {
            html += '<div class="meters-found-section">';
            html += '<h3>Meters Identified</h3>';
            html += '<div class="meters-list">';
            const chandas = data.summary.line.match.chanda;
            Object.entries(chandas).forEach(([meter, count]) => {
                const englishName = this.getMeterEnglish(meter);
                html += `<div class="meter-badge">
                    <span class="meter-name-large" data-hindi="${meter}" data-english="${englishName}">${meter}</span>
                    <span class="meter-count">${count} line${count > 1 ? 's' : ''}</span>
                </div>`;
            });
            html += '</div>';
            html += '<button class="language-toggle-btn" onclick="window.resultsComponent.toggleLanguage(event)">Change to English</button>';
            html += '</div>';
        }
        
        // Summary - Collapsible
        if (data.summary) {
            html += '<details class="summary-details">';
            html += '<summary class="summary-toggle">View Summary Statistics</summary>';
            html += '<div class="summary-content">';
            html += this.renderSummary(data.summary);
            html += '</div>';
            html += '</details>';
        }
        
        // OCR text (for image input)
        if (type === 'image' && data.ocr_text) {
            html += '<div class="ocr-section">';
            html += '<h4>';
            html += '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">';
            html += '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>';
            html += '<polyline points="14 2 14 8 20 8"></polyline>';
            html += '<line x1="16" y1="13" x2="8" y2="13"></line>';
            html += '<line x1="16" y1="17" x2="8" y2="17"></line>';
            html += '<line x1="10" y1="9" x2="8" y2="9"></line>';
            html += '</svg>';
            html += 'Extracted Text';
            html += '</h4>';
            html += `<div class="ocr-text">${this.escapeHtml(data.ocr_text)}</div>`;
            html += '</div>';
        }
        
        // Results table
        if (data.result) {
            const lineResults = data.result.line || [];
            const verseResults = data.result.verse || [];
            
            if (lineResults.length > 0 || verseResults.length > 0) {
                html += this.renderResultsTable(lineResults, verseResults);
            } else {
                html += '<div class="alert alert-warning">';
                html += '<span>No meters identified in the provided text.</span>';
                html += '</div>';
            }
        } else {
            html += '<div class="alert alert-warning">';
            html += '<span>No meters identified in the provided text.</span>';
            html += '</div>';
        }
        
        html += '</div>';
        
        container.innerHTML = html;
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    /**
     * Render summary section
     */
    renderSummary(summary) {
        let html = '<div class="result-summary-container">';
        
        // Summary stats box
        html += '<div class="summary-box">';
        html += '<h4>Summary</h4>';
        html += '<div class="summary-stats">';
        
        // Count section
        if (summary.count) {
            if (summary.count.line !== undefined) {
                html += '<div class="summary-item">';
                html += '<span class="summary-label">Total Lines</span>';
                html += `<span class="summary-value">${summary.count.line}</span>`;
                html += '</div>';
            }
            
            if (summary.count.match_line !== undefined) {
                html += '<div class="summary-item">';
                html += '<span class="summary-label">Identified Lines</span>';
                html += `<span class="summary-value">${summary.count.match_line}</span>`;
                html += '</div>';
            }
        }
        
        // Unique meters count
        if (summary.line && summary.line.match && summary.line.match.chanda) {
            const uniqueMeters = Object.keys(summary.line.match.chanda).length;
            html += '<div class="summary-item">';
            html += '<span class="summary-label">Unique Meters</span>';
            html += `<span class="summary-value">${uniqueMeters}</span>`;
            html += '</div>';
        }
        
        html += '</div></div>';
        
        // Meters found box
        if (summary.line && summary.line.match && summary.line.match.chanda) {
            html += '<div class="summary-box">';
            html += '<h4>Meters Found</h4>';
            html += '<div class="meters-found-list">';
            Object.entries(summary.line.match.chanda).forEach(([meter, count]) => {
                const englishName = this.getMeterEnglish(meter);
                html += `<div class="meter-found-item">
                    <span class="meter-name-text">${meter}<br><small>${englishName}</small></span>
                    <span class="meter-count-badge">${count} line${count > 1 ? 's' : ''}</span>
                </div>`;
            });
            html += '</div></div>';
        }
        
        html += '</div>';
        
        return html;
    }
    
    /**
     * Render results table
     */
    renderResultsTable(lineResults, verseResults) {
        let html = '';
        
        // Render line results
        if (lineResults && lineResults.length > 0) {
            html += '<h4>Line-by-Line Analysis</h4>';
            
            lineResults.forEach((lineItem, index) => {
                const result = lineItem.result || {};
                const line = lineItem.line || '';
                
                html += '<div class="line-analysis-card">';
                html += `<div class="line-header">Line ${index + 1}</div>`;
                
                // Get data directly from backend
                const syllables = result.display_syllables || [];
                const lgArray = result.display_lg || [];
                const ganaString = result.display_gana || '';
                
                // Filter out syllables with empty L/G marks (like halanta)
                const validSyllables = [];
                const validLG = [];
                syllables.forEach((syl, idx) => {
                    if (lgArray[idx] && lgArray[idx].trim() !== '') {
                        validSyllables.push(syl);
                        validLG.push(lgArray[idx]);
                    }
                });
                
                if (validSyllables.length > 0) {
                    // Create table structure
                    html += '<div class="analysis-table-container">';
                    html += '<table class="analysis-table">';
                    
                    // Header row - Syllables
                    html += '<thead><tr>';
                    html += '<th class="row-label-cell">Akṣarāṇi</th>';
                    validSyllables.forEach((syllable) => {
                        html += `<th>${this.escapeHtml(syllable)}</th>`;
                    });
                    html += '</tr></thead>';
                    
                    html += '<tbody>';
                    
                    // L/G Pattern row
                    if (validLG.length > 0) {
                        html += '<tr>';
                        html += '<td class="row-label-cell">Laghu-Guru</td>';
                        validLG.forEach(lg => {
                            const isLaghu = lg === 'ल' || lg === 'L';
                            const sanskritLG = (lg === 'ग' || lg === 'G') ? 'ग' : 'ल';
                            const englishLG = (lg === 'ग' || lg === 'G') ? 'G' : 'L';
                            html += `<td class="lg-cell ${isLaghu ? 'laghu' : 'guru'} table-content" data-sanskrit="${sanskritLG}" data-english="${englishLG}">${englishLG}</td>`;
                        });
                        html += '</tr>';
                    }
                    
                    // Gana row - each gana spans 3 syllables
                    if (ganaString) {
                        html += '<tr>';
                        html += '<td class="row-label-cell">Gaṇa</td>';
                        const ganaChars = Array.from(ganaString);
                        let cellsUsed = 0;
                        
                        ganaChars.forEach((ganaChar) => {
                            if (cellsUsed < validSyllables.length) {
                                const spanCount = Math.min(3, validSyllables.length - cellsUsed);
                                // Get English equivalent for gana character
                                const ganaMap = {
                                    'य': 'Y', 'र': 'R', 'त': 'T', 'न': 'N',
                                    'भ': 'B', 'ज': 'J', 'स': 'S', 'म': 'M',
                                    'ल': 'L', 'ग': 'G'
                                };
                                const englishGana = ganaMap[ganaChar] || ganaChar;
                                html += `<td colspan="${spanCount}" class="gana-cell table-content" data-sanskrit="${ganaChar}" data-english="${englishGana}">${englishGana}</td>`;
                                cellsUsed += spanCount;
                            }
                        });
                        
                        // Fill remaining cells if any
                        if (cellsUsed < validSyllables.length) {
                            const remainingCells = validSyllables.length - cellsUsed;
                            html += `<td colspan="${remainingCells}" class="gana-cell-empty"></td>`;
                        }
                        html += '</tr>';
                    }
                    
                    html += '</tbody>';
                    html += '</table>';
                    
                    // Add language toggle button for table content
                    html += '<button class="table-language-toggle-btn" onclick="window.resultsComponent.toggleTableLanguage(event)">Change to Sanskrit</button>';
                    
                    html += '</div>';
                }
                
                // Identified Meter
                html += '<div class="meter-result-row">';
                if (result.found && result.display_chanda) {
                    const englishName = this.getMeterEnglish(result.display_chanda);
                    html += `<span class="meter-name-identified" data-hindi="${result.display_chanda}" data-english="${englishName}">${result.display_chanda}</span>`;
                    html += `<span class="meter-match match-exact">Exact Match</span>`;
                } else if (result.fuzzy && result.fuzzy.length > 0) {
                    const firstFuzzy = result.fuzzy[0];
                    const fuzzyMeter = firstFuzzy.display_chanda || '-';
                    const englishName = this.getMeterEnglish(fuzzyMeter);
                    html += `<span class="meter-name-identified" data-hindi="${fuzzyMeter}" data-english="${englishName}">${fuzzyMeter}</span>`;
                    html += `<span class="meter-match match-fuzzy">Fuzzy (${Math.round(firstFuzzy.similarity * 100)}%)</span>`;
                } else {
                    html += '<span class="meter-name-identified">No match found</span>';
                }
                html += '</div>';
                
                html += '</div>';
            });
        }
        
        // Render verse results
        if (verseResults && verseResults.length > 0) {
            html += '<h4>Verse Analysis</h4>';
            verseResults.forEach((verse, vIndex) => {
                html += '<div class="verse-result">';
                if (verse.chanda && verse.chanda[0]) {
                    html += `<h5>Verse ${vIndex + 1}: ${verse.chanda[0].join(' / ')} (Score: ${verse.chanda[1]})</h5>`;
                }
                html += '</div>';
            });
        }
        
        return html;
    }
    
    /**
     * Show error message
     */
    showError(container, message) {
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
    
    /**
     * Toggle between Hindi and English meter names
     */
    toggleLanguage(event) {
        const button = event.target;
        const meterNames = document.querySelectorAll('.meter-name-large, .meter-name-identified');
        const isEnglish = button.textContent === 'Change to Sanskrit';
        
        meterNames.forEach(element => {
            const hindi = element.dataset.hindi || element.textContent;
            const english = element.dataset.english || element.textContent;
            
            if (!element.dataset.hindi) {
                element.dataset.hindi = hindi;
                element.dataset.english = english;
            }
            
            element.textContent = isEnglish ? hindi : english;
        });
        
        button.textContent = isEnglish ? 'Change to English' : 'Change to Sanskrit';
    }
    
    /**
     * Toggle between Sanskrit and English table content (L/G and Gana values)
     */
    toggleTableLanguage(event) {
        const button = event.target;
        const tableContent = document.querySelectorAll('.table-content');
        const isEnglish = button.textContent === 'Change to Sanskrit';
        
        tableContent.forEach(element => {
            const sanskrit = element.dataset.sanskrit;
            const english = element.dataset.english;
            
            element.textContent = isEnglish ? sanskrit : english;
        });
        
        button.textContent = isEnglish ? 'Change to English' : 'Change to Sanskrit';
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize results component
window.resultsComponent = new Results();
