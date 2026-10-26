import { describe, expect, it } from 'vitest';
import type { IdentifyResponse, LineResult } from '../../types/api';
import { describeConfidence, padaOffsets, rankVerseMeters, recitationText } from './confidence';

function line(reason?: object, syllables = 16, lg = 16, meter = 'अनुष्टुभ्'): LineResult {
  return {
    line: 'x',
    result: {
      primary_confidence_reason: reason,
      display_syllables: Array(syllables).fill('क'),
      display_lg: Array(lg).fill('L'),
      display_chanda_primary: `${meter} [10]`,
    },
  } as unknown as LineResult;
}

const structure = { totalSyllables: 28, syllablesPerPada: 7, totalPadas: 4 } as never;

describe('describeConfidence', () => {
  it('uses the backend level and caps the score at 10', () => {
    const result = describeConfidence([line({ level: 'medium', confidence: 11, reason: 'Close.' })], null, () => 0);
    expect(result).toEqual({ label: 'Medium', color: '#F59E0B', score: 10, reason: 'Close.' });
  });

  it('reports the verse total instead of the per-line syllable count', () => {
    const reason = { level: 'high', confidence: 9, reason: 'Matches at 14 syllables.', technical_details: { syllable_count: 14 } };
    const result = describeConfidence([line(reason), line(reason)], structure, () => 0);
    expect(result.reason).toBe('Matches at 28 syllables.');
  });

  it.each([
    [40, 'Low'],
    [70, 'Medium'],
    [95, 'High'],
  ])('falls back to %i%% as %s without a backend reason', (percent, label) => {
    const result = describeConfidence([line()], null, () => percent);
    expect(result.label).toBe(label);
    expect(result.score).toBe(percent / 10);
    expect(result.reason).toBe('');
  });
});

it('rankVerseMeters sums scores per meter', () => {
  expect(
    rankVerseMeters([
      { chanda: [['गायत्री'], 2] },
      { chanda: [['त्रिष्टुभ्'], 3] },
      { chanda: [['गायत्री'], 2] },
      {},
    ]),
  ).toEqual([
    ['गायत्री', 4],
    ['त्रिष्टुभ्', 3],
  ]);
});

it('padaOffsets counts the padas of earlier lines', () => {
  expect(padaOffsets([line(), line(), line()])).toEqual([0, 2, 4]);
});

describe('recitationText', () => {
  it('prefers the typed input', () => {
    expect(recitationText({ input: { text: 'typed' }, ocr_text: 'ocr' } as IdentifyResponse, [])).toBe('typed');
  });

  it('falls back to the analysed lines', () => {
    expect(recitationText({} as IdentifyResponse, [line(), line()])).toBe('x\nx');
  });
});
