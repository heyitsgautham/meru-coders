/**
 * ResultsDisplay Component
 * Displays meter identification results with language toggle
 */

import { useState } from 'react';
import { Download, ChevronDown, ChevronUp, FileText, AlertCircle, X } from 'lucide-react';
import { getDownloadURL } from '../services/api';
import type { IdentifyResponse, LineResult, Summary } from '../types/api';
import { TextToSpeech } from './TextToSpeech';

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

// Educational information about each gaṇa (prosodic foot)
// Each gaṇa represents a specific L-G pattern of 3 syllables
const GANA_INFO: Record<string, { pattern: string; meaning: string; mnemonic: string; description: string }> = {
  'य': {
    pattern: 'LGG',
    meaning: 'Yagaṇa (यगण)',
    mnemonic: 'यमाता (ya-mā-tā)',
    description: 'Light-Heavy-Heavy pattern. First syllable is laghu (short), followed by two guru (long) syllables. Common in meters like Indravajrā.'
  },
  'र': {
    pattern: 'GLG',
    meaning: 'Ragaṇa (रगण)',
    mnemonic: 'राजभा (rā-ja-bhā)',
    description: 'Heavy-Light-Heavy pattern. Heavy syllable, followed by light, then heavy. Creates a galloping rhythm.'
  },
  'त': {
    pattern: 'GGL',
    meaning: 'Tagaṇa (तगण)',
    mnemonic: 'ताराज (tā-rā-ja)',
    description: 'Heavy-Heavy-Light pattern. Two heavy syllables followed by a light one. Often used at the end of pādas.'
  },
  'न': {
    pattern: 'LLL',
    meaning: 'Nagaṇa (नगण)',
    mnemonic: 'नभसा (na-bha-sā)',
    description: 'Light-Light-Light pattern. Three short syllables creating a rapid, light rhythm. Gives swift movement to verses.'
  },
  'भ': {
    pattern: 'GLL',
    meaning: 'Bhagaṇa (भगण)',
    mnemonic: 'भानुस (bhā-nu-sa)',
    description: 'Heavy-Light-Light pattern. Heavy syllable followed by two light ones. Creates a "falling" rhythmic pattern.'
  },
  'ज': {
    pattern: 'LGL',
    meaning: 'Jagaṇa (जगण)',
    mnemonic: 'जभान (ja-bhā-na)',
    description: 'Light-Heavy-Light pattern. Light syllable encased by heavy ones. Traditionally considered inauspicious to start a verse with.'
  },
  'स': {
    pattern: 'LLG',
    meaning: 'Sagaṇa (सगण)',
    mnemonic: 'सलगा (sa-la-gā)',
    description: 'Light-Light-Heavy pattern. Two light syllables followed by a heavy one. Creates a "rising" rhythmic pattern.'
  },
  'म': {
    pattern: 'GGG',
    meaning: 'Magaṇa (मगण)',
    mnemonic: 'मातारा (mā-tā-rā)',
    description: 'Heavy-Heavy-Heavy pattern. Three heavy syllables creating the most weighty and solemn rhythm. Common in stately meters.'
  },
  // Single syllable markers
  'ल': {
    pattern: 'L',
    meaning: 'Laghu (लघु)',
    mnemonic: 'Short syllable',
    description: 'A single short/light syllable. Has 1 mātrā (mora). Ends in a short vowel without following consonant cluster.'
  },
  'ग': {
    pattern: 'G',
    meaning: 'Guru (गुरु)',
    mnemonic: 'Long syllable',
    description: 'A single long/heavy syllable. Has 2 mātrās (morae). Has a long vowel, diphthong, or short vowel followed by conjunct consonants.'
  }
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

// Meter structure information
interface MeterStructureInfo {
  totalPadas: number;
  syllablesPerPada: number | string;
  totalSyllables: number;
  ganaPattern: string | null;
  structureNote?: string;
}

// Known meter structures
const METER_STRUCTURES: Record<string, Partial<MeterStructureInfo>> = {
  'अनुष्टुभ्': { totalPadas: 4, syllablesPerPada: 8, totalSyllables: 32, structureNote: '4×8 syllables (Śloka meter)' },
  'गायत्री': { totalPadas: 3, syllablesPerPada: 8, totalSyllables: 24, structureNote: '3×8 syllables (Vedic)' },
  'त्रिष्टुभ्': { totalPadas: 4, syllablesPerPada: 11, totalSyllables: 44, structureNote: '4×11 syllables (Vedic)' },
  'जगती': { totalPadas: 4, syllablesPerPada: 12, totalSyllables: 48, structureNote: '4×12 syllables (Vedic)' },
  'उष्णिक्': { totalPadas: 4, syllablesPerPada: 7, totalSyllables: 28, structureNote: '4×7 syllables' },
  'बृहती': { totalPadas: 4, syllablesPerPada: 9, totalSyllables: 36, structureNote: '4×9 syllables' },
  'पङ्क्ति': { totalPadas: 5, syllablesPerPada: 8, totalSyllables: 40, structureNote: '5×8 syllables' },
  'वसन्ततिलका': { totalPadas: 4, syllablesPerPada: 14, totalSyllables: 56, structureNote: '4×14 syllables' },
  'मन्दाक्रान्ता': { totalPadas: 4, syllablesPerPada: 17, totalSyllables: 68, structureNote: '4×17 syllables' },
  'शार्दूलविक्रीडित': { totalPadas: 4, syllablesPerPada: 19, totalSyllables: 76, structureNote: '4×19 syllables' },
  'स्रग्धरा': { totalPadas: 4, syllablesPerPada: 21, totalSyllables: 84, structureNote: '4×21 syllables' },
  'इन्द्रवज्रा': { totalPadas: 4, syllablesPerPada: 11, totalSyllables: 44, structureNote: '4×11 syllables' },
  'उपेन्द्रवज्रा': { totalPadas: 4, syllablesPerPada: 11, totalSyllables: 44, structureNote: '4×11 syllables' },
  'मालिनी': { totalPadas: 4, syllablesPerPada: 15, totalSyllables: 60, structureNote: '4×15 syllables' },
  'शालिनी': { totalPadas: 4, syllablesPerPada: 11, totalSyllables: 44, structureNote: '4×11 syllables' },
};

// Get meter structure information
function getMeterStructure(meterName: string, lineResults: LineResult[]): MeterStructureInfo | null {
  // Check if we have predefined structure
  const knownStructure = METER_STRUCTURES[meterName];

  if (knownStructure) {
    // Try to extract gana pattern from first line result
    let ganaPattern: string | null = null;
    if (lineResults.length > 0 && lineResults[0].result?.display_gana) {
      ganaPattern = lineResults[0].result.display_gana;
    }

    return {
      totalPadas: knownStructure.totalPadas || 4,
      syllablesPerPada: knownStructure.syllablesPerPada || '-',
      totalSyllables: knownStructure.totalSyllables || 0,
      ganaPattern,
      structureNote: knownStructure.structureNote,
    };
  }

  // Calculate from line results if no predefined structure
  if (lineResults.length > 0) {
    const firstResult = lineResults[0].result;
    const syllableCount = firstResult?.display_syllables?.length || 0;
    const ganaPattern = firstResult?.display_gana || null;

    return {
      totalPadas: lineResults.length,
      syllablesPerPada: syllableCount,
      totalSyllables: syllableCount * lineResults.length,
      ganaPattern,
    };
  }

  return null;
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

// Pada sizes for known meters (syllables per pada)
const METER_PADA_SIZES: Record<string, number> = {
  'अनुष्टुभ्': 8,
  'गायत्री': 8,
  'त्रिष्टुभ्': 11,
  'जगती': 12,
  'उष्णिक्': 7,
  'बृहती': 9,
  'पङ्क्ति': 8,
  'वसन्ततिलका': 14,
  'मन्दाक्रान्ता': 17,
  'शार्दूलविक्रीडित': 19,
  'स्रग्धरा': 21,
  'इन्द्रवज्रा': 11,
  'उपेन्द्रवज्रा': 11,
  'मालिनी': 15,
  'शालिनी': 11,
  'भुजङ्गप्रयात': 12,
};

// Get pada size from meter name
function getPadaSize(meterName: string): number {
  // Check known meters
  for (const [meter, size] of Object.entries(METER_PADA_SIZES)) {
    if (meterName.includes(meter)) {
      return size;
    }
  }
  // Default to 8 (most common)
  return 8;
}

// Split array into chunks of given size
function splitIntoPadas<T>(arr: T[], padaSize: number): T[][] {
  const padas: T[][] = [];
  for (let i = 0; i < arr.length; i += padaSize) {
    padas.push(arr.slice(i, i + padaSize));
  }
  return padas;
}

// Line Analysis Card Component
function LineAnalysisCard({
  lineItem,
  showSanskrit,
  padaOffset = 0
}: {
  lineItem: LineResult;
  showSanskrit: boolean;
  padaOffset?: number;
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
  let meterName = '';

  if (result.display_chanda_primary && result.display_chanda_primary.trim()) {
    const primaryMeters = result.display_chanda_primary.split('|').map(m => m.trim());
    const firstMeter = primaryMeters[0];
    const meterMatch = firstMeter.match(/^(.+?)\s*\[[\d.]+\]$/);
    meterDisplay = meterMatch ? meterMatch[1].trim() : firstMeter;
    // Extract just the meter name without pada info
    const nameMatch = meterDisplay.match(/^([^\s(]+)/);
    meterName = nameMatch ? nameMatch[1] : meterDisplay;
  } else if (result.found && result.display_chanda) {
    const meters = result.display_chanda.split('/').map(m => m.trim());
    meterDisplay = meters[0];
    const nameMatch = meterDisplay.match(/^([^\s(]+)/);
    meterName = nameMatch ? nameMatch[1] : meterDisplay;
  } else if (result.fuzzy && result.fuzzy.length > 0) {
    const firstFuzzy = result.fuzzy[0];
    meterDisplay = firstFuzzy.display_chanda || '-';
  }

  // Split syllables into padas based on meter
  const padaSize = getPadaSize(meterName);
  const padas = splitIntoPadas(validPairs, padaSize);

  // Split gana string into padas (each pada typically has ganas = padaSize / 3)
  const ganaChars = Array.from(ganaString);
  const ganasPerPada = Math.ceil(padaSize / 3);
  const ganaPadas = splitIntoPadas(ganaChars, ganasPerPada);

  return (
    <div className="p-8 rounded-2xl shadow-md" style={{ minWidth: '100%', backgroundColor: '#FFF9F2', border: '2px solid #E1B88E' }}>
      {/* Analysis Tables - One per Pada */}
      {padas.length > 0 && (
        <div className="space-y-4 mb-6">
          {padas.map((padaPairs, padaIndex) => (
            <div key={padaIndex} className="overflow-x-auto">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-semibold text-[#C68642] bg-[#FFE0BF] px-3 py-1 rounded-full">
                  पाद {padaOffset + padaIndex + 1}
                </span>
              </div>
              <table className="w-full border-collapse text-center shadow-md" style={{ fontSize: '1.25rem', border: '4px solid #C68642' }}>
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left font-bold" style={{ border: '2px solid #E1B88E', borderRight: '4px solid #C68642', fontSize: '1rem', backgroundColor: '#FFE0BF', color: '#3E2815', whiteSpace: 'nowrap', minWidth: '100px' }}>
                      Akṣarāṇi
                    </th>
                    {padaPairs.map((pair, idx) => {
                      const isGanaBoundary = (idx + 1) % 3 === 0 && idx < padaPairs.length - 1;
                      return (
                        <th key={idx} className="px-4 py-3 font-bold" style={{
                          border: '2px solid #E1B88E',
                          borderRight: isGanaBoundary ? '4px solid #C68642' : '2px solid #E1B88E',
                          fontSize: '1.1rem',
                          fontFamily: "'Noto Sans Devanagari', sans-serif",
                          backgroundColor: '#FFE0BF',
                          color: '#000000',
                          minWidth: '50px'
                        }}>
                          {showSanskrit ? pair.syllable : transliterateToIAST(pair.syllable)}
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {/* L/G Row */}
                  <tr>
                    <td className="px-4 py-3 text-left font-bold" style={{ border: '2px solid #E1B88E', borderRight: '4px solid #C68642', fontSize: '1rem', backgroundColor: '#FFE0BF', color: '#3E2815', whiteSpace: 'nowrap', minWidth: '100px' }}>
                      Laghu-Guru
                    </td>
                    {padaPairs.map((pair, idx) => {
                      const isLaghu = pair.lg === 'ल' || pair.lg === 'L';
                      const sanskritLG = (pair.lg === 'ग' || pair.lg === 'G') ? 'ग' : 'ल';
                      const englishLG = (pair.lg === 'ग' || pair.lg === 'G') ? 'G' : 'L';
                      const isGanaBoundary = (idx + 1) % 3 === 0 && idx < padaPairs.length - 1;
                      return (
                        <td
                          key={idx}
                          className="px-4 py-3 font-bold"
                          style={{
                            border: '2px solid #E1B88E',
                            borderRight: isGanaBoundary ? '4px solid #C68642' : '2px solid #E1B88E',
                            fontSize: '1.1rem',
                            fontFamily: "'Noto Sans Devanagari', monospace",
                            backgroundColor: isLaghu ? '#E8F4FD' : '#FFF9F2',
                            color: isLaghu ? '#2563EB' : '#C2185B',
                            minWidth: '50px'
                          }}
                        >
                          {showSanskrit ? sanskritLG : englishLG}
                        </td>
                      );
                    })}
                  </tr>

                  {/* Gana Row */}
                  {ganaPadas[padaIndex] && ganaPadas[padaIndex].length > 0 && (
                    <tr>
                      <td className="px-4 py-3 text-left font-bold" style={{ border: '2px solid #E1B88E', borderRight: '4px solid #C68642', fontSize: '1rem', backgroundColor: '#FFE0BF', color: '#3E2815', whiteSpace: 'nowrap', minWidth: '100px' }}>
                        Gaṇa
                      </td>
                      {(() => {
                        const padaGanas = ganaPadas[padaIndex] || [];
                        const cells: JSX.Element[] = [];
                        let cellsUsed = 0;

                        padaGanas.forEach((ganaChar, gIdx) => {
                          if (cellsUsed < padaPairs.length) {
                            const remainingSyllables = padaPairs.length - cellsUsed;
                            const spanCount = Math.min(3, remainingSyllables);
                            const englishGana = GANA_MAP[ganaChar] || ganaChar;
                            const isLastGana = cellsUsed + spanCount >= padaPairs.length;

                            // Get educational tooltip info
                            const ganaInfo = GANA_INFO[ganaChar];
                            const tooltipText = ganaInfo
                              ? `${ganaInfo.meaning}\nPattern: ${ganaInfo.pattern}\nMnemonic: ${ganaInfo.mnemonic}\n\n${ganaInfo.description}`
                              : '';

                            if (spanCount === 3) {
                              cells.push(
                                <td
                                  key={gIdx}
                                  colSpan={spanCount}
                                  className="px-4 py-3 font-bold cursor-help"
                                  title={tooltipText}
                                  style={{
                                    border: '2px solid #E1B88E',
                                    borderRight: !isLastGana ? '4px solid #C68642' : '2px solid #E1B88E',
                                    fontSize: '1.1rem',
                                    fontFamily: "'Noto Sans Devanagari', sans-serif",
                                    backgroundColor: '#E7F5E8',
                                    color: '#2D5A30'
                                  }}
                                >
                                  {showSanskrit ? ganaChar : englishGana}
                                </td>
                              );
                            } else {
                              cells.push(
                                <td
                                  key={gIdx}
                                  colSpan={spanCount}
                                  className="px-4 py-3"
                                  style={{
                                    border: '2px solid #E1B88E',
                                    backgroundColor: '#FFF9F2'
                                  }}
                                />
                              );
                            }
                            cellsUsed += spanCount;
                          }
                        });

                        if (cellsUsed < padaPairs.length) {
                          cells.push(
                            <td
                              key="remaining"
                              colSpan={padaPairs.length - cellsUsed}
                              style={{ border: '2px solid #E1B88E', backgroundColor: '#FFF9F2' }}
                              className="px-4 py-3"
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
          ))}
        </div>
      )}

      {/* Chanda Result */}
      <div className="pt-5 mt-5" style={{ borderTop: '2px solid #E1B88E' }}>
        <span className="font-bold" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif", fontSize: '1.5rem', color: '#3E2815' }}>
          Chanda - <span style={{ color: '#E57F1B' }}>{meterDisplay}</span>
        </span>
      </div>

      {/* Pattern Validation Display - Removed to avoid confusing users with technical details */}
    </div>
  );
}

export function ResultsDisplay({ result, type, onClose }: ResultsDisplayProps) {
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
  const firstValidationError = lineResults.find(line => line.result?.validation_error)?.result?.validation_error;

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
    <div className="mt-10 animate-fadeIn" style={{ width: '100%', maxWidth: '100%' }}>
      <div className="bg-white border-2 border-gray-300 rounded-3xl p-12 shadow-lg" style={{ width: '100%', maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div className="flex items-center justify-between pb-8 border-b-2 border-gray-200 bg-gray-50 -mx-12 -mt-12 px-12 pt-12 rounded-t-3xl">
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
          <div className="mb-8 p-8 rounded-2xl border-3 border-orange-500 shadow-lg" style={{ background: 'linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)' }}>
            <div className="flex items-center justify-between mb-6">
              <h4 className="text-xl font-bold text-orange-700 flex items-center gap-2">
                🕉️ Verse Meter (Primary Result)
              </h4>
              {/* Show detection mode indicator - shows effective mode when auto-detect is used */}
              {(() => {
                const requestedMode = result.input?.identification_mode || 'auto';
                const effectiveMode = result.result?.effective_mode;
                const isAutoDetect = requestedMode === 'auto';

                // Determine display mode
                const displayMode = effectiveMode || requestedMode;
                const modeLabel = displayMode === 'vedic' ? 'Vedic' : displayMode === 'classical' ? 'Classical' : 'Auto-detect';

                // Style based on effective mode
                const modeStyle = displayMode === 'vedic'
                  ? 'bg-purple-100 text-purple-700 border border-purple-300'
                  : displayMode === 'classical'
                    ? 'bg-blue-100 text-blue-700 border border-blue-300'
                    : 'bg-gray-100 text-gray-700 border border-gray-300';

                return (
                  <span className={`px-3 py-1.5 rounded-full text-xs font-semibold ${modeStyle}`}>
                    {isAutoDetect && effectiveMode
                      ? `Auto → ${modeLabel}`
                      : `Mode: ${modeLabel}`}
                  </span>
                );
              })()}
            </div>
            {/* Consolidate all verse results into a single display */}
            {(() => {
              // Aggregate all verse results - combine scores for same meters
              const meterScores: Record<string, number> = {};
              let totalScore = 0;

              verseResults.forEach(verse => {
                if (verse.chanda && Array.isArray(verse.chanda[0])) {
                  const meterName = verse.chanda[0][0];
                  const score = verse.chanda[1] || 0;
                  meterScores[meterName] = (meterScores[meterName] || 0) + score;
                  totalScore += score;
                }
              });

              // Get unique meters sorted by score
              const sortedMeters = Object.entries(meterScores)
                .sort((a, b) => b[1] - a[1]);

              if (sortedMeters.length === 0) return null;

              const primaryMeter = sortedMeters[0][0];
              const primaryScore = sortedMeters[0][1];
              const englishName = getMeterEnglish(primaryMeter);

              // Calculate confidence based on total score vs total lines
              // Backend normalizes exact match scores to ~1.0 per line
              // A perfect match gives score 1.0 per line, boosts can increase it
              const numLines = lineResults.length || 1;
              const scorePerLine = primaryScore / Math.max(numLines, 1);
              // Score of 1.0 per line = 100% confidence (exact match)
              // Scale: 0.0 = 0%, 1.0+ = 100%
              const confidencePercent = Math.min(100, Math.round(scorePerLine * 100));

              let confidenceClass = 'bg-green-600';
              if (confidencePercent < 50) {
                confidenceClass = 'bg-red-500';
              } else if (confidencePercent < 80) {
                confidenceClass = 'bg-amber-500';
              }

              // Get meter structure info
              const meterStructure = getMeterStructure(primaryMeter, lineResults);

              return (
                <div className="bg-white rounded-xl p-6 shadow-md">
                  <div className="flex items-center gap-4 flex-wrap mb-4">
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

                  {/* Meter Structure Info */}
                  {meterStructure && (
                    <div className="mt-4 p-4 bg-orange-50 rounded-lg border border-orange-200">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-orange-700">{meterStructure.totalPadas}</div>
                          <div className="text-gray-600">Pādas</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-orange-700">{meterStructure.syllablesPerPada}</div>
                          <div className="text-gray-600">Syllables/Pāda</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-orange-700">{meterStructure.totalSyllables}</div>
                          <div className="text-gray-600">Total Syllables</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-orange-700">{meterStructure.ganaPattern || '-'}</div>
                          <div className="text-gray-600">Gaṇa Pattern</div>
                        </div>
                      </div>
                      {meterStructure.structureNote && (
                        <div className="mt-3 text-center text-gray-600 text-xs">
                          {meterStructure.structureNote}
                        </div>
                      )}
                    </div>
                  )}

                  {sortedMeters.length > 1 && (
                    <div className="mt-4 text-gray-600">
                      <small>Alternates: {sortedMeters.slice(1).map(m => m[0]).join(', ')}</small>
                    </div>
                  )}
                </div>
              );
            })()}
            <p className="mt-4 p-4 bg-white/70 rounded-xl text-gray-600 text-sm border-l-4 border-orange-500 text-center">
              <em>Note: For Vedic meters (Gāyatrī, Triṣṭubh, Jagatī, etc.), the verse-level identification is the primary result. Line-by-line patterns below show individual pāda analysis.</em>
            </p>
          </div>
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
              {/* Identified Chanda - Single div at top for line-by-line mode */}
              {sortedMeters.length > 0 && (
                <div className="mb-8 p-8 rounded-2xl border-2 border-orange-300" style={{ background: '#FFF6EA' }}>
                  <h4 className="text-xl font-bold text-orange-700 mb-6 flex items-center gap-2">
                    🕉️ Identified Chanda
                  </h4>
                  <div className="rounded-xl p-6 border-2 border-orange-300" style={{ background: '#FFF6EA' }}>
                    {(() => {
                      const primaryMeter = sortedMeters[0][0];
                      const lineCount = sortedMeters[0][1];
                      const englishName = getMeterEnglish(primaryMeter);
                      const totalLines = lineResults.length;
                      const confidencePercent = Math.round((lineCount / totalLines) * 100);

                      return (
                        <div className="flex items-center gap-4 flex-wrap">
                          <span className="text-3xl font-bold text-orange-700" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
                            {primaryMeter}
                          </span>
                          {englishName && englishName !== primaryMeter && (
                            <span className="text-xl text-gray-600 italic">({englishName})</span>
                          )}
                          <span className="px-5 py-2 rounded-full text-sm font-semibold" style={{ backgroundColor: '#f97316', color: '#ffffff' }}>
                            {confidencePercent}% Match
                          </span>
                        </div>
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
