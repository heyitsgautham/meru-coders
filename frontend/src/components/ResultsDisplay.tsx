/**
 * ResultsDisplay Component
 * Displays meter identification results with language toggle
 */

import { useState } from 'react';
import { Download, ChevronDown, ChevronUp, FileText, AlertCircle, X } from 'lucide-react';
import { getDownloadURL } from '../services/api';
import type { IdentifyResponse, LineResult, Summary } from '../types/api';

interface ResultsDisplayProps {
  result: IdentifyResponse;
  type: 'text' | 'image' | 'file';
  onClose?: () => void;
}

// Meter name mappings for English transliteration
const METER_MAP: Record<string, string> = {
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

// Devanagari to IAST mapping - improved for proper transliteration
const DEVA_TO_IAST: Record<string, string> = {
  'अ': 'a', 'आ': 'ā', 'इ': 'i', 'ई': 'ī', 'उ': 'u', 'ऊ': 'ū',
  'ऋ': 'ṛ', 'ॠ': 'ṝ', 'ऌ': 'ḷ', 'ॡ': 'ḹ', 'ए': 'e', 'ऐ': 'ai',
  'ओ': 'o', 'औ': 'au',
  'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ṅ',
  'च': 'c', 'छ': 'ch', 'ज': 'j', 'झ': 'jh', 'ञ': 'ñ',
  'ट': 'ṭ', 'ठ': 'ṭh', 'ड': 'ḍ', 'ढ': 'ḍh', 'ण': 'ṇ',
  'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
  'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
  'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
  'श': 'ś', 'ष': 'ṣ', 'स': 's', 'ह': 'h',
  'ा': 'ā', 'ि': 'i', 'ी': 'ī', 'ु': 'u', 'ू': 'ū',
  'ृ': 'ṛ', 'ॄ': 'ṝ', 'ॢ': 'ḷ', 'ॣ': 'ḹ',
  'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
  'ं': 'ṃ', 'ः': 'ḥ', '्': '', 'ँ': 'ṁ',
  // Additional characters
  'ऽ': "'", '॰': '.', '।': '|', '॥': '||',
  // Nukta variants
  'क़': 'q', 'ख़': 'ḵh', 'ग़': 'ġ', 'ज़': 'z', 'फ़': 'f',
  // Numbers
  '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
  '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
};

// Gana mappings
const GANA_MAP: Record<string, string> = {
  'य': 'Y', 'र': 'R', 'त': 'T', 'न': 'N',
  'भ': 'B', 'ज': 'J', 'स': 'S', 'म': 'M',
  'ल': 'L', 'ग': 'G'
};

// Transliterate Devanagari to IAST - improved algorithm
function transliterateToIAST(text: string): string {
  let result = '';
  const chars = Array.from(text);
  
  for (let i = 0; i < chars.length; i++) {
    const char = chars[i];
    const nextChar = chars[i + 1];
    
    // Check if this is a consonant
    const isConsonant = /[क-ह]/.test(char);
    
    if (DEVA_TO_IAST[char] !== undefined) {
      result += DEVA_TO_IAST[char];
      
      // Add inherent 'a' after consonant if no vowel sign or halant follows
      if (isConsonant && nextChar) {
        const isVowelSign = /[ा-ौ]/.test(nextChar);
        const isHalant = nextChar === '्';
        const isAnusvara = nextChar === 'ं';
        const isVisarga = nextChar === 'ः';
        
        if (!isVowelSign && !isHalant && !isAnusvara && !isVisarga) {
          result += 'a';
        }
      } else if (isConsonant && !nextChar) {
        // Last character is a consonant, add inherent 'a'
        result += 'a';
      }
    } else {
      result += char;
    }
  }
  
  return result;
}

// Get English name for meter
function getMeterEnglish(meterName: string): string {
  return METER_MAP[meterName] || transliterateToIAST(meterName);
}

// Extract top meter from a line result
function extractTopMeter(lineItem: LineResult): string | null {
  const result = lineItem.result;
  if (!result) return null;

  // Extract from display_chanda_primary (new format with confidence scores)
  if (result.display_chanda_primary && result.display_chanda_primary.trim()) {
    const primaryMeters = result.display_chanda_primary.split('|').map(m => m.trim());
    if (primaryMeters.length > 0) {
      const meterMatch = primaryMeters[0].match(/^(.+?)\s*\[[\d.]+\]$/);
      let topMeter = meterMatch ? meterMatch[1].trim() : primaryMeters[0];
      
      // Remove transliteration if present
      const parenMatch = topMeter.match(/^(.+?)\s*\([^)]+\)$/);
      if (parenMatch) {
        topMeter = parenMatch[1].trim();
      }
      return topMeter;
    }
  }

  // Fallback to display_chanda (old format)
  if (result.found && result.display_chanda) {
    const meters = result.display_chanda.split('/').map(m => m.trim());
    if (meters.length > 0) {
      const cleanMatch = meters[0].match(/^([^\(]+)/);
      return cleanMatch ? cleanMatch[1].trim() : meters[0];
    }
  }

  return null;
}

// Build top meter counts from line results
function buildMeterCounts(lineResults: LineResult[]): Record<string, number> {
  const counts: Record<string, number> = {};
  
  lineResults.forEach(lineItem => {
    const topMeter = extractTopMeter(lineItem);
    if (topMeter) {
      counts[topMeter] = (counts[topMeter] || 0) + 1;
    }
  });

  return counts;
}

// Summary Section Component
function SummarySection({ summary }: { summary: Summary }) {
  const [isOpen, setIsOpen] = useState(false);

  const lineCount = summary.count?.line || 0;
  const matchCount = summary.count?.match_line || 0;
  const chandaCount = summary.line?.match?.chanda 
    ? Object.keys(summary.line.match.chanda).length 
    : 0;

  return (
    <div className="border border-[var(--color-border-subtle)] rounded-[16px] overflow-hidden mb-8 bg-white shadow-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-5 bg-[#fdf8f3] hover:bg-[var(--color-primary-soft)] transition-colors border-b border-[var(--color-border-subtle)]"
      >
        <span className="font-semibold text-[var(--color-text-main)] text-base">View Summary Statistics</span>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-[var(--color-text-muted)]" />
        ) : (
          <ChevronDown className="w-5 h-5 text-[var(--color-text-muted)]" />
        )}
      </button>
      
      {isOpen && (
        <div className="p-6 border-t border-[var(--color-border-subtle)] bg-white">
          <div className="grid grid-cols-3 gap-5 mb-6">
            <div className="text-center p-5 bg-[#fdf8f3] rounded-xl border border-[var(--color-border-subtle)]">
              <div className="text-3xl font-bold text-[var(--color-primary)] mb-2">{lineCount}</div>
              <div className="text-sm font-medium text-[var(--color-text-muted)]">Total Lines</div>
            </div>
            <div className="text-center p-5 bg-[#fdf8f3] rounded-xl border border-[var(--color-border-subtle)]">
              <div className="text-3xl font-bold text-[var(--color-primary)] mb-2">{matchCount}</div>
              <div className="text-sm font-medium text-[var(--color-text-muted)]">Identified</div>
            </div>
            <div className="text-center p-5 bg-[#fdf8f3] rounded-xl border border-[var(--color-border-subtle)]">
              <div className="text-3xl font-bold text-[var(--color-primary)] mb-2">{chandaCount}</div>
              <div className="text-sm font-medium text-[var(--color-text-muted)]">Unique Meters</div>
            </div>
          </div>

          {summary.line?.match?.chanda && Object.keys(summary.line.match.chanda).length > 0 && (
            <div className="bg-[#fdf8f3] p-5 rounded-xl border border-[var(--color-border-subtle)]">
              <h4 className="font-semibold text-[var(--color-text-main)] mb-4 text-base">Meters Found</h4>
              <div className="space-y-3">
                {Object.entries(summary.line.match.chanda).map(([meter, count]) => (
                  <div key={meter} className="flex items-center justify-between p-4 bg-white rounded-xl border border-[var(--color-border-subtle)]">
                    <div>
                      <span className="text-[var(--color-text-main)] font-medium">{meter}</span>
                      <span className="text-sm text-[var(--color-text-muted)] ml-3">({getMeterEnglish(meter)})</span>
                    </div>
                    <span className="text-sm font-semibold text-white bg-[var(--color-primary)] px-3 py-1 rounded-full">
                      {count} line{count > 1 ? 's' : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Line Analysis Card Component
function LineAnalysisCard({ 
  lineItem, 
  showSanskrit 
}: { 
  lineItem: LineResult; 
  showSanskrit: boolean;
}) {
  const result = lineItem.result || {};
  const syllables = result.display_syllables || [];
  const lgArray = result.display_lg || [];
  const ganaString = result.display_gana || '';

  // Filter out syllables with empty L/G marks
  const validPairs: { syllable: string; lg: string }[] = [];
  syllables.forEach((syl, idx) => {
    if (lgArray[idx] && lgArray[idx].trim() !== '') {
      validPairs.push({ syllable: syl, lg: lgArray[idx] });
    }
  });

  // Get identified meter
  let meterDisplay = 'No match found';

  if (result.display_chanda_primary && result.display_chanda_primary.trim()) {
    const primaryMeters = result.display_chanda_primary.split('|').map(m => m.trim());
    const firstMeter = primaryMeters[0];
    const meterMatch = firstMeter.match(/^(.+?)\s*\[[\d.]+\]$/);
    meterDisplay = meterMatch ? meterMatch[1].trim() : firstMeter;
  } else if (result.found && result.display_chanda) {
    const meters = result.display_chanda.split('/').map(m => m.trim());
    meterDisplay = meters[0];
  } else if (result.fuzzy && result.fuzzy.length > 0) {
    const firstFuzzy = result.fuzzy[0];
    meterDisplay = firstFuzzy.display_chanda || '-';
  }

  return (
    <div className="p-8 bg-white rounded-2xl border-2 border-gray-300 shadow-md" style={{ minWidth: '100%' }}>
      {/* Analysis Table */}
      {validPairs.length > 0 && (
        <div className="overflow-x-auto mb-6">
          <table className="w-full border-collapse text-center shadow-md" style={{ minWidth: '100%', fontSize: '1.25rem' }}>
            <thead>
              <tr>
                <th className="border-2 border-gray-300 px-6 py-5 text-left font-bold text-gray-800 bg-gray-200 whitespace-nowrap min-w-[160px]" style={{ borderRight: '3px solid #6b7280', fontSize: '1.25rem' }}>
                  Akṣarāṇi
                </th>
                {validPairs.map((pair, idx) => (
                  <th key={idx} className="border-2 border-gray-300 px-6 py-5 font-bold bg-orange-400 text-gray-900" style={{ fontSize: '1.25rem', fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
                    {showSanskrit ? pair.syllable : transliterateToIAST(pair.syllable)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* L/G Row */}
              <tr>
                <td className="border-2 border-gray-300 px-6 py-5 text-left font-bold text-gray-800 bg-gray-200 whitespace-nowrap" style={{ borderRight: '3px solid #6b7280', fontSize: '1.25rem' }}>
                  Laghu-Guru
                </td>
                {validPairs.map((pair, idx) => {
                  const isLaghu = pair.lg === 'ल' || pair.lg === 'L';
                  const sanskritLG = (pair.lg === 'ग' || pair.lg === 'G') ? 'ग' : 'ल';
                  const englishLG = (pair.lg === 'ग' || pair.lg === 'G') ? 'G' : 'L';
                  return (
                    <td 
                      key={idx} 
                      className={`border-2 border-gray-300 px-6 py-5 font-bold ${
                        isLaghu 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-amber-100 text-amber-800'
                      }`}
                      style={{ fontSize: '1.25rem', fontFamily: "'Noto Sans Devanagari', monospace" }}
                    >
                      {showSanskrit ? sanskritLG : englishLG}
                    </td>
                  );
                })}
              </tr>

              {/* Gana Row */}
              {ganaString && (
                <tr>
                  <td className="border-2 border-gray-300 px-6 py-5 text-left font-bold text-gray-800 bg-gray-200 whitespace-nowrap" style={{ borderRight: '3px solid #6b7280', fontSize: '1.25rem' }}>
                    Gaṇa
                  </td>
                  {(() => {
                    const ganaChars = Array.from(ganaString);
                    const cells: JSX.Element[] = [];
                    let cellsUsed = 0;

                    ganaChars.forEach((ganaChar, gIdx) => {
                      if (cellsUsed < validPairs.length) {
                        const spanCount = Math.min(3, validPairs.length - cellsUsed);
                        const englishGana = GANA_MAP[ganaChar] || ganaChar;
                        cells.push(
                          <td 
                            key={gIdx}
                            colSpan={spanCount}
                            className="border-2 border-gray-300 px-6 py-5 bg-green-100 text-green-800 font-bold"
                            style={{ fontSize: '1.25rem', fontFamily: "'Noto Sans Devanagari', sans-serif" }}
                          >
                            {showSanskrit ? ganaChar : englishGana}
                          </td>
                        );
                        cellsUsed += spanCount;
                      }
                    });

                    // Fill remaining
                    if (cellsUsed < validPairs.length) {
                      cells.push(
                        <td 
                          key="remaining"
                          colSpan={validPairs.length - cellsUsed}
                          className="border-2 border-gray-300 px-6 py-5 bg-white"
                        />
                      );
                    }

                    return cells;
                  })()}
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Meter Result */}
      <div className="pt-5 mt-5 border-t-2 border-gray-300">
        <span className="font-bold text-orange-600" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif", fontSize: '1.5rem' }}>
          {meterDisplay}
        </span>
      </div>
    </div>
  );
}

export function ResultsDisplay({ result, type, onClose }: ResultsDisplayProps) {
  const [showSanskrit, setShowSanskrit] = useState(false);
  const [meterLanguage, setMeterLanguage] = useState<'devanagari' | 'english'>('devanagari');

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

  return (
    <div className="mt-10 animate-fadeIn" style={{ width: '100%', maxWidth: '100%' }}>
      <div className="bg-white border-2 border-gray-300 rounded-3xl p-12 shadow-lg" style={{ width: '100%', maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div className="flex items-center justify-between mb-10 pb-8 border-b-2 border-gray-200 bg-gray-50 -mx-12 -mt-12 px-12 pt-12 rounded-t-3xl">
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

        {/* Meters Identified Section */}
        {sortedMeters.length > 0 && (
          <div className="mb-8 bg-gray-50 p-8 rounded-2xl border-2 border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-bold text-gray-800 text-xl">Meters Identified</h3>
              <button
                onClick={() => setMeterLanguage(prev => prev === 'devanagari' ? 'english' : 'devanagari')}
                className="language-toggle-btn"
              >
                {meterLanguage === 'devanagari' ? 'Show English' : 'Show Sanskrit'}
              </button>
            </div>
            <div className="flex flex-wrap gap-4">
              {sortedMeters.map(([meter, count]) => {
                const iast = getMeterEnglish(meter);
                return (
                  <div
                    key={meter}
                    className="flex items-center gap-3 px-5 py-3 bg-white border-2 border-gray-200 rounded-xl shadow-sm"
                  >
                    <span className="font-bold text-gray-800" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif", fontSize: '1.125rem' }}>
                      {meterLanguage === 'devanagari' ? meter : iast}
                    </span>
                    <span className="text-sm text-gray-700 bg-gray-100 px-3 py-1.5 rounded-lg font-semibold border border-gray-300">
                      {count} line{count > 1 ? 's' : ''}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Summary Section */}
        {result.summary && <SummarySection summary={result.summary} />}

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

        {/* IMPORTANT: Show Verse Meter (Primary Result) FIRST when available */}
        {/* This is crucial for Vedic meters (Gāyatrī, Triṣṭubh, etc.) */}
        {verseResults.length > 0 && (
          <div className="mb-8 p-8 rounded-2xl border-3 border-orange-500 shadow-lg" style={{ background: 'linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)' }}>
            <h4 className="text-xl font-bold text-orange-700 mb-6 flex items-center gap-2">
              🕉️ Verse Meter (Primary Result)
            </h4>
            {verseResults.map((verse, vIndex) => (
              <div key={vIndex} className="bg-white rounded-xl p-6 mb-4 shadow-md">
                {verse.chanda && verse.chanda[0] && (() => {
                  const meterNames = verse.chanda[0];
                  const score = verse.chanda[1];
                  const primaryMeter = meterNames[0];
                  const englishName = getMeterEnglish(primaryMeter);
                  
                  // Calculate confidence as percentage
                  const numLines = lineResults.length || 1;
                  const scorePerLine = score / Math.max(numLines, 1);
                  const confidencePercent = Math.min(100, Math.round((scorePerLine / 2.0) * 100));
                  
                  let confidenceClass = 'bg-green-600';
                  if (confidencePercent < 50) {
                    confidenceClass = 'bg-red-500';
                  } else if (confidencePercent < 80) {
                    confidenceClass = 'bg-amber-500';
                  }

                  return (
                    <>
                      <div className="flex items-center gap-4 flex-wrap">
                        <span className="text-3xl font-bold text-orange-700" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
                          {primaryMeter}
                        </span>
                        {englishName && englishName !== primaryMeter && (
                          <span className="text-xl text-gray-600 italic">({englishName})</span>
                        )}
                        <span className={`${confidenceClass} text-white px-4 py-1.5 rounded-full text-sm font-semibold`}>
                          {confidencePercent}% Match
                        </span>
                      </div>
                      {meterNames.length > 1 && (
                        <div className="mt-3 text-gray-600">
                          <small>Alternates: {meterNames.slice(1).join(', ')}</small>
                        </div>
                      )}
                    </>
                  );
                })()}
              </div>
            ))}
            <p className="mt-4 p-4 bg-white/70 rounded-xl text-gray-600 text-sm border-l-4 border-orange-500 text-center">
              <em>Note: For Vedic meters (Gāyatrī, Triṣṭubh, Jagatī, etc.), the verse-level identification is the primary result. Line-by-line patterns below show individual pāda analysis.</em>
            </p>
          </div>
        )}

        {/* Line-by-Line Analysis (secondary when verse results exist) */}
        {lineResults.length > 0 && (
          verseResults.length > 0 ? (
            <details className="mt-6">
              <summary className="cursor-pointer font-semibold text-gray-700 p-4 bg-gray-100 rounded-xl mb-4 hover:bg-gray-200 transition-colors">
                Line-by-Line Analysis (Pāda Details)
              </summary>
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
                  {lineResults.map((lineItem, index) => (
                    <LineAnalysisCard
                      key={index}
                      lineItem={lineItem}
                      showSanskrit={showSanskrit}
                    />
                  ))}
                </div>
              </div>
            </details>
          ) : (
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
                {lineResults.map((lineItem, index) => (
                  <LineAnalysisCard
                    key={index}
                    lineItem={lineItem}
                    showSanskrit={showSanskrit}
                  />
                ))}
              </div>
            </div>
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
