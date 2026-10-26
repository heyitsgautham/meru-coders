import type { ConfidenceDisplay } from './confidence';
import type { MeterStructureInfo } from './meterData';

interface PrimaryMeterCardProps {
  meter: string;
  englishName: string;
  meterStructure: MeterStructureInfo | null;
  confidence: ConfidenceDisplay;
}

/** The identified meter with its syllable count, confidence and the reason for that confidence. */
export function PrimaryMeterCard({ meter, englishName, meterStructure, confidence }: PrimaryMeterCardProps) {
  return (
    <div className="mb-8">
      <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-200">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
            <svg className="w-7 h-7 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <div className="flex items-baseline gap-3">
              <h3 className="text-3xl font-bold text-gray-900" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
                {meter}
              </h3>
              {englishName && englishName !== meter && (
                <span className="text-xl text-gray-600">({englishName})</span>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500 mb-1">Syllables</div>
            <div className="text-3xl font-bold text-gray-900">
              {meterStructure ? `${meterStructure.totalSyllables}` : '-'}
              {meterStructure && (
                <span className="text-lg font-normal text-gray-500 ml-2">
                  ({meterStructure.syllablesPerPada}×{meterStructure.totalPadas})
                </span>
              )}
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500 mb-1">Confidence</div>
            <div className="text-3xl font-bold" style={{ color: confidence.color }}>
              {confidence.label}
              <span className="text-lg font-normal text-gray-500 ml-2">
                ({Math.min(confidence.score, 10).toFixed(1)}/10)
              </span>
            </div>
          </div>
        </div>

        {confidence.reason && (
          <div className="mt-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100">
            <div className="flex items-start gap-5">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div className="flex-1">
                <div style={{ fontSize: '1.5rem', fontWeight: 600 }} className="text-blue-900 mb-4">Why this confidence score?</div>
                <div style={{ fontSize: '1.25rem', lineHeight: '2' }} className="text-blue-800 space-y-3">
                  {confidence.reason.split(/(?<=[.!?])\s+/).map((sentence, idx) => (
                    <p key={idx}>{sentence.trim()}</p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
