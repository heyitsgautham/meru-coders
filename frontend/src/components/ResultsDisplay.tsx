/**
 * ResultsDisplay Component
 * Displays meter identification results with language toggle
 */

import { useState } from 'react';
import { Download, FileText, AlertCircle, X } from 'lucide-react';
import { getDownloadURL } from '../services/api';
import type { IdentifyResponse } from '../types/api';
import { TextToSpeech } from './TextToSpeech';
import { getMeterEnglish, buildMeterCounts, getMeterStructure } from './results/meterData';
import { describeConfidence, rankVerseMeters, recitationText } from './results/confidence';
import { LineAnalysisCards, PadaDetails, ScriptToggle } from './results/LineAnalysisList';
import { PrimaryMeterCard } from './results/PrimaryMeterCard';
import { SummarySection } from './results/SummarySection';
import { ShlokaOverview } from './results/ShlokaOverview';

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
  const verseMeters = rankVerseMeters(verseResults);
  const hasVerseMeter = verseResults.some(v => v.chanda && Array.isArray(v.chanda[0]) && v.chanda[0].length > 0);
  const recitation = recitationText(result, lineResults);

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
        {recitation.trim() && (
          <TextToSpeech
            text={recitation}
            label="🔊 Listen to Sanskrit Recitation"
          />
        )}

        {/* The verse-level meter comes first when there is one; it is how Vedic meters are found. */}
        {hasVerseMeter && (
          <PrimaryMeterCard
            meter={verseMeters[0][0]}
            englishName={getMeterEnglish(verseMeters[0][0])}
            meterStructure={getMeterStructure(verseMeters[0][0], lineResults)}
            confidence={describeConfidence(lineResults, getMeterStructure(verseMeters[0][0], lineResults), () =>
              Math.min(100, Math.round((verseMeters[0][1] / Math.max(lineResults.length || 1, 1)) * 100)),
            )}
          />
        )}

        {/* Shloka Overview - Colored syllables at a glance (hidden in compact/split view) */}
        {lineResults.length > 0 && !compact && (
          <ShlokaOverview lineResults={lineResults} />
        )}

        {/* Line-by-Line Analysis (secondary when verse results exist) */}
        {lineResults.length > 0 && (
          verseResults.length > 0 ? (
            <PadaDetails>
              <div className="flex items-center justify-end mb-6">
                <ScriptToggle showSanskrit={showSanskrit} onToggle={() => setShowSanskrit(prev => !prev)} />
              </div>
              <LineAnalysisCards lineResults={lineResults} showSanskrit={showSanskrit} />
            </PadaDetails>
          ) : (
            <>
              {sortedMeters.length > 0 && (
                <PrimaryMeterCard
                  meter={sortedMeters[0][0]}
                  englishName={getMeterEnglish(sortedMeters[0][0])}
                  meterStructure={getMeterStructure(sortedMeters[0][0], lineResults)}
                  confidence={describeConfidence(lineResults, getMeterStructure(sortedMeters[0][0], lineResults), () =>
                    Math.round((sortedMeters[0][1] / lineResults.length) * 100),
                  )}
                />
              )}

              <div className="bg-gray-50 p-8 rounded-2xl border-2 border-gray-200">
                <div className="flex items-center justify-between mb-8">
                  <h3 className="font-bold text-gray-800 text-xl">Line-by-Line Analysis</h3>
                  <ScriptToggle showSanskrit={showSanskrit} onToggle={() => setShowSanskrit(prev => !prev)} />
                </div>
                <LineAnalysisCards lineResults={lineResults} showSanskrit={showSanskrit} />
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
