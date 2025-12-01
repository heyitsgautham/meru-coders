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
     * Transliterate Devanagari to IAST (basic mapping)
     */
    transliterateToIAST(text) {
        const devaToIAST = {
            'अ': 'a', 'आ': 'ā', 'इ': 'i', 'ई': 'ī', 'उ': 'u', 'ऊ': 'ū',
            'ऋ': 'ṛ', 'ॠ': 'ṝ', 'ऌ': 'ḷ', 'ॡ': 'ḹ', 'ए': 'e', 'ऐ': 'ai',
            'ओ': 'o', 'औ': 'au',
            'क': 'ka', 'ख': 'kha', 'ग': 'ga', 'घ': 'gha', 'ङ': 'ṅa',
            'च': 'ca', 'छ': 'cha', 'ज': 'ja', 'झ': 'jha', 'ञ': 'ña',
            'ट': 'ṭa', 'ठ': 'ṭha', 'ड': 'ḍa', 'ढ': 'ḍha', 'ण': 'ṇa',
            'त': 'ta', 'थ': 'tha', 'द': 'da', 'ध': 'dha', 'न': 'na',
            'प': 'pa', 'फ': 'pha', 'ब': 'ba', 'भ': 'bha', 'म': 'ma',
            'य': 'ya', 'र': 'ra', 'ल': 'la', 'व': 'va',
            'श': 'śa', 'ष': 'ṣa', 'स': 'sa', 'ह': 'ha',
            'ा': 'ā', 'ि': 'i', 'ी': 'ī', 'ु': 'u', 'ू': 'ū',
            'ृ': 'ṛ', 'ॄ': 'ṝ', 'ॢ': 'ḷ', 'ॣ': 'ḹ',
            'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
            'ं': 'ṃ', 'ः': 'ḥ', '्': '', 'ँ': 'm̐'
        };

        let result = '';
        for (let char of text) {
            result += devaToIAST[char] || char;
        }
        return result;
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

        // Meters Found - Show ONLY top meters from each line
        if (data.result && data.result.line) {
            // Build our own summary showing only top meter per line
            const topMeterCounts = {};

            data.result.line.forEach(lineItem => {
                const result = lineItem.result;
                if (!result) return;

                let topMeter = null;

                // Extract top meter from display_chanda_primary (new format)
                if (result.display_chanda_primary && result.display_chanda_primary.trim()) {
                    const primaryMeters = result.display_chanda_primary.split('|').map(m => m.trim());
                    if (primaryMeters.length > 0) {
                        // Extract meter name (before the bracket with confidence score)
                        const meterMatch = primaryMeters[0].match(/^(.+?)\s*\[[\d.]+\]$/);
                        topMeter = meterMatch ? meterMatch[1].trim() : primaryMeters[0];

                        // Remove transliteration if present
                        const parenMatch = topMeter.match(/^(.+?)\s*\([^)]+\)$/);
                        if (parenMatch) {
                            topMeter = parenMatch[1].trim();
                        }
                    }
                }
                // Fallback to display_chanda (old format) - take first meter only
                else if (result.found && result.display_chanda) {
                    const meters = result.display_chanda.split('/').map(m => m.trim());
                    if (meters.length > 0) {
                        topMeter = meters[0];
                        // Extract just the meter name, remove pada info
                        const cleanMatch = topMeter.match(/^([^\(]+)/);
                        if (cleanMatch) {
                            topMeter = cleanMatch[1].trim();
                        }
                    }
                }

                // Count this top meter
                if (topMeter) {
                    topMeterCounts[topMeter] = (topMeterCounts[topMeter] || 0) + 1;
                }
            });

            // Display the summary if we found any meters
            if (Object.keys(topMeterCounts).length > 0) {
                html += '<div class="meters-found-section">';
                html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-sm);">';
                html += '<h3 style="margin: 0;">Meters Identified</h3>';
                html += '<button class="language-toggle-btn-compact" onclick="window.resultsComponent.toggleLanguage(event)">EN</button>';
                html += '</div>';
                html += '<div class="meters-list">';

                // Sort by count (highest to lowest)
                const sortedMeters = Object.entries(topMeterCounts).sort((a, b) => b[1] - a[1]);

                sortedMeters.forEach(([meter, count]) => {
                    // The meter name as is (in Devanagari)
                    let devanagari = meter;
                    let iast = '';

                    // Check if there's a parenthetical note (like "पाद 1-2")
                    const parenMatch = meter.match(/^(.+?)\s*\((.+?)\)$/);
                    if (parenMatch) {
                        // Full name with parentheses for Devanagari
                        devanagari = meter;
                        // Transliterate the main part, keep parenthetical as is
                        const mainPart = parenMatch[1].trim();
                        const parenPart = parenMatch[2].trim();
                        // Try mapping first, fall back to transliteration
                        let mainIAST = this.getMeterEnglish(mainPart);
                        if (mainIAST === mainPart || mainIAST === this.transliterateToIAST(mainPart)) {
                            // No mapping found, use transliteration
                            mainIAST = this.transliterateToIAST(mainPart);
                        }
                        iast = `${mainIAST} (${parenPart})`;
                    } else {
                        // Simple meter name without parentheses
                        // Try mapping first, fall back to transliteration
                        iast = this.getMeterEnglish(meter);
                        if (iast === meter || iast === this.transliterateToIAST(meter)) {
                            // No mapping found, use transliteration
                            iast = this.transliterateToIAST(meter);
                        }
                    }

                    html += `<div class="meter-badge">
                        <span class="meter-name-large meter-name-toggle" data-devanagari="${this.escapeHtml(devanagari)}" data-iast="${this.escapeHtml(iast)}">${this.escapeHtml(devanagari)}</span>
                        <span class="meter-count">${count} line${count > 1 ? 's' : ''}</span>
                    </div>`;
                });

                html += '</div>';
                html += '</div>';
            }
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

        // IMPORTANT: Show Verse Analysis FIRST when available
        // This is crucial for Vedic meters (Gāyatrī, Triṣṭubh, etc.) 
        // where the meter is identified from the complete verse, not individual lines
        if (verseResults && verseResults.length > 0) {
            html += '<div class="verse-analysis-section primary-result">';
            html += '<h4>🕉️ Verse Meter (Primary Result)</h4>';
            verseResults.forEach((verse, vIndex) => {
                html += '<div class="verse-result-card">';
                if (verse.chanda && verse.chanda[0]) {
                    const meterNames = verse.chanda[0];
                    const score = verse.chanda[1];
                    const primaryMeter = meterNames[0];
                    const englishName = this.getMeterEnglish(primaryMeter);

                    // Calculate confidence as percentage
                    // For verse mode: score is cumulative based on lines
                    // A score of 4+ for 2 lines = excellent match
                    // Normalize: score per line, then convert to percentage
                    const numLines = lineResults ? lineResults.length : 1;
                    const scorePerLine = score / Math.max(numLines, 1);
                    // scorePerLine of 2.0+ means holistic match was found (excellent)
                    // scorePerLine of 1.0 means basic line match
                    // Convert to 0-100% scale where 2.0 per line = 100%
                    const confidencePercent = Math.min(100, Math.round((scorePerLine / 2.0) * 100));

                    let confidenceClass;
                    if (confidencePercent >= 80) {
                        confidenceClass = 'confidence-high';
                    } else if (confidencePercent >= 50) {
                        confidenceClass = 'confidence-medium';
                    } else {
                        confidenceClass = 'confidence-low';
                    }

                    html += '<div class="verse-meter-display">';
                    html += `<span class="verse-meter-name">${primaryMeter}</span>`;
                    if (englishName && englishName !== primaryMeter) {
                        html += `<span class="verse-meter-english">(${englishName})</span>`;
                    }
                    html += `<span class="verse-meter-score ${confidenceClass}">${confidencePercent}% Match</span>`;
                    html += '</div>';

                    if (meterNames.length > 1) {
                        html += '<div class="verse-meter-alternates">';
                        html += '<small>Alternates: ' + meterNames.slice(1).join(', ') + '</small>';
                        html += '</div>';
                    }
                }
                html += '</div>';
            });
            html += '<p class="verse-note"><em>Note: For Vedic meters (Gāyatrī, Triṣṭubh, Jagatī, etc.), the verse-level identification is the primary result. Line-by-line patterns below show individual pāda analysis.</em></p>';
            html += '</div>';
        }

        // Render line results (secondary, for detailed analysis)
        if (lineResults && lineResults.length > 0) {
            const hasVerseResult = verseResults && verseResults.length > 0;
            html += hasVerseResult ? '<details class="line-details"><summary>Line-by-Line Analysis (Pāda Details)</summary>' : '<h4>Line-by-Line Analysis</h4>';

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
                    // Transliterate syllables to IAST for English display
                    const syllablesIAST = validSyllables.map(syl => this.transliterateToIAST(syl));

                    // Create table structure
                    html += '<div class="analysis-table-container">';
                    html += '<table class="analysis-table">';

                    // Header row - Syllables
                    html += '<thead><tr>';
                    html += '<th class="row-label-cell">Akṣarāṇi</th>';
                    validSyllables.forEach((syllable, idx) => {
                        const iast = syllablesIAST[idx];
                        html += `<th class="syllable-cell table-content" data-sanskrit="${this.escapeHtml(syllable)}" data-english="${this.escapeHtml(iast)}">${this.escapeHtml(iast)}</th>`;
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

                // Identified Meter - Show only TOP MOST RELEVANT meter
                html += '<div class="meter-result-row">';

                // Use display_chanda_primary if available (high-confidence matches only)
                if (result.display_chanda_primary && result.display_chanda_primary.trim()) {
                    // Split multiple primary matches and SHOW ONLY THE FIRST ONE
                    const primaryMeters = result.display_chanda_primary.split('|').map(m => m.trim());
                    const firstMeter = primaryMeters[0];

                    // Extract meter name (before the bracket with confidence score)
                    const meterMatch = firstMeter.match(/^(.+?)\s*\[[\d.]+\]$/);
                    const meterName = meterMatch ? meterMatch[1].trim() : firstMeter;

                    html += `<span class="meter-name-identified">${this.escapeHtml(meterName)}</span>`;
                    html += `<span class="meter-match match-exact">Exact Match</span>`;
                } else if (result.found && result.display_chanda) {
                    // Fallback to old display_chanda field (show only first meter)
                    const meters = result.display_chanda.split('/').map(m => m.trim());
                    const firstMeter = meters[0];
                    const englishName = this.getMeterEnglish(firstMeter);
                    html += `<span class="meter-name-identified" data-hindi="${firstMeter}" data-english="${englishName}">${firstMeter}</span>`;
                    html += `<span class="meter-match match-exact">Match Found</span>`;
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

            // Close the details tag if we opened it (when verse results exist)
            if (hasVerseResult) {
                html += '</details>';
            }
        }

        // NOTE: Verse results are now rendered FIRST (above line results)
        // so we don't need to render them again here

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

        // Check if it's the compact button (shows "EN" or "हि")
        const isCompact = button.classList.contains('language-toggle-btn-compact');
        const isShowingDevanagari = isCompact ? (button.textContent === 'EN') : (button.textContent === 'Change to English');

        // Toggle meter names in the summary section
        const meterToggles = document.querySelectorAll('.meter-name-toggle');
        meterToggles.forEach(element => {
            const devanagari = element.dataset.devanagari;
            const iast = element.dataset.iast;

            if (devanagari && iast) {
                element.textContent = isShowingDevanagari ? iast : devanagari;
            }
        });

        // Toggle meter names in line analysis
        const meterNames = document.querySelectorAll('.meter-name-large:not(.meter-name-toggle), .meter-name-identified');
        meterNames.forEach(element => {
            const hindi = element.dataset.hindi || element.textContent;
            const english = element.dataset.english || element.textContent;

            // Store both values if not already stored
            if (!element.dataset.hindi) {
                element.dataset.hindi = hindi;
            }
            if (!element.dataset.english) {
                element.dataset.english = english;
            }

            element.textContent = isShowingDevanagari ? english : hindi;
        });

        // Update button text
        if (isCompact) {
            button.textContent = isShowingDevanagari ? 'हि' : 'EN';
        } else {
            button.textContent = isShowingDevanagari ? 'Change to Sanskrit' : 'Change to English';
        }
    }

    /**
     * Toggle display of alternate meter matches
     */
    toggleAlternates(event, lineIndex) {
        const button = event.target;
        const alternatesDiv = document.getElementById(`alternates-${lineIndex}`);

        if (alternatesDiv) {
            if (alternatesDiv.style.display === 'none') {
                alternatesDiv.style.display = 'block';
                button.textContent = button.textContent.replace('+', '−');
            } else {
                alternatesDiv.style.display = 'none';
                button.textContent = button.textContent.replace('−', '+');
            }
        }
    }

    /**
     * Toggle between Sanskrit and English table content (Syllables, L/G and Gana values)
     */
    toggleTableLanguage(event) {
        const button = event.target;
        const tableContent = document.querySelectorAll('.table-content');
        const isEnglish = button.textContent === 'Change to Sanskrit';

        tableContent.forEach(element => {
            const sanskrit = element.dataset.sanskrit;
            const english = element.dataset.english;

            if (sanskrit && english) {
                element.textContent = isEnglish ? sanskrit : english;
            }
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
