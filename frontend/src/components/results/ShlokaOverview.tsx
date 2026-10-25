/**
 * Colored laghu/guru syllable overview of a verse.
 */

import type { LineResult } from '../../types/api';

// Shloka Overview Component - Shows colored syllables at a glance
// Blue = Laghu (ल/L), Red/Pink = Guru (ग/G)
export function ShlokaOverview({ lineResults }: { lineResults: LineResult[] }) {
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
