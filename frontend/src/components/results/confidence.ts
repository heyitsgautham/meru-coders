import type { ConfidenceReason, IdentifyResponse, LineResult, VerseResult } from '../../types/api';
import { getPadaSize } from './meterData';
import type { MeterStructureInfo } from './meterData';

export interface ConfidenceDisplay {
  label: string;
  color: string;
  /** 0 to 10 */
  score: number;
  /** Sentences explaining the score; empty when the backend sent no reason. */
  reason: string;
}

const LEVELS: Record<ConfidenceReason['level'], { label: string; color: string }> = {
  very_high: { label: 'Very High', color: '#16A34A' }, // green-600
  high: { label: 'High', color: '#22C55E' }, // green-500
  medium: { label: 'Medium', color: '#F59E0B' }, // amber-500
  low: { label: 'Low', color: '#F97316' }, // orange-500
  very_low: { label: 'Very Low', color: '#EF4444' }, // red-500
};

/**
 * The confidence shown for the winning meter.
 *
 * With the backend's primary_confidence_reason, its level and text are used, and in a
 * multi-line verse the per-line syllable count in the text is replaced by the verse total,
 * so an Uṣṇik reads "28 syllables", not "14 syllables". Without it, `fallbackPercent`
 * decides: below 50 is Low, below 80 Medium, otherwise High.
 */
export function describeConfidence(
  lineResults: LineResult[],
  meterStructure: MeterStructureInfo | null,
  fallbackPercent: () => number,
): ConfidenceDisplay {
  const confidenceReason = lineResults[0]?.result?.primary_confidence_reason;
  if (!confidenceReason) {
    const percent = fallbackPercent();
    const score = percent / 10;
    if (percent < 50) return { label: 'Low', color: '#EF4444', score, reason: '' };
    if (percent < 80) return { label: 'Medium', color: '#F59E0B', score, reason: '' };
    return { label: 'High', color: '#16A34A', score, reason: '' };
  }

  let reason = confidenceReason.reason;
  if (lineResults.length > 1 && meterStructure) {
    const perLineSyllables = confidenceReason.technical_details?.syllable_count;
    const totalSyllables = meterStructure.totalSyllables;
    if (perLineSyllables && totalSyllables && perLineSyllables !== totalSyllables) {
      const pattern = new RegExp(`\\b${perLineSyllables}\\s+syllables?\\b`, 'gi');
      reason = reason.replace(pattern, `${totalSyllables} syllables`);
    }
  }
  const level = LEVELS[confidenceReason.level] ?? { label: 'High', color: '#16A34A' };
  return { ...level, score: Math.min(confidenceReason.confidence, 10), reason };
}

/** Summed verse-level score per meter, highest first. */
export function rankVerseMeters(verseResults: VerseResult[]): [string, number][] {
  const meterScores: Record<string, number> = {};
  verseResults.forEach((verse) => {
    if (verse.chanda && Array.isArray(verse.chanda[0])) {
      const meterName = verse.chanda[0][0];
      const score = verse.chanda[1] || 0;
      meterScores[meterName] = (meterScores[meterName] || 0) + score;
    }
  });
  return Object.entries(meterScores).sort((a, b) => b[1] - a[1]);
}

/** Number of padas before each line, using each line's meter to size its padas. */
export function padaOffsets(lineResults: LineResult[]): number[] {
  return lineResults.map((_, index) =>
    lineResults.slice(0, index).reduce((acc, item) => {
      const syllables = item.result?.display_syllables || [];
      const lgArray = item.result?.display_lg || [];
      const validCount = syllables.filter((_, i) => lgArray[i] && lgArray[i].trim() !== '').length;
      const meterName = item.result?.display_chanda_primary?.split(' ')[0] || '';
      return acc + Math.ceil(validCount / getPadaSize(meterName));
    }, 0),
  );
}

/** The text to recite: the typed input, else OCR or file text, else the analysed lines. */
export function recitationText(result: IdentifyResponse, lineResults: LineResult[]): string {
  if (result.input?.text) return result.input.text;
  if (result.ocr_text) return result.ocr_text;
  if (result.file_text) return result.file_text;
  if (lineResults.length > 0) return lineResults.map((line) => line.line).join('\n');
  return '';
}
