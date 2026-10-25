import { Sparkles, Loader2, AlertTriangle } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { ScrollInput } from "./ScrollInput";
import { ResultsDisplay } from "./ResultsDisplay";
import { DandakaResultsDisplay } from "./DandakaResultsDisplay";
import { PingalaAcharyaSpeaker } from "./PingalaAcharyaSpeaker";
import { ImageTab } from "./analysis/ImageTab";
import { DocumentTab } from "./analysis/DocumentTab";
import { VoiceTab } from "./analysis/VoiceTab";
import { InputTabBar, ModeSelector } from "./analysis/InputTabBar";
import { ErrorCallout } from "./analysis/UploadParts";
import {
  ACTIVE_TAB_STORAGE_KEY,
  ANALYSIS_MODE,
  OUTPUT_SCRIPT,
  foundMeter,
  readSavedTab,
} from "./analysis/analysisModes";
import type { InputTab } from "./analysis/analysisModes";
import { useAPIInfo, useIdentifyText } from "../hooks/useApi";
import { useImageInput } from "../hooks/useImageInput";
import { useDocumentInput } from "../hooks/useDocumentInput";
import { useAudioInput } from "../hooks/useAudioInput";
import { identifyDandaka } from "../services/api";
import type { DandakaModeResult, IdentifyResponse, IdentificationMode } from "../types/api";

interface AnalysisFormProps {
  initialText?: string;
  initialMode?: string;
  onTextChange?: (text: string) => void;
  autoIdentify?: boolean;
}

/**
 * The analysis screen: four ways to get Sanskrit text in (typing, image OCR,
 * document upload, voice) and one results panel for the identified meter.
 * Each upload tab owns its state through a hook in src/hooks/; this component
 * owns the text, the identification mode and the result.
 */
