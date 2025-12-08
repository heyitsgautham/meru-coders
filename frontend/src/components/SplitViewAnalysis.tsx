import { Sparkles, Loader2, AlertTriangle } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { ScrollInput } from "./ScrollInput";
import { ResultsDisplay } from "./ResultsDisplay";
import { useAPIInfo, useIdentifyText } from "../hooks/useApi";
import type { AnalysisMode, IdentifyResponse, IdentificationMode } from "../types/api";

// Fixed analysis settings
const ANALYSIS_MODE: AnalysisMode = "verse";
const OUTPUT_SCRIPT = "";

// Mode descriptions for UI
const MODE_INFO: Record<IdentificationMode, { label: string; description: string }> = {
  auto: {
    label: "Auto Detect",
    description: "Automatically chooses the best identification method based on text characteristics"
  },
  vedic: {
    label: "Vedic Mode",
    description: "Optimized for Vedic meters (Gayatri, Trishtubh, Jagati) using syllable-count detection"
  },
  classical: {
    label: "Classical Mode",
    description: "For classical Sanskrit meters using L-G pattern matching (Anushtubh, Vasantatilaka)"
  }
};

interface SplitViewAnalysisProps {
  initialTextLeft?: string;
  initialTextRight?: string;
}

export function SplitViewAnalysis({ initialTextLeft = "", initialTextRight = "" }: SplitViewAnalysisProps) {
  const [textLeft, setTextLeft] = useState(initialTextLeft);
  const [textRight, setTextRight] = useState(initialTextRight);

  // Identification mode state
  const [identificationMode, setIdentificationMode] = useState<IdentificationMode>("auto");

  // Results state
  const [resultLeft, setResultLeft] = useState<IdentifyResponse | null>(null);
  const [resultRight, setResultRight] = useState<IdentifyResponse | null>(null);

  // Refs for scroll to results
  const resultsRef = useRef<HTMLDivElement>(null);

  // API hooks - separate hooks for left and right to track loading independently
  const { connected } = useAPIInfo();
  const { loading: textLoadingLeft, error: textErrorLeft, identify: identifyTextLeft } = useIdentifyText();
  const { loading: textLoadingRight, error: textErrorRight, identify: identifyTextRight } = useIdentifyText();

  const isLoading = textLoadingLeft || textLoadingRight;
  const error = textErrorLeft || textErrorRight;

  // Scroll to results when they appear
  useEffect(() => {
    if ((resultLeft || resultRight) && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [resultLeft, resultRight]);

  // Sync text with parent when initialText changes
  useEffect(() => {
    if (initialTextLeft) {
      setTextLeft(initialTextLeft);
    }
  }, [initialTextLeft]);

  useEffect(() => {
    if (initialTextRight) {
      setTextRight(initialTextRight);
    }
  }, [initialTextRight]);

  // Handle form submission - analyze both texts
  const handleSubmit = async () => {
    setResultLeft(null);
    setResultRight(null);

    const hasLeftText = textLeft.trim().length > 0;
    const hasRightText = textRight.trim().length > 0;

    if (!hasLeftText && !hasRightText) {
      alert("Please enter at least one Sanskrit text");
      return;
    }

    try {
      // Run both analyses in parallel
      const promises: Promise<void>[] = [];

      if (hasLeftText) {
        promises.push(
          identifyTextLeft(textLeft, ANALYSIS_MODE, OUTPUT_SCRIPT, identificationMode)
            .then(response => setResultLeft(response))
            .catch(err => console.error("Left analysis failed:", err))
        );
      }

      if (hasRightText) {
        promises.push(
          identifyTextRight(textRight, ANALYSIS_MODE, OUTPUT_SCRIPT, identificationMode)
            .then(response => setResultRight(response))
            .catch(err => console.error("Right analysis failed:", err))
        );
      }

      await Promise.all(promises);
    } catch (err) {
      console.error("Analysis failed:", err);
    }
  };

  const handleCloseResultsLeft = () => {
    setResultLeft(null);
  };

  const handleCloseResultsRight = () => {
    setResultRight(null);
  };

  return (
    <>
      {/* Main Form Container - wider for split view */}
      <div style={{ width: '1600px', maxWidth: '95%', margin: '0 auto' }} className="animate-fadeIn">
        {/* API Connection Warning */}
        {!connected && (
          <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-[12px] flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-amber-700">Backend API not connected</p>
              <p className="text-sm text-amber-600">Make sure the backend is running at <code className="bg-amber-100 px-1 rounded">http://localhost:5000</code></p>
            </div>
          </div>
        )}

        {/* Main card */}
        <div className="main-card">
          {/* Title Block */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-3 mb-4">
              <div className="h-px w-12 bg-gradient-to-r from-transparent via-[var(--color-accent-gold)] to-[var(--color-primary)]" />
              <Sparkles className="w-4 h-4 text-[var(--color-accent-amber)]" />
              <div className="h-px w-12 bg-gradient-to-l from-transparent via-[var(--color-accent-gold)] to-[var(--color-primary)]" />
            </div>
            <h1 className="text-center mb-2">
              Compare Two Shlokas
            </h1>
            <p className="subtitle-text">
              Analyze two Sanskrit verses side by side
            </p>
          </div>

          {/* Split View Input Area */}
          <div className="flex gap-6">
            {/* Left Text Input */}
            <div className="flex-1">
              <label className="block text-[var(--color-text-main)] mb-3 font-semibold text-base text-center">
                First Shloka
              </label>
              <div className="field-group--textarea">
                <ScrollInput
                  value={textLeft}
                  onChange={setTextLeft}
                  placeholder="Type or paste your first Sanskrit shloka here…"
                />
              </div>
            </div>

            {/* Right Text Input */}
            <div className="flex-1">
              <label className="block text-[var(--color-text-main)] mb-3 font-semibold text-base text-center">
                Second Shloka
              </label>
              <div className="field-group--textarea">
                <ScrollInput
                  value={textRight}
                  onChange={setTextRight}
                  placeholder="Type or paste your second Sanskrit shloka here…"
                />
              </div>
            </div>
          </div>

          {/* Identification Mode Selector */}
          <div className="mt-8 flex flex-col items-center">
            <div className="inline-flex rounded-xl border-2 border-[var(--color-border-subtle)] p-1.5 bg-[#faf7f4] shadow-sm">
              {(Object.keys(MODE_INFO) as IdentificationMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setIdentificationMode(mode)}
                  className={`px-8 py-3.5 rounded-lg text-lg font-semibold transition-all duration-200 ${identificationMode === mode
                    ? "bg-white text-[var(--color-primary-dark)] shadow-md border-2 border-[var(--color-primary-light)]"
                    : "text-[var(--color-text-muted)] hover:text-[var(--color-text-main)] hover:bg-white/50"
                    }`}
                >
                  {MODE_INFO[mode].label}
                </button>
              ))}
            </div>
          </div>

          {/* Central Analyze Button */}
          <div className="mt-8 pt-6 border-t border-[var(--color-border-subtle)] bg-[#fdf8f3] -mx-8 px-8 py-6 -mb-8 rounded-b-[20px] flex justify-center">
            <button
              className="identify-btn h-[52px] px-12 text-lg"
              onClick={handleSubmit}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Analyzing Both...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Analyze Both Shlokas</span>
                </>
              )}
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mt-6 p-5 bg-red-50 border-2 border-red-200 rounded-[16px] flex items-start gap-4">
              <div className="p-2 bg-red-100 rounded-full">
                <AlertTriangle className="w-5 h-5 text-red-500" />
              </div>
              <div>
                <p className="font-semibold text-red-700 mb-1">Error</p>
                <p className="text-red-600">{error}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Results Display - Side by side */}
      {(resultLeft || resultRight) && (
        <div ref={resultsRef} style={{ width: '1600px', maxWidth: '95%', margin: '40px auto 0 auto' }}>
          <div className="flex gap-6">
            {/* Left Result */}
            <div className="flex-1">
              {resultLeft ? (
                <div>
                  <h3 className="text-xl font-bold text-[var(--color-text-main)] mb-4 text-center">
                    First Shloka Result
                  </h3>
                  <ResultsDisplay
                    result={resultLeft}
                    type="text"
                    onClose={handleCloseResultsLeft}
                  />
                </div>
              ) : textLeft.trim() ? (
                <div className="p-8 bg-[#fdf8f3] border border-[var(--color-border-subtle)] rounded-[20px] text-center">
                  <p className="text-[var(--color-text-muted)]">No result for first shloka</p>
                </div>
              ) : null}
            </div>

            {/* Right Result */}
            <div className="flex-1">
              {resultRight ? (
                <div>
                  <h3 className="text-xl font-bold text-[var(--color-text-main)] mb-4 text-center">
                    Second Shloka Result
                  </h3>
                  <ResultsDisplay
                    result={resultRight}
                    type="text"
                    onClose={handleCloseResultsRight}
                  />
                </div>
              ) : textRight.trim() ? (
                <div className="p-8 bg-[#fdf8f3] border border-[var(--color-border-subtle)] rounded-[20px] text-center">
                  <p className="text-[var(--color-text-muted)]">No result for second shloka</p>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
