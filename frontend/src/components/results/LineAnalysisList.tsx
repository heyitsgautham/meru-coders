import type { ReactNode } from 'react';
import type { LineResult } from '../../types/api';
import { padaOffsets } from './confidence';
import { LineAnalysisCard } from './LineAnalysisCard';

/** The script toggle and one analysis card per line, with pada numbering that runs across lines. */
export function LineAnalysisCards({ lineResults, showSanskrit }: { lineResults: LineResult[]; showSanskrit: boolean }) {
  const offsets = padaOffsets(lineResults);
  return (
    <div className="space-y-6">
      {lineResults.map((lineItem, index) => (
        <LineAnalysisCard key={index} lineItem={lineItem} showSanskrit={showSanskrit} padaOffset={offsets[index]} />
      ))}
    </div>
  );
}

export function ScriptToggle({ showSanskrit, onToggle }: { showSanskrit: boolean; onToggle: () => void }) {
  return (
    <button onClick={onToggle} className="language-toggle-btn">
      {showSanskrit ? 'Show IAST (English)' : 'Show Devanagari'}
    </button>
  );
}

/** Line analysis under a verse result: a grey heading bar, then the cards. */
export function PadaDetails({ children }: { children: ReactNode }) {
  return (
    <div className="mt-6">
      <h3 className="font-semibold text-gray-700 p-4 bg-gray-100 rounded-xl mb-4">
        Line-by-Line Analysis (Pāda Details)
      </h3>
      <div className="bg-gray-50 p-8 rounded-2xl border-2 border-gray-200">{children}</div>
    </div>
  );
}
