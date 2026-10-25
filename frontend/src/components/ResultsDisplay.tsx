/**
 * ResultsDisplay Component
 * Displays meter identification results with language toggle
 */

import { useState } from 'react';
import { Download, FileText, AlertCircle, X } from 'lucide-react';
import { getDownloadURL } from '../services/api';
import type { IdentifyResponse } from '../types/api';
import { TextToSpeech } from './TextToSpeech';
import { getMeterEnglish, buildMeterCounts, getMeterStructure, getPadaSize } from './results/meterData';
import { SummarySection } from './results/SummarySection';
import { ShlokaOverview } from './results/ShlokaOverview';
import { LineAnalysisCard } from './results/LineAnalysisCard';

interface ResultsDisplayProps {
  result: IdentifyResponse;
  type: 'text' | 'image' | 'file';
  onClose?: () => void;
  compact?: boolean; // When true, hides ShlokaOverview for side-by-side layout (split view)
}


export function ResultsDisplay({ result, type, onClose, compact = false }: ResultsDisplayProps) {
  const [showSanskrit, setShowSanskrit] = useState(true);

  if (!result.success) {
    return (
      <div className="mt-8 p-6 bg-red-50 border border-red-200 rounded-[16px] flex items-start gap-4">
        <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-red-700 text-lg mb-1">Analysis Failed</p>
          <p className="text-base text-red-600">{result.error || 'An error occurred during analysis'}</p>
        </div>
      </div>
    );
  }

  const lineResults = result.result?.line || [];
  const verseResults = result.result?.verse || [];
  const meterCounts = buildMeterCounts(lineResults);
  const sortedMeters = Object.entries(meterCounts).sort((a, b) => b[1] - a[1]);

  // Check if all lines have invalid input (e.g., English text)
  const allInvalidInput = lineResults.length > 0 && lineResults.every(
    (line) => line.result?.is_valid_input === false
  );
  // Store first validation error for potential future use
  const _firstValidationError = lineResults.find(line => line.result?.validation_error)?.result?.validation_error;
  void _firstValidationError;

  // If all input is invalid, show a helpful error message
  if (allInvalidInput) {
    return (
      <div className="mt-10 animate-fadeIn" style={{ width: '100%', maxWidth: '100%' }}>
        <div className="bg-white border-2 border-amber-300 rounded-3xl p-12 shadow-lg" style={{ width: '100%', maxWidth: '1000px', margin: '0 auto' }}>
          <div className="text-center">
            <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertCircle className="w-12 h-12 text-amber-500" />
            </div>
            <h2 className="text-2xl font-bold text-amber-700 mb-4">Invalid Input</h2>
            <p className="text-lg text-gray-700 mb-2">
              Please enter valid Sanskrit text.
            </p>
            <p className="text-base text-gray-600">
              Use Devanagari (देवनागरी) or IAST with diacritics (dharmakṣetre)
            </p>
            {onClose && (
              <button
                onClick={onClose}
                className="mt-8 px-8 py-3 bg-amber-500 hover:bg-amber-600 text-white rounded-full font-semibold transition-colors"
              >
                Try Again
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="results-display mt-10 animate-fadeIn" style={{ width: '100%', maxWidth: '100%' }}>
      <div className="results-card bg-white border-2 border-gray-300 rounded-3xl p-12 shadow-lg" style={{ width: '100%', maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div className="results-header flex items-center justify-between pb-8 border-b-2 border-gray-200 bg-gray-50 -mx-12 -mt-12 px-12 pt-12 rounded-t-3xl">
          <h2 className="text-2xl font-bold text-[var(--color-text-main)]">Analysis Results</h2>
          <div className="flex items-center gap-4">
            {result.result_path && (
              <a
                href={getDownloadURL(result.result_path)}
                className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-white rounded-full text-sm font-semibold hover:shadow-lg transition-all"
              >
                <Download className="w-4 h-4" />
                Download Results
              </a>
            )}
            {onClose && (
              <button
                onClick={onClose}
                className="p-2.5 text-[var(--color-text-muted)] hover:text-[var(--color-text-main)] bg-white hover:bg-[var(--color-primary-soft)] rounded-full transition-colors border border-[var(--color-border-subtle)]"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Spacer after header */}
        <div className="mt-10" />

        {/* Summary Section - Only show in verse mode, not line-by-line */}
        {result.summary && verseResults.length > 0 && <SummarySection summary={result.summary} />}

        {/* OCR Text (for image input) */}
        {type === 'image' && result.ocr_text && (
          <div className="mb-8 p-6 bg-[#fdf8f3] border border-[var(--color-border-subtle)] rounded-[16px]">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-[var(--color-primary-soft)] rounded-lg">
                <FileText className="w-5 h-5 text-[var(--color-primary)]" />
              </div>
              <h4 className="font-semibold text-[var(--color-text-main)] text-lg">Extracted Text</h4>
            </div>
            <pre className="whitespace-pre-wrap text-base text-[var(--color-text-main)] font-serif leading-relaxed">
              {result.ocr_text}
            </pre>
          </div>
        )}

        {/* File Text (for file input) */}
        {type === 'file' && result.file_text && (
          <div className="mb-8 p-6 bg-[#fdf8f3] border border-[var(--color-border-subtle)] rounded-[16px]">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-[var(--color-primary-soft)] rounded-lg">
                <FileText className="w-5 h-5 text-[var(--color-primary)]" />
              </div>
              <h4 className="font-semibold text-[var(--color-text-main)] text-lg">File Content</h4>
            </div>
            <pre className="whitespace-pre-wrap text-base text-[var(--color-text-main)] font-serif leading-relaxed">
              {result.file_text}
            </pre>
          </div>
        )}

        {/* Text-to-Speech Component - Shows after identification */}
        {(() => {
          // Extract the original text for TTS
          let textForTTS = '';

          if (result.input?.text) {
            textForTTS = result.input.text;
          } else if (result.ocr_text) {
            textForTTS = result.ocr_text;
          } else if (result.file_text) {
            textForTTS = result.file_text;
          } else if (lineResults.length > 0) {
            // Fallback: extract text from line results
            textForTTS = lineResults.map(line => line.line).join('\n');
          }

          // Only show TTS if we have text
          if (textForTTS.trim()) {
            return (
              <TextToSpeech
                text={textForTTS}
                label="🔊 Listen to Sanskrit Recitation"
              />
            );
          }
          return null;
        })()}

        {/* IMPORTANT: Show Verse Meter (Primary Result) FIRST when available */}
        {/* This is crucial for Vedic meters (Gāyatrī, Triṣṭubh, etc.) */}
        {verseResults.length > 0 && verseResults.some(v => v.chanda && Array.isArray(v.chanda[0]) && v.chanda[0].length > 0) && (
          <div className="mb-8">
            {/* Consolidate all verse results into a single display */}
            {(() => {
              // Aggregate all verse results - combine scores for same meters
              const meterScores: Record<string, number> = {};

              verseResults.forEach(verse => {
                if (verse.chanda && Array.isArray(verse.chanda[0])) {
                  const meterName = verse.chanda[0][0];
                  const score = verse.chanda[1] || 0;
                  meterScores[meterName] = (meterScores[meterName] || 0) + score;
                }
              });

              // Get unique meters sorted by score
              const sortedMeters = Object.entries(meterScores)
                .sort((a, b) => b[1] - a[1]);

              if (sortedMeters.length === 0) return null;

              const primaryMeter = sortedMeters[0][0];
              const primaryScore = sortedMeters[0][1];
              const englishName = getMeterEnglish(primaryMeter);

              // Calculate meter structure early so we can use it in confidence fix
              const meterStructure = getMeterStructure(primaryMeter, lineResults);

              // Get confidence from backend's primary_confidence_reason if available
              const firstLineResult = lineResults[0]?.result;
              const confidenceReason = firstLineResult?.primary_confidence_reason;

              let confidenceLabel = 'High';
              let confidenceColor = '#16A34A'; // green-600
              let confidenceScore = 0;
              let confidenceReasonText = '';

              if (confidenceReason) {
                // Use backend confidence reason (cap at 10.0 for display)
                confidenceScore = Math.min(confidenceReason.confidence, 10);
                confidenceReasonText = confidenceReason.reason;

                // FIX: For Vedic meters with multiple lines, replace the per-line syllable count
                // with the total verse syllable count in the confidence explanation.
                // This prevents showing "14 syllables" when the full verse has 28 syllables (उष्णिक्)
                if (lineResults.length > 1 && meterStructure) {
                  const perLineSyllables = confidenceReason.technical_details?.syllable_count;
                  const totalSyllables = meterStructure.totalSyllables;

                  // Replace "(X syllables)" with "(Y syllables)" where Y is the total
                  if (perLineSyllables && totalSyllables && perLineSyllables !== totalSyllables) {
                    const pattern = new RegExp(`\\b${perLineSyllables}\\s+syllables?\\b`, 'gi');
                    confidenceReasonText = confidenceReasonText.replace(
                      pattern,
                      `${totalSyllables} syllables`
                    );
                  }
                }

                // Map level to label and color
                switch (confidenceReason.level) {
                  case 'very_high':
                    confidenceLabel = 'Very High';
                    confidenceColor = '#16A34A'; // green-600
                    break;
                  case 'high':
                    confidenceLabel = 'High';
                    confidenceColor = '#22C55E'; // green-500
                    break;
                  case 'medium':
                    confidenceLabel = 'Medium';
                    confidenceColor = '#F59E0B'; // amber-500
                    break;
                  case 'low':
                    confidenceLabel = 'Low';
                    confidenceColor = '#F97316'; // orange-500
                    break;
                  case 'very_low':
                    confidenceLabel = 'Very Low';
                    confidenceColor = '#EF4444'; // red-500
                    break;
                }
              } else {
                // Fallback: Calculate confidence based on total score vs total lines
                const numLines = lineResults.length || 1;
                const scorePerLine = primaryScore / Math.max(numLines, 1);
                const confidencePercent = Math.min(100, Math.round(scorePerLine * 100));
                confidenceScore = confidencePercent / 10; // Convert to 0-10 scale

                if (confidencePercent < 50) {
                  confidenceLabel = 'Low';
                  confidenceColor = '#EF4444'; // red-500
                } else if (confidencePercent < 80) {
                  confidenceLabel = 'Medium';
                  confidenceColor = '#F59E0B'; // amber-500
                }
              }

              // meterStructure already calculated earlier (line ~959)
              // to support confidence reason syllable count fix

              return (
                <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-200">
                  {/* Meter name with checkmark */}
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                      <svg className="w-7 h-7 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <div>
                      <div className="flex items-baseline gap-3">
                        <h3 className="text-3xl font-bold text-gray-900" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
                          {primaryMeter}
                        </h3>
                        {englishName && englishName !== primaryMeter && (
                          <span className="text-xl text-gray-600">({englishName})</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Syllables and Confidence - Side by side boxes */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Syllables Box */}
                    <div className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm">
                      <div className="text-sm font-medium text-gray-500 mb-1">Syllables</div>
                      <div className="text-3xl font-bold text-gray-900">
                        {meterStructure ? `${meterStructure.totalSyllables}` : '-'}
                        {meterStructure && (
                          <span className="text-lg font-normal text-gray-500 ml-2">
                            ({meterStructure.syllablesPerPada}×{meterStructure.totalPadas})
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Confidence Box - with integrated reason */}
                    <div className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm">
                      <div className="text-sm font-medium text-gray-500 mb-1">Confidence</div>
                      <div className="text-3xl font-bold" style={{ color: confidenceColor }}>
                        {confidenceLabel}
                        <span className="text-lg font-normal text-gray-500 ml-2">
                          ({Math.min(confidenceScore, 10).toFixed(1)}/10)
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Confidence Reason - Full width explanation below */}
                  {confidenceReasonText && (
                    <div className="mt-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100">
                      <div className="flex items-start gap-5">
                        <div className="flex-shrink-0 w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                          <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <div style={{ fontSize: '1.5rem', fontWeight: 600 }} className="text-blue-900 mb-4">Why this confidence score?</div>
                          <div style={{ fontSize: '1.25rem', lineHeight: '2' }} className="text-blue-800 space-y-3">
                            {confidenceReasonText.split(/(?<=[.!?])\s+/).map((sentence, idx) => (
                              <p key={idx}>{sentence.trim()}</p>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        )}

        {/* Shloka Overview - Colored syllables at a glance (hidden in compact/split view) */}
        {lineResults.length > 0 && !compact && (
          <ShlokaOverview lineResults={lineResults} />
        )}

        {/* Line-by-Line Analysis (secondary when verse results exist) */}
        {lineResults.length > 0 && (
          verseResults.length > 0 ? (
            <div className="mt-6">
              <h3 className="font-semibold text-gray-700 p-4 bg-gray-100 rounded-xl mb-4">
                Line-by-Line Analysis (Pāda Details)
              </h3>
              <div className="bg-gray-50 p-8 rounded-2xl border-2 border-gray-200">
                <div className="flex items-center justify-end mb-6">
                  <button
                    onClick={() => setShowSanskrit(prev => !prev)}
                    className="language-toggle-btn"
                  >
                    {showSanskrit ? 'Show IAST (English)' : 'Show Devanagari'}
                  </button>
                </div>
                <div className="space-y-6">
                  {lineResults.map((lineItem, index) => {
                    // Calculate padaOffset based on previous lines' padas
                    // Use the identified meter's syllables per pada, not hardcoded 8
                    const padaOffset = lineResults.slice(0, index).reduce((acc, item) => {
                      const syllables = item.result?.display_syllables || [];
                      const lgArray = item.result?.display_lg || [];
                      const validCount = syllables.filter((_, i) => lgArray[i] && lgArray[i].trim() !== '').length;
                      // Get the meter name and look up its pada size
                      const meterName = item.result?.display_chanda_primary?.split(' ')[0] || '';
                      const padaSize = getPadaSize(meterName);
                      return acc + Math.ceil(validCount / padaSize);
                    }, 0);
                    return (
                      <LineAnalysisCard
                        key={index}
                        lineItem={lineItem}
                        showSanskrit={showSanskrit}
                        padaOffset={padaOffset}
                      />
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* Identified Chanda - Clean minimal design */}
              {sortedMeters.length > 0 && (
                <div className="mb-8">
                  <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-200">
                    {/* Meter name with checkmark */}
                    {(() => {
                      const primaryMeter = sortedMeters[0][0];
                      const lineCount = sortedMeters[0][1];
                      const englishName = getMeterEnglish(primaryMeter);
                      const totalLines = lineResults.length;

                      // Get confidence from backend's primary_confidence_reason if available
                      const firstLineResult = lineResults[0]?.result;
                      const confidenceReason = firstLineResult?.primary_confidence_reason;

                      let confidenceLabel = 'High';
                      let confidenceColor = '#16A34A'; // green-600
                      let confidenceScore = 0;
                      let confidenceReasonText = '';

                      if (confidenceReason) {
                        // Use backend confidence reason (cap at 10.0 for display)
                        confidenceScore = Math.min(confidenceReason.confidence, 10);
                        confidenceReasonText = confidenceReason.reason;

                        // Get meter structure first to check if we need to fix syllable count
                        const meterStructure = getMeterStructure(primaryMeter, lineResults);

                        // FIX: For Vedic meters with multiple lines, replace the per-line syllable count
                        // with the total verse syllable count in the confidence explanation.
                        // This prevents showing "14 syllables" when the full verse has 28 syllables (उष्णिक्)
                        if (lineResults.length > 1 && meterStructure) {
                          const perLineSyllables = confidenceReason.technical_details?.syllable_count;
                          const totalSyllables = meterStructure.totalSyllables;

                          // Replace "(X syllables)" with "(Y syllables)" where Y is the total
                          if (perLineSyllables && totalSyllables && perLineSyllables !== totalSyllables) {
                            const pattern = new RegExp(`\\b${perLineSyllables}\\s+syllables?\\b`, 'gi');
                            confidenceReasonText = confidenceReasonText.replace(
                              pattern,
                              `${totalSyllables} syllables`
                            );
                          }
                        }

                        // Map level to label and color
                        switch (confidenceReason.level) {
                          case 'very_high':
                            confidenceLabel = 'Very High';
                            confidenceColor = '#16A34A'; // green-600
                            break;
                          case 'high':
                            confidenceLabel = 'High';
                            confidenceColor = '#22C55E'; // green-500
                            break;
                          case 'medium':
                            confidenceLabel = 'Medium';
                            confidenceColor = '#F59E0B'; // amber-500
                            break;
                          case 'low':
                            confidenceLabel = 'Low';
                            confidenceColor = '#F97316'; // orange-500
                            break;
                          case 'very_low':
                            confidenceLabel = 'Very Low';
                            confidenceColor = '#EF4444'; // red-500
                            break;
                        }
                      } else {
                        // Fallback to old calculation
                        const confidencePercent = Math.round((lineCount / totalLines) * 100);
                        confidenceScore = confidencePercent / 10;

                        if (confidencePercent < 50) {
                          confidenceLabel = 'Low';
                          confidenceColor = '#EF4444'; // red-500
                        } else if (confidencePercent < 80) {
                          confidenceLabel = 'Medium';
                          confidenceColor = '#F59E0B'; // amber-500
                        }
                      }

                      // Get meter structure info
                      const meterStructure = getMeterStructure(primaryMeter, lineResults);

                      return (
                        <>
                          <div className="flex items-center gap-3 mb-6">
                            <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                              <svg className="w-7 h-7 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                              </svg>
                            </div>
                            <div>
                              <div className="flex items-baseline gap-3">
                                <h3 className="text-3xl font-bold text-gray-900" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
                                  {primaryMeter}
                                </h3>
                                {englishName && englishName !== primaryMeter && (
                                  <span className="text-xl text-gray-600">({englishName})</span>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Syllables and Confidence - Side by side boxes */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Syllables Box */}
                            <div className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm">
                              <div className="text-sm font-medium text-gray-500 mb-1">Syllables</div>
                              <div className="text-3xl font-bold text-gray-900">
                                {meterStructure ? `${meterStructure.totalSyllables}` : '-'}
                                {meterStructure && (
                                  <span className="text-lg font-normal text-gray-500 ml-2">
                                    ({meterStructure.syllablesPerPada}×{meterStructure.totalPadas})
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Confidence Box */}
                            <div className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm">
                              <div className="text-sm font-medium text-gray-500 mb-1">Confidence</div>
                              <div className="text-3xl font-bold" style={{ color: confidenceColor }}>
                                {confidenceLabel}
                                <span className="text-lg font-normal text-gray-500 ml-2">
                                  ({Math.min(confidenceScore, 10).toFixed(1)}/10)
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Confidence Reason - Full width explanation below */}
                          {confidenceReasonText && (
                            <div className="mt-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100">
                              <div className="flex items-start gap-5">
                                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                                  <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                  </svg>
                                </div>
                                <div className="flex-1">
                                  <div style={{ fontSize: '1.5rem', fontWeight: 600 }} className="text-blue-900 mb-4">Why this confidence score?</div>
                                  <div style={{ fontSize: '1.25rem', lineHeight: '2' }} className="text-blue-800 space-y-3">
                                    {confidenceReasonText.split(/(?<=[.!?])\s+/).map((sentence, idx) => (
                                      <p key={idx}>{sentence.trim()}</p>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                        </>
                      );
                    })()}
                  </div>
                </div>
              )}

              <div className="bg-gray-50 p-8 rounded-2xl border-2 border-gray-200">
                <div className="flex items-center justify-between mb-8">
                  <h3 className="font-bold text-gray-800 text-xl">Line-by-Line Analysis</h3>
                  <button
                    onClick={() => setShowSanskrit(prev => !prev)}
                    className="language-toggle-btn"
                  >
                    {showSanskrit ? 'Show IAST (English)' : 'Show Devanagari'}
                  </button>
                </div>
                <div className="space-y-6">
                  {lineResults.map((lineItem, index) => {
                    // Calculate padaOffset based on previous lines' padas
                    // Use the identified meter's syllables per pada, not hardcoded 8
                    const padaOffset = lineResults.slice(0, index).reduce((acc, item) => {
                      const syllables = item.result?.display_syllables || [];
                      const lgArray = item.result?.display_lg || [];
                      const validCount = syllables.filter((_, i) => lgArray[i] && lgArray[i].trim() !== '').length;
                      // Get the meter name and look up its pada size
                      const meterName = item.result?.display_chanda_primary?.split(' ')[0] || '';
                      const padaSize = getPadaSize(meterName);
                      return acc + Math.ceil(validCount / padaSize);
                    }, 0);
                    return (
                      <LineAnalysisCard
                        key={index}
                        lineItem={lineItem}
                        showSanskrit={showSanskrit}
                        padaOffset={padaOffset}
                      />
                    );
                  })}
                </div>
              </div>
            </>
          )
        )}

        {/* No Results */}
        {lineResults.length === 0 && verseResults.length === 0 && (
          <div className="text-center py-12 bg-[#fdf8f3] rounded-[16px] border border-[var(--color-border-subtle)]">
            <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-10 h-10 text-amber-400" />
            </div>
            <p className="text-lg text-[var(--color-text-muted)]">
              No meters identified in the provided text.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
