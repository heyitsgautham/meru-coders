import { CheckCircle, GitCompare, Loader2, Mic } from "lucide-react";
import type { AudioInput } from "../../hooks/useAudioInput";
import { audioIcon, formatKilobytes } from "./inputFiles";
import { TranscriptValidation } from "./TranscriptValidation";
import {
  ChooseFileButton,
  ClearButton,
  DropZoneFrame,
  EmptyDropPrompt,
  ErrorCallout,
  ExtractButton,
  ExtractedTextBody,
  ExtractedTextPanel,
  FieldLabel,
  HiddenFileInput,
  IdentifyChandasButton,
  PRIMARY_PILL,
  SelectedFileSummary,
} from "./UploadParts";

interface VoiceTabProps {
  input: AudioInput;
  identifying: boolean;
  onIdentify: () => void;
}

const CHOICE_BUTTON = "h-[52px] px-6 text-base font-semibold rounded-full transition-all duration-300 shadow-md hover:shadow-xl flex items-center justify-center gap-3";

function RecordingPrompt({ onStop }: { onStop: () => void }) {
  return (
    <div className="flex flex-col items-center gap-6">
      <div className="p-6 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-primary-dark)] rounded-2xl shadow-lg animate-pulse">
        <Mic className="w-10 h-10 text-white" />
      </div>
      <div className="text-center">
        <p className="text-lg font-semibold text-[var(--color-primary)] mb-2">
          Recording...
        </p>
        <p className="text-[var(--color-text-muted)] text-base">
          Click Stop when finished chanting
        </p>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onStop();
        }}
        className={`${PRIMARY_PILL} flex items-center gap-2`}
      >
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <rect x="6" y="6" width="12" height="12" rx="2" />
        </svg>
        <span>Stop Recording</span>
      </button>
    </div>
  );
}

/** Voice Input tab: record or upload chanting, transcribe it, normalise it, then identify the meter. */
export function VoiceTab({ input, identifying, onIdentify }: VoiceTabProps) {
  const { audio, audioUrl, transcript, validation, dropZone } = input;

  return (
    <div className="space-y-6">
      <div>
        <FieldLabel>Record or Upload Sanskrit Chanting</FieldLabel>
        <HiddenFileInput
          inputRef={input.inputRef}
          accept=".wav,.mp3,.webm,.ogg,.m4a,.flac"
          onChange={input.onInputChange}
        />
        <DropZoneFrame
          isDragging={dropZone.isDragging}
          hasSelection={Boolean(audio)}
          onClick={() => !audio && !input.isRecording && input.inputRef.current?.click()}
          handlers={dropZone.handlers}
        >
          {audio ? (
            <div className="flex flex-col items-center gap-6">
              <SelectedFileSummary
                icon={audioIcon(audio.name)}
                name={audio.name}
                size={formatKilobytes(audio.size)}
                removeTitle="Remove audio"
                onRemove={input.remove}
              />
              {audioUrl && (
                <div className="w-full max-w-md">
                  <audio
                    controls
                    src={audioUrl}
                    className="w-full rounded-lg"
                    style={{
                      height: '40px',
                      backgroundColor: 'var(--color-bg-subtle)',
                      border: '1px solid var(--color-border-subtle)',
                      borderRadius: '8px'
                    }}
                  >
                    Your browser does not support the audio element.
                  </audio>
                </div>
              )}
              {!transcript && (
                <ExtractButton loading={input.loading} loadingLabel="Transcribing..." onExtract={input.extract} />
              )}
              {transcript && <ClearButton label="Clear Audio" onClear={input.remove} />}
            </div>
          ) : input.isRecording ? (
            <RecordingPrompt onStop={input.stopRecording} />
          ) : (
            <EmptyDropPrompt
              icon={<Mic className="w-10 h-10 text-white" />}
              isDragging={dropZone.isDragging}
              title={dropZone.isDragging ? 'Drop your audio here!' : 'Record or upload audio'}
              description="Chant a shloka and we'll identify the meter"
              formats="Supports WAV, MP3 (max 10MB)"
            >
              <div className="flex items-center gap-4">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    input.startRecording();
                  }}
                  className={`${PRIMARY_PILL} flex items-center gap-2`}
                >
                  <Mic className="w-5 h-5" />
                  <span>Record</span>
                </button>
                <span className="text-[var(--color-text-muted)]">or</span>
                <ChooseFileButton isDragging={dropZone.isDragging} />
              </div>
            </EmptyDropPrompt>
          )}
        </DropZoneFrame>
      </div>

      {input.error && <ErrorCallout title="Transcription Failed" message={input.error} />}

      {transcript && (
        <ExtractedTextPanel>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-[var(--color-text-main)]">
              Transcribed Text
            </h3>
            <span className="px-3 py-1 bg-white rounded-full border border-[var(--color-border-subtle)] text-sm text-[var(--color-text-muted)]">
              IndicConformer ASR
            </span>
          </div>

          <ExtractedTextBody text={transcript} scrollable />

          {validation && <TranscriptValidation validation={validation} />}

          <div className="flex flex-col gap-4">
            {/* Normalize or keep the transcript; hidden once a choice is made. */}
            {!validation && (
              <div className="flex items-center gap-4">
                <button
                  onClick={input.normalize}
                  disabled={input.isValidating}
                  className={`flex-1 ${CHOICE_BUTTON} bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-white hover:from-[var(--color-primary-dark)] hover:to-[#D96E12] disabled:opacity-50`}
                >
                  {input.isValidating ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Validating...</span>
                    </>
                  ) : (
                    <>
                      <GitCompare className="w-5 h-5" />
                      <span>NORMALIZE (Find Verified Sloka)</span>
                    </>
                  )}
                </button>

                <button
                  onClick={input.keepTranscript}
                  disabled={input.isValidating}
                  className={`${CHOICE_BUTTON} bg-white text-gray-700 border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-50 disabled:opacity-50`}
                >
                  <CheckCircle className="w-5 h-5" />
                  <span>USE AS-IS</span>
                </button>
              </div>
            )}

            <IdentifyChandasButton loading={identifying} onIdentify={onIdentify} fullWidth />
          </div>
        </ExtractedTextPanel>
      )}
    </div>
  );
}
