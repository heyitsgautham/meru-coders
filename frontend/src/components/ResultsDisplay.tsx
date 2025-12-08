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
  compact?: boolean; // When true, hides ShlokaOverview for side-by-side layout (split view)
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
  // Calculate actual syllable counts from line results
  if (lineResults.length > 0) {
    const firstResult = lineResults[0].result;

    // Count only VALID syllables (those with L-G marks)
    const firstSyllables = firstResult?.display_syllables || [];
    const firstLgArray = firstResult?.display_lg || [];
    const validFirstSyllables = firstSyllables.filter((_, idx: number) =>
      firstLgArray[idx] && firstLgArray[idx].trim() !== ''
    ).length;

    const ganaPattern = firstResult?.display_gana || null;

    // Calculate actual total syllables from all lines (only valid syllables)
    let actualTotalSyllables = 0;
    lineResults.forEach(line => {
      const syllables = line.result?.display_syllables || [];
      const lgArray = line.result?.display_lg || [];
      // Count only syllables that have corresponding L-G marks
      const validCount = syllables.filter((_: string, idx: number) =>
        lgArray[idx] && lgArray[idx].trim() !== ''
      ).length;
      actualTotalSyllables += validCount;
    });

    // Check if we have predefined structure for this meter
    const knownStructure = METER_STRUCTURES[meterName];

    // If we have a known meter structure, use it to calculate proper pada breakdown
    // This ensures correct display like "28 (7×4)" instead of "28 (28×1)"
    if (knownStructure && knownStructure.totalSyllables && knownStructure.syllablesPerPada && knownStructure.totalPadas) {
      // Use known structure for the format, but show actual total syllables counted
      return {
        totalPadas: knownStructure.totalPadas,
        syllablesPerPada: knownStructure.syllablesPerPada,
        totalSyllables: actualTotalSyllables,
        ganaPattern,
        structureNote: knownStructure.structureNote,
      };
    }

    // For unknown meters, try to infer structure from actual data
    // If input is a single line, try to detect proper pada structure based on total syllables
    if (lineResults.length === 1 && actualTotalSyllables > 0) {
      // Common Vedic meter structures by total syllable count
      const SYLLABLE_STRUCTURES: Record<number, { padas: number; perPada: number }> = {
        24: { padas: 3, perPada: 8 },   // Gayatri: 3×8
        28: { padas: 4, perPada: 7 },   // Ushnik: 4×7
        32: { padas: 4, perPada: 8 },   // Anushtubh: 4×8
        36: { padas: 4, perPada: 9 },   // Brihati: 4×9
        40: { padas: 5, perPada: 8 },   // Pankti: 5×8
        44: { padas: 4, perPada: 11 },  // Trishtubh: 4×11
        48: { padas: 4, perPada: 12 },  // Jagati: 4×12
        56: { padas: 4, perPada: 14 },  // Vasantatilaka: 4×14
        68: { padas: 4, perPada: 17 },  // Mandakranta: 4×17
        76: { padas: 4, perPada: 19 },  // Shardula: 4×19
        84: { padas: 4, perPada: 21 },  // Sragdhara: 4×21
      };

      const inferredStructure = SYLLABLE_STRUCTURES[actualTotalSyllables];
      if (inferredStructure) {
        return {
          totalPadas: inferredStructure.padas,
          syllablesPerPada: inferredStructure.perPada,
          totalSyllables: actualTotalSyllables,
          ganaPattern,
          structureNote: knownStructure?.structureNote,
        };
      }
    }

    // Fallback: use actual data as-is
    return {
      totalPadas: lineResults.length,  // Actual number of lines/padas
      syllablesPerPada: validFirstSyllables,  // Valid syllables per pada from first line
      totalSyllables: actualTotalSyllables,  // Total valid syllables from all lines
      ganaPattern,
      structureNote: knownStructure?.structureNote,
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

// Shloka Overview Component - Shows colored syllables at a glance
// Blue = Laghu (ल/L), Red/Pink = Guru (ग/G)
function ShlokaOverview({ lineResults }: { lineResults: LineResult[] }) {
  if (!lineResults || lineResults.length === 0) return null;

  return (
    <div className="mb-8 bg-[#FDF6E3] rounded-2xl p-10 shadow-sm border border-[#E8DCC8] overflow-hidden">
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <h3 className="text-2xl font-bold text-gray-800">Shloka Overview</h3>
        <div className="flex items-center gap-8 text-base flex-wrap">
          <div className="flex items-center gap-2">
            <span 
              className="inline-block w-6 h-6 rounded" 
              style={{ backgroundColor: '#A8D4F0' }}
            />
            <span className="text-gray-700 font-medium">Laghu (ल) - Short</span>
          </div>
          <div className="flex items-center gap-2">
            <span 
              className="inline-block w-6 h-6 rounded" 
              style={{ backgroundColor: '#F5B7B1' }}
            />
            <span className="text-gray-700 font-medium">Guru (ग) - Long</span>
          </div>
        </div>
      </div>
      
      <div className="flex flex-col items-center space-y-6 w-full">
        {lineResults.map((lineItem, lineIndex) => {
          const result = lineItem.result || {};
          const syllables = result.display_syllables || [];
          const lgArray = result.display_lg || [];
          const originalLine = lineItem.line || '';

          // Build syllable-to-word mapping
          const validPairs: { syllable: string; lg: string; isWordEnd: boolean }[] = [];
          
          // Split original line into words (space-separated)
          const words = originalLine.split(/\s+/).filter((w: string) => w.trim());
          
          // Match syllables to words by accumulating syllable text
          let wordIdx = 0;
          let accumulated = '';
          
          syllables.forEach((syl: string, idx: number) => {
            if (lgArray[idx] && lgArray[idx].trim() !== '') {
              accumulated += syl;
              
              // Check if current word is complete
              let isWordEnd = false;
              if (wordIdx < words.length) {
                const currentWord = words[wordIdx];
                // Remove any diacritics/marks for comparison and normalize
                const normalizedWord = currentWord.replace(/[\s।॥]/g, '');
                const normalizedAccum = accumulated.replace(/[\s।॥]/g, '');
                
                // Word ends when accumulated syllables match or exceed word length
                if (normalizedAccum.length >= normalizedWord.length) {
                  isWordEnd = true;
                  wordIdx++;
                  accumulated = '';
                }
              }
              
              validPairs.push({ syllable: syl, lg: lgArray[idx], isWordEnd });
            }
          });

          if (validPairs.length === 0) return null;

          return (
            <div 
              key={lineIndex} 
              className="w-full"
              style={{
                fontFamily: "'Noto Sans Devanagari', 'Siddhanta', sans-serif",
                fontSize: '2.25rem',
                lineHeight: '2.8',
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                alignItems: 'center',
                maxWidth: '100%',
                gap: '4px 2px'
              }}
            >
              {validPairs.map((pair, idx) => {
                const isLaghu = pair.lg === 'ल' || pair.lg === 'L';
                // Use actual word boundary detection instead of arbitrary grouping
                const addWordGap = pair.isWordEnd && idx < validPairs.length - 1;
                
                return (
                  <span
                    key={idx}
                    style={{
                      backgroundColor: isLaghu ? '#A8D4F0' : '#F5B7B1',
                      color: '#2D2D2D',
                      fontWeight: 500,
                      borderRadius: '6px',
                      marginRight: addWordGap ? '40px' : '0',
                      padding: '8px 12px',
                      minWidth: '2.5rem',
                      textAlign: 'center',
                      flexShrink: 0
                    }}
                    title={isLaghu ? 'Laghu (Short syllable)' : 'Guru (Long syllable)'}
                  >
                    {pair.syllable}
                  </span>
                );
              })}
              {/* Add a visual separator between lines */}
              {lineIndex < lineResults.length - 1 && (
                <span style={{ color: '#8B7355', fontSize: '2rem', marginLeft: '8px', flexShrink: 0 }}>।</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
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
              const numLines = lineResults.length || 1;
              const scorePerLine = primaryScore / Math.max(numLines, 1);
              const confidencePercent = Math.min(100, Math.round(scorePerLine * 100));

              let confidenceLabel = 'High';
              let confidenceColor = '#16A34A'; // green-600
              if (confidencePercent < 50) {
                confidenceLabel = 'Low';
                confidenceColor = '#EF4444'; // red-500
              } else if (confidencePercent < 80) {
                confidenceLabel = 'Medium';
                confidenceColor = '#F59E0B'; // amber-500
              }

              // Get meter structure info
              const meterStructure = getMeterStructure(primaryMeter, lineResults);

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
                  <div className="flex gap-6">
                    <div className="flex-1 bg-white rounded-2xl p-5 border border-gray-300">
                      <div className="text-sm font-medium text-gray-500 mb-2">Syllables</div>
                      <div className="text-3xl font-bold text-gray-900">
                        {meterStructure ? `${meterStructure.totalSyllables} (${meterStructure.syllablesPerPada}×${meterStructure.totalPadas})` : '-'}
                      </div>
                    </div>
                    <div className="flex-1 bg-white rounded-2xl p-5 border border-gray-300">
                      <div className="text-sm font-medium text-gray-500 mb-2">Confidence</div>
                      <div className="text-3xl font-bold" style={{ color: confidenceColor }}>
                        {confidenceLabel}
                      </div>
                    </div>
                  </div>
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
                      const confidencePercent = Math.round((lineCount / totalLines) * 100);

                      let confidenceLabel = 'High';
                      let confidenceColor = '#16A34A'; // green-600
                      if (confidencePercent < 50) {
                        confidenceLabel = 'Low';
                        confidenceColor = '#EF4444'; // red-500
                      } else if (confidencePercent < 80) {
                        confidenceLabel = 'Medium';
                        confidenceColor = '#F59E0B'; // amber-500
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
                          <div className="flex gap-6">
                            <div className="flex-1 bg-white rounded-2xl p-5 border border-gray-300">
                              <div className="text-sm font-medium text-gray-500 mb-2">Syllables</div>
                              <div className="text-3xl font-bold text-gray-900">
                                {meterStructure ? `${meterStructure.totalSyllables} (${meterStructure.syllablesPerPada}×${meterStructure.totalPadas})` : '-'}
                              </div>
                            </div>
                            <div className="flex-1 bg-white rounded-2xl p-5 border border-gray-300">
                              <div className="text-sm font-medium text-gray-500 mb-2">Confidence</div>
                              <div className="text-3xl font-bold" style={{ color: confidenceColor }}>
                                {confidenceLabel}
                              </div>
                            </div>
                          </div>
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
