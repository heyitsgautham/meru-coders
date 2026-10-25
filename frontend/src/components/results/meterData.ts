/**
 * Meter name, gaṇa and pada tables plus the lookup helpers ResultsDisplay uses.
 */

import type { LineResult } from '../../types/api';

// Meter name mappings for English transliteration
export const METER_MAP: Record<string, string> = {
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
export const DEVA_TO_IAST: Record<string, string> = {
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
export const GANA_MAP: Record<string, string> = {
  'य': 'Y', 'र': 'R', 'त': 'T', 'न': 'N',
  'भ': 'B', 'ज': 'J', 'स': 'S', 'म': 'M',
  'ल': 'L', 'ग': 'G'
};

// Educational information about each gaṇa (prosodic foot)
// Each gaṇa represents a specific L-G pattern of 3 syllables
export const GANA_INFO: Record<string, { pattern: string; meaning: string; mnemonic: string; description: string }> = {
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
export function transliterateToIAST(text: string): string {
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
export function getMeterEnglish(meterName: string): string {
  return METER_MAP[meterName] || transliterateToIAST(meterName);
}

// Extract top meter from a line result
export function extractTopMeter(lineItem: LineResult): string | null {
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
      const cleanMatch = meters[0].match(/^([^(]+)/);
      return cleanMatch ? cleanMatch[1].trim() : meters[0];
    }
  }

  return null;
}

// Build top meter counts from line results
export function buildMeterCounts(lineResults: LineResult[]): Record<string, number> {
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
export interface MeterStructureInfo {
  totalPadas: number;
  syllablesPerPada: number | string;
  totalSyllables: number;
  ganaPattern: string | null;
  structureNote?: string;
}

// Known meter structures
export const METER_STRUCTURES: Record<string, Partial<MeterStructureInfo>> = {
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
export function getMeterStructure(meterName: string, lineResults: LineResult[]): MeterStructureInfo | null {
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

// Pada sizes for known meters (syllables per pada)
export const METER_PADA_SIZES: Record<string, number> = {
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
export function getPadaSize(meterName: string): number {
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
export function splitIntoPadas<T>(arr: T[], padaSize: number): T[][] {
  const padas: T[][] = [];
  for (let i = 0; i < arr.length; i += padaSize) {
    padas.push(arr.slice(i, i + padaSize));
  }
  return padas;
}
