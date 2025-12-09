/**
 * Sanskrit Number Conversion Utility
 * Converts numbers to Sanskrit words for TTS narration
 */

const SANSKRIT_NUMBERS: Record<number, string> = {
  0: 'शून्य',
  1: 'एक',
  2: 'द्वे',
  3: 'त्रीणि',
  4: 'चत्वारि',
  5: 'पञ्च',
  6: 'षट्',
  7: 'सप्त',
  8: 'अष्ट',
  9: 'नव',
  10: 'दश',
  11: 'एकादश',
  12: 'द्वादश',
  13: 'त्रयोदश',
  14: 'चतुर्दश',
  15: 'पञ्चदश',
  16: 'षोडश',
  17: 'सप्तदश',
  18: 'अष्टादश',
  19: 'नवदश',
  20: 'विंशति',
  21: 'एकविंशति',
  22: 'द्वाविंशति',
  24: 'चतुर्विंशति',
  28: 'अष्टाविंशति',
  30: 'त्रिंशत्',
  32: 'द्वात्रिंशत्',
  36: 'षट्त्रिंशत्',
  40: 'चत्वारिंशत्',
  44: 'चतुश्चत्वारिंशत्',
  48: 'अष्टचत्वारिंशत्',
  50: 'पञ्चाशत्',
  60: 'षष्टि',
  70: 'सप्तति',
  80: 'अशीति',
  90: 'नवति',
  100: 'शतम्',
};

/**
 * Convert a number to Sanskrit word
 * @param num - Number to convert
 * @returns Sanskrit word representation
 */
export function numberToSanskrit(num: number): string {
  // Direct lookup for known numbers
  if (SANSKRIT_NUMBERS[num]) {
    return SANSKRIT_NUMBERS[num];
  }

  // For numbers not in dictionary, fallback to English numeral
  return num.toString();
}

/**
 * Format gana pattern for speech (with hyphens between letters)
 * @param gana - Gana pattern string (e.g., "RJSMRJSM")
 * @returns Formatted gana for speech (e.g., "र-ज-स-म-र-ज-स-म")
 */
export function formatGanaForSpeech(gana: string): string {
  if (!gana) return '';
  
  // Map English gana letters to Devanagari
  const ganaMap: Record<string, string> = {
    'Y': 'य',
    'R': 'र',
    'T': 'त',
    'N': 'न',
    'B': 'भ',
    'J': 'ज',
    'S': 'स',
    'M': 'म',
  };

  // Convert and join with hyphens
  return gana
    .toUpperCase()
    .split('')
    .map(letter => ganaMap[letter] || letter)
    .join('-');
}

/**
 * Generate Pingala Acharya's spoken explanation for identified chandas
 * @param meterName - Name of the meter (Devanagari)
 * @returns Sanskrit explanation text
 */
export function generatePingalaScript(
  meterName: string
): string {
  const lines: string[] = [];

  // Simple greeting and meter identification only
  lines.push(`नमस्ते। अहं पिङ्गलाचार्यः।`);
  lines.push(`अयं छन्दः ${meterName} अस्ति।`);

  return lines.join(' ');
}
