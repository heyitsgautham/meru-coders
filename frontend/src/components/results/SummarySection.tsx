/**
 * Summary statistics panel of ResultsDisplay.
 */

import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { Summary } from '../../types/api';
import { getMeterEnglish } from './meterData';

// Summary Section Component
export function SummarySection({ summary }: { summary: Summary }) {
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
