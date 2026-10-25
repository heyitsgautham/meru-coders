/**
 * Per-line pada table: akṣaras, laghu-guru marks and gaṇas.
 */

import type { LineResult } from '../../types/api';
import { GANA_MAP, GANA_INFO, transliterateToIAST, getPadaSize, splitIntoPadas } from './meterData';

// Line Analysis Card Component
export function LineAnalysisCard({
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
