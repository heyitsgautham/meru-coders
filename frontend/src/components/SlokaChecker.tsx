/**
 * SlokaChecker Component
 * A beautiful text input box for checking slokas against the database
 * Features side-by-side comparison, error highlighting, and smooth UX
 */

import { useState, useCallback, useRef, useMemo } from 'react';
import { Search, CheckCircle, AlertCircle, Loader2, X, BookOpen, ArrowRight, Copy, Sparkles, GitCompare } from 'lucide-react';
import * as api from '../services/api';
import type { SlokaValidateResponse, SlokaSearchMatch } from '../types/api';
// Imported as a string and injected while mounted: class names such as .clear-btn also exist elsewhere.
import SLOKA_CHECKER_CSS from '../styles/sloka-checker.css?inline';
import { computeWordDiff } from '../utils/wordDiff';

export function SlokaChecker() {
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [result, setResult] = useState<SlokaValidateResponse | null>(null);
  const [searchMatches, setSearchMatches] = useState<SlokaSearchMatch[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showDiff, setShowDiff] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Compute word-based diff when we have both texts
  const diffResult = useMemo(() => {
    if (!result?.original_text || result.is_valid) return null;
    return computeWordDiff(inputText.trim(), result.original_text);
  }, [inputText, result]);

  const handleCheck = useCallback(async () => {
    if (!inputText.trim()) return;

    setIsLoading(true);
    setError(null);
    setResult(null);
    setSearchMatches([]);

    try {
      const validateResponse = await api.validateSloka(inputText.trim());
      
      if (validateResponse.success) {
        setResult(validateResponse);
        
        if (!validateResponse.found || (validateResponse.similarity && validateResponse.similarity < 0.8)) {
          const searchResponse = await api.searchSloka(inputText.trim(), { threshold: 0.5, limit: 5 });
          if (searchResponse.success && searchResponse.matches) {
            setSearchMatches(searchResponse.matches);
          }
        }
      } else {
        setError(validateResponse.error || 'Validation failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check sloka');
    } finally {
      setIsLoading(false);
    }
  }, [inputText]);

  const handleClear = useCallback(() => {
    setInputText('');
    setResult(null);
    setSearchMatches([]);
    setError(null);
    setShowDiff(false);
    textareaRef.current?.focus();
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleCheck();
    }
  }, [handleCheck]);

  const handleCopyCorrect = useCallback(() => {
    if (result?.original_text) {
      navigator.clipboard.writeText(result.original_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [result]);

  const getSimilarityColor = (similarity: number): string => {
    if (similarity >= 0.95) return '#10b981';
    if (similarity >= 0.8) return '#84cc16';
    if (similarity >= 0.6) return '#eab308';
    return '#ef4444';
  };

  const getSimilarityLabel = (similarity: number): string => {
    if (similarity >= 0.98) return 'Perfect!';
    if (similarity >= 0.95) return 'Excellent';
    if (similarity >= 0.9) return 'Very Good';
    if (similarity >= 0.8) return 'Good';
    if (similarity >= 0.6) return 'Fair';
    return 'Low';
  };

  return (
    <div className="sloka-checker">
      {/* Header Section */}
      <div className="checker-header">
        <div className="header-icon">
          <BookOpen size={28} />
        </div>
        <div className="header-content">
          <h3>श्लोक परीक्षक <span className="english-title">Sloka Checker</span></h3>
          <p>Verify your Sanskrit verses against our database of 14,000+ authentic slokas</p>
        </div>
      </div>

      {/* Input Section */}
      <div className="input-section">
        <div className={`textarea-wrapper ${isFocused ? 'focused' : ''}`}>
          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={handleKeyDown}
            placeholder="पेस्ट करें अपना श्लोक यहाँ...&#10;&#10;Example: अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं"
            rows={4}
          />
          {inputText && (
            <button className="clear-btn" onClick={handleClear} title="Clear">
              <X size={18} />
            </button>
          )}
        </div>

        <div className="action-row">
          <button
            className={`check-btn ${(!inputText.trim() || isLoading) ? 'disabled' : ''}`}
            onClick={handleCheck}
            disabled={!inputText.trim() || isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 size={20} className="spinner" />
                <span>Checking...</span>
              </>
            ) : (
              <>
                <Search size={20} />
                <span>Check Sloka</span>
              </>
            )}
          </button>
          <span className="hint">Press <kbd>Ctrl</kbd> + <kbd>Enter</kbd></span>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="error-box">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && (
        <div className="results-section">
          {result.found ? (
            <>
              {/* Status Banner */}
              <div className={`status-banner ${result.is_valid ? 'success' : 'warning'}`}>
                <div className="status-left">
                  {result.is_valid ? (
                    <>
                      <CheckCircle size={24} />
                      <div className="status-text">
                        <strong>Perfect Match!</strong>
                        <span>Your sloka is 100% accurate</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <AlertCircle size={24} />
                      <div className="status-text">
                        <strong>{result.difference_count} Difference{result.difference_count !== 1 ? 's' : ''} Found</strong>
                        <span>See comparison below</span>
                      </div>
                    </>
                  )}
                </div>
                <div className="status-right">
                  <div className="similarity-badge" style={{ borderColor: getSimilarityColor(result.similarity || 0) }}>
                    <span className="similarity-value" style={{ color: getSimilarityColor(result.similarity || 0) }}>
                      {result.similarity_percentage}%
                    </span>
                    <span className="similarity-label">{getSimilarityLabel(result.similarity || 0)}</span>
                  </div>
                </div>
              </div>

              {/* Metadata Pills */}
              <div className="metadata-row">
                <div className="meta-pill">
                  <span className="meta-label">Meter</span>
                  <span className="meta-value">{result.chandas || 'Unknown'}</span>
                </div>
                <div className="meta-pill">
                  <span className="meta-label">Source</span>
                  <span className="meta-value">{result.dataset_name}</span>
                </div>
                {/* Diff Toggle Button */}
                {!result.is_valid && (
                  <button 
                    className={`diff-toggle-btn ${showDiff ? 'active' : ''}`}
                    onClick={() => setShowDiff(!showDiff)}
                  >
                    <GitCompare size={16} />
                    <span>{showDiff ? 'Hide Diff' : 'Show Diff'}</span>
                  </button>
                )}
              </div>

              {/* Comparison View - Only show if there are differences */}
              {!result.is_valid && (
                <div className="comparison-container">
                  <div className="comparison-header">
                    <Sparkles size={18} />
                    <span>Side-by-Side Comparison</span>
                    {showDiff && diffResult && (
                      <div className="diff-legend">
                        <span className="legend-item delete">
                          <span className="legend-color"></span>
                          Remove ({diffResult.deletions})
                        </span>
                        <span className="legend-item insert">
                          <span className="legend-color"></span>
                          Add ({diffResult.insertions})
                        </span>
                      </div>
                    )}
                  </div>
                  
                  <div className="comparison-grid">
                    {/* Your Input */}
                    <div className="comparison-box yours">
                      <div className="box-header">
                        <span className="box-icon">📝</span>
                        <span className="box-title">Your Input</span>
                        {diffResult && (
                          <span className="box-badge error">{diffResult.deletions} missing</span>
                        )}
                      </div>
                      <div className="box-content">
                        {showDiff && diffResult ? (
                          diffResult.userSegments.map((segment, index) => (
                            <span
                              key={index}
                              className={segment.type === 'delete' ? 'diff-delete' : ''}
                            >
                              {segment.text}
                            </span>
                          ))
                        ) : (
                          <span>{inputText}</span>
                        )}
                      </div>
                    </div>

                    {/* Arrow */}
                    <div className="comparison-arrow">
                      <ArrowRight size={24} />
                    </div>

                    {/* Correct Version */}
                    <div className="comparison-box correct">
                      <div className="box-header">
                        <span className="box-icon">✓</span>
                        <span className="box-title">Correct Version</span>
                        <button className="copy-btn" onClick={handleCopyCorrect} title="Copy to clipboard">
                          {copied ? <CheckCircle size={14} /> : <Copy size={14} />}
                          <span>{copied ? 'Copied!' : 'Copy'}</span>
                        </button>
                      </div>
                      <div className="box-content">
                        {showDiff && diffResult ? (
                          diffResult.correctSegments.map((segment, index) => (
                            <span
                              key={index}
                              className={segment.type === 'insert' ? 'diff-insert' : ''}
                            >
                              {segment.text}
                            </span>
                          ))
                        ) : (
                          <span>{result.original_text}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Quick Summary */}
                  {showDiff && diffResult && (diffResult.deletions > 0 || diffResult.insertions > 0) && (
                    <div className="diff-summary-bar">
                      <span>
                        {diffResult.deletions > 0 && (
                          <span className="summary-tag delete">−{diffResult.deletions} word{diffResult.deletions !== 1 ? 's' : ''} to remove</span>
                        )}
                        {diffResult.insertions > 0 && (
                          <span className="summary-tag insert">+{diffResult.insertions} word{diffResult.insertions !== 1 ? 's' : ''} to add</span>
                        )}
                      </span>
                    </div>
                  )}

                  {/* Differences Log */}
                  {showDiff && diffResult && (
                    <div className="differences-log">
                      <div className="log-header">
                        📋 Changes Log
                      </div>
                      <div className="log-content">
                        {diffResult.userSegments
                          .filter(seg => seg.type === 'delete')
                          .map((seg, index) => (
                            <div key={`del-${index}`} className="log-item delete">
                              <span className="log-icon">−</span>
                              <span className="log-label">Remove:</span>
                              <span className="log-text">"{seg.text.trim()}"</span>
                            </div>
                          ))
                        }
                        {diffResult.correctSegments
                          .filter(seg => seg.type === 'insert')
                          .map((seg, index) => (
                            <div key={`ins-${index}`} className="log-item insert">
                              <span className="log-icon">+</span>
                              <span className="log-label">Add:</span>
                              <span className="log-text">"{seg.text.trim()}"</span>
                            </div>
                          ))
                        }
                        {diffResult.deletions === 0 && diffResult.insertions === 0 && (
                          <div className="log-item success">
                            <span className="log-icon">✓</span>
                            <span>No word-level differences (only spacing/punctuation)</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Perfect match - show the original anyway for reference */}
              {result.is_valid && (
                <div className="perfect-match-box">
                  <div className="match-header">
                    <CheckCircle size={18} />
                    <span>Verified Sloka</span>
                    <button className="copy-btn" onClick={handleCopyCorrect}>
                      {copied ? <CheckCircle size={14} /> : <Copy size={14} />}
                      <span>{copied ? 'Copied!' : 'Copy'}</span>
                    </button>
                  </div>
                  <div className="match-content">
                    {result.original_text}
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Not Found State */
            <div className="not-found-section">
              <div className="not-found-icon">
                <BookOpen size={48} />
              </div>
              <h4>Sloka Not Found</h4>
              <p>{result.message || 'This verse was not found in our database of 14,000+ slokas.'}</p>
              
              {searchMatches.length > 0 && (
                <div className="suggestions">
                  <p className="suggestions-title">Did you mean one of these?</p>
                  {searchMatches.map((match, index) => (
                    <div
                      key={index}
                      className="suggestion-item"
                      onClick={() => setInputText(match.original_text)}
                    >
                      <div className="suggestion-text">
                        {match.original_text.length > 100 
                          ? match.original_text.substring(0, 100) + '...' 
                          : match.original_text}
                      </div>
                      <div className="suggestion-meta">
                        <span>{match.chandas}</span>
                        <span>•</span>
                        <span>{match.dataset_name}</span>
                        <span className="match-percent">{Math.round(match.similarity * 100)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Styles */}
      <style>{SLOKA_CHECKER_CSS}</style>
    </div>
  );
}
