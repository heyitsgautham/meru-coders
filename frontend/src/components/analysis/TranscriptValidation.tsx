import { AlertTriangle, CheckCircle, GitCompare } from "lucide-react";
import type { ReactNode } from "react";
import type { SlokaValidateResponse } from "../../types/api";
import { NORMALIZE_MIN_SIMILARITY } from "../../hooks/useAudioInput";

function Notice({ tone, icon, title, children }: { tone: string; icon: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className={`mb-6 p-6 rounded-xl border-2 ${tone}`}>
      <div className="flex items-start gap-3">
        {icon}
        <div className="flex-1">
          <h4 className="font-bold text-lg mb-2 text-gray-800">
            {title}
          </h4>
          {children}
        </div>
      </div>
    </div>
  );
}

/** Outcome of matching a transcript against the verified verse database. */
export function TranscriptValidation({ validation }: { validation: SlokaValidateResponse }) {
  if (!validation.found) {
    return (
      <Notice
        tone="bg-blue-50 border-blue-300"
        icon={<AlertTriangle className="w-6 h-6 text-blue-600 mt-1" />}
        title="No Match Found"
      >
        <p className="text-sm text-gray-700">
          This verse was not found in our database. Using your transcribed text as-is.
        </p>
      </Notice>
    );
  }

  if (!validation.similarity) return null;

  if (validation.similarity < NORMALIZE_MIN_SIMILARITY) {
    return (
      <Notice
        tone="bg-red-50 border-red-300"
        icon={<AlertTriangle className="w-6 h-6 text-red-600 mt-1" />}
        title="Similarity Too Low"
      >
        <p className="text-sm text-gray-700 mb-2">
          Found a match with {validation.similarity_percentage?.toFixed(1)}% similarity, but requires at least 90% to normalize.
        </p>
        <p className="text-sm text-gray-600 italic">
          Using your original transcribed text as-is.
        </p>
      </Notice>
    );
  }

  return (
    <Notice
      tone={validation.is_valid ? 'bg-green-50 border-green-300' : 'bg-yellow-50 border-yellow-300'}
      icon={
        validation.is_valid ? (
          <CheckCircle className="w-6 h-6 text-green-600 mt-1" />
        ) : (
          <GitCompare className="w-6 h-6 text-yellow-600 mt-1" />
        )
      }
      title={validation.is_valid ? 'Perfect Match! ✓' : 'Normalised'}
    >
      {!validation.is_valid && (
        <>
          <p className="text-sm text-gray-700 mb-3">
            Text has been normalized
          </p>
          {validation.difference_count && validation.difference_count > 0 && (
            <p className="text-sm text-gray-600 italic">
              {validation.difference_count} difference{validation.difference_count > 1 ? 's' : ''} corrected
            </p>
          )}
        </>
      )}
    </Notice>
  );
}