export function AnalysisForm({ initialText = "", initialMode, onTextChange, autoIdentify = false }: AnalysisFormProps) {
  const [text, setText] = useState(initialText);
  const [activeTab, setActiveTab] = useState<InputTab>(() => readSavedTab(localStorage));
  const [identificationMode, setIdentificationMode] = useState<IdentificationMode>(
    (initialMode as IdentificationMode) || "auto"
  );
  const [result, setResult] = useState<IdentifyResponse | null>(null);
  const [showPingala, setShowPingala] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  const { connected } = useAPIInfo();
  const { loading: textLoading, error: textError, identify: identifyText } = useIdentifyText();
  const imageInput = useImageInput();
  const documentInput = useDocumentInput();
  const audioInput = useAudioInput();

  const error = textError || imageInput.error || documentInput.error || audioInput.error;

  useEffect(() => {
    localStorage.setItem(ACTIVE_TAB_STORAGE_KEY, activeTab);
  }, [activeTab]);

  // Scroll to results when they appear
  useEffect(() => {
    if (result && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [result]);

  // A verse picked from Examples or a chatbot link replaces the text and opens the text tab.
  useEffect(() => {
    if (initialText) {
      setText(initialText);
      setActiveTab("text");
    }
  }, [initialText]);

  // Identify automatically when the parent asks for it, after the text has rendered.
  useEffect(() => {
    if (autoIdentify && text.trim() && activeTab === "text") {
      const timer = setTimeout(() => {
        handleSubmit();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [autoIdentify, text, activeTab]);

  const handleTextChange = (newText: string) => {
    setText(newText);
    onTextChange?.(newText);
  };

  const selectTab = (tab: InputTab) => {
    setActiveTab(tab);
    setResult(null);
  };

  const showResult = (response: IdentifyResponse, announce: boolean) => {
    setResult(response);
    if (announce && foundMeter(response)) {
      setShowPingala(true);
    }
  };

  // Move text extracted on another tab into the text tab and identify it there.
  const identifyExtracted = async (extracted: string | null, mode: IdentificationMode) => {
    if (!extracted) return;
    setText(extracted);
    setActiveTab("text");
    setResult(null);
    try {
      showResult(await identifyText(extracted, ANALYSIS_MODE, OUTPUT_SCRIPT, mode), true);
    } catch (err) {
      console.error("Analysis failed:", err);
    }
  };

  // Identify the typed text; the upload tabs identify through identifyExtracted instead.
  const handleSubmit = async () => {
    setResult(null);
    if (!text.trim()) {
      alert("Please enter some Sanskrit text");
      return;
    }
    try {
      const response = identificationMode === 'dandaka'
        ? await identifyDandaka(text)
        : await identifyText(text, ANALYSIS_MODE, OUTPUT_SCRIPT, identificationMode);
      // Pingala Acharya does not narrate Daṇḍaka results.
      showResult(response, identificationMode !== 'dandaka');
    } catch (err) {
      console.error("Analysis failed:", err);
    }
  };

  return (
    <>
      {/* Main Form Container - constrained to 900px and centered */}
      <div style={{ width: '900px', maxWidth: '100%', margin: '0 auto' }} className="animate-fadeIn">
        {!connected && (
          <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-[12px] flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-amber-700">Backend API not connected</p>
              <p className="text-sm text-amber-600">Make sure the backend is running at <code className="bg-amber-100 px-1 rounded">http://localhost:5000</code></p>
            </div>
          </div>
        )}

        <div className="main-card">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-3 mb-4">
              <div className="h-px w-12 bg-gradient-to-r from-transparent via-[var(--color-accent-gold)] to-[var(--color-primary)]" />
              <Sparkles className="w-4 h-4 text-[var(--color-accent-amber)]" />
              <div className="h-px w-12 bg-gradient-to-l from-transparent via-[var(--color-accent-gold)] to-[var(--color-primary)]" />
            </div>
            <h1 className="text-center mb-2">
              Analyze Sanskrit Text
            </h1>
            <p className="subtitle-text">
              Choose your input method and identify the meter
            </p>
          </div>

          <InputTabBar active={activeTab} onSelect={selectTab} />

          <div className="field-group--textarea">
            {activeTab === "text" && (
              <div>
                <ScrollInput
                  value={text}
                  onChange={handleTextChange}
                  placeholder="Type or paste your Sanskrit shloka here…"
                />
              </div>
            )}
            {activeTab === "image" && (
              <ImageTab
                input={imageInput}
                identifying={textLoading}
                onIdentify={() => identifyExtracted(imageInput.extractedText, identificationMode)}
              />
            )}
            {activeTab === "file" && (
              <DocumentTab
                input={documentInput}
                identifying={textLoading}
                onIdentify={() => identifyExtracted(documentInput.extractedText, "auto")}
              />
            )}
            {activeTab === "voice" && (
              <VoiceTab
                input={audioInput}
                identifying={textLoading}
                onIdentify={() => identifyExtracted(audioInput.transcript, identificationMode)}
              />
            )}
          </div>

          {activeTab === "text" && (
            <>
              <ModeSelector mode={identificationMode} onSelect={setIdentificationMode} />
              <div className="mt-8 pt-6 border-t border-[var(--color-border-subtle)] bg-[#fdf8f3] -mx-8 px-8 py-6 -mb-8 rounded-b-[20px] flex justify-center">
                <button
                  className="identify-btn h-[52px] px-8 text-base"
                  onClick={handleSubmit}
                  disabled={textLoading}
                >
                  {textLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      <span>Identify Chanda</span>
                    </>
                  )}
                </button>
              </div>
            </>
          )}

          {error && <ErrorCallout title="Error" message={error} className="mt-6" />}
        </div>
      </div>

      {/* Results sit outside the 900px card so they can use up to 1400px. */}
      {result && activeTab === "text" && (
        <div ref={resultsRef} style={{ width: '1400px', maxWidth: '100%', margin: '40px auto 0 auto' }}>
          {identificationMode === 'dandaka' && result.result ? (
            // identifyDandaka() returns the dandaka endpoint's payload in `result`
            <DandakaResultsDisplay result={result.result as unknown as DandakaModeResult} />
          ) : (
            <ResultsDisplay
              result={result}
              type="text"
              onClose={() => setResult(null)}
            />
          )}
        </div>
      )}

      {showPingala && result && activeTab === "text" && (
        <PingalaAcharyaSpeaker
          result={result}
          onClose={() => setShowPingala(false)}
        />
      )}
    </>
  );
}
