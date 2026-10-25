// Building blocks shared by the image, document and voice tabs of the analysis form.
import type { CSSProperties, ReactNode, RefObject } from "react";
import { AlertTriangle, FileText, Loader2, Sparkles } from "lucide-react";
import type { DropZoneHandlers } from "../../hooks/useDropZone";

/** Orange gradient pill used for Choose File, Extract Text, Record and Stop Recording. */
export const PRIMARY_PILL =
  "px-8 py-3 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-white rounded-full hover:from-[var(--color-primary-dark)] hover:to-[#D96E12] transition-all duration-300 shadow-lg hover:shadow-xl font-semibold text-base";

const ICON_TILE = "p-6 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-primary-dark)] rounded-2xl shadow-lg";

export const EXTRACTED_TEXT_STYLE: CSSProperties = {
  fontFamily: "'Crimson Text', 'Merriweather', Georgia, 'Times New Roman', serif",
  fontSize: '25px',
  fontWeight: 400,
  color: '#4a2c10',
  lineHeight: 1.75,
  letterSpacing: '0.02em'
};

export function FieldLabel({ children }: { children: ReactNode }) {
  return (
    <label className="block text-[var(--color-text-main)] mb-3 font-semibold text-base">
      {children}
    </label>
  );
}

export function HiddenFileInput({
  inputRef,
  accept,
  onChange,
}: {
  inputRef: RefObject<HTMLInputElement>;
  accept: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) {
  return <input ref={inputRef} type="file" accept={accept} onChange={onChange} className="hidden" />;
}

/** Dashed upload area; it highlights while a file is dragged over it and opens the picker when empty. */
export function DropZoneFrame({
  isDragging,
  hasSelection,
  onClick,
  handlers,
  children,
}: {
  isDragging: boolean;
  hasSelection: boolean;
  onClick: () => void;
  handlers: DropZoneHandlers;
  children: ReactNode;
}) {
  return (
    <div
      onClick={onClick}
      onDragOver={handlers.onDragOver}
      onDragEnter={handlers.onDragEnter}
      onDragLeave={handlers.onDragLeave}
      onDrop={handlers.onDrop}
      className={`group border-2 border-dashed rounded-[20px] p-8 bg-gradient-to-b transition-all duration-300 ${isDragging
        ? 'border-[var(--color-primary)] bg-[var(--color-primary-soft)] shadow-xl scale-[1.02]'
        : hasSelection
          ? 'border-[var(--color-border-subtle)] from-white to-[#fdf8f3]'
          : 'border-[var(--color-border-subtle)] from-white to-[#fdf8f3] cursor-pointer hover:from-white hover:to-[var(--color-primary-soft)] hover:border-[var(--color-primary)] hover:shadow-xl'
        }`}
    >
      {children}
    </div>
  );
}

/** Icon tile, prompt text and actions shown in an empty drop zone. */
export function EmptyDropPrompt({
  icon,
  isDragging,
  title,
  description,
  formats,
  children,
}: {
  icon: ReactNode;
  isDragging: boolean;
  title: string;
  description: string;
  formats: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-6">
      <div className={`${ICON_TILE} transition-all duration-300 ${isDragging ? 'scale-110 shadow-xl' : 'group-hover:shadow-xl group-hover:scale-110'}`}>
        {icon}
      </div>
      <div className="text-center">
        <p className="text-lg font-semibold text-[var(--color-text-main)] mb-2">
          {title}
        </p>
        <p className="text-[var(--color-text-muted)] text-base mb-1">
          {description}
        </p>
        <p className="text-[var(--color-text-muted)] text-sm">
          {formats}
        </p>
      </div>
      {children}
    </div>
  );
}

export function ChooseFileButton({ isDragging }: { isDragging: boolean }) {
  return (
    <button className={`${PRIMARY_PILL} ${isDragging ? 'scale-105' : 'group-hover:scale-105'}`}>
      Choose File
    </button>
  );
}

/** Round red button pinned to the corner of a selected file's tile. */
export function RemoveBadge({ title, onRemove }: { title: string; onRemove: () => void }) {
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onRemove();
      }}
      className="absolute -top-3 -right-3 p-2 bg-red-500 hover:bg-red-600 rounded-full shadow-lg transition-all duration-200 hover:scale-110"
      title={title}
    >
      <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  );
}

/** Emoji tile, name and size of a selected document or recording. */
export function SelectedFileSummary({
  icon,
  name,
  size,
  removeTitle,
  onRemove,
}: {
  icon: string;
  name: string;
  size: string;
  removeTitle: string;
  onRemove: () => void;
}) {
  return (
    <>
      <div className="relative">
        <div className={ICON_TILE}>
          <span className="text-4xl">{icon}</span>
        </div>
        <RemoveBadge title={removeTitle} onRemove={onRemove} />
      </div>
      <div className="text-center">
        <p className="text-lg font-semibold text-[var(--color-text-main)] mb-1">
          {name}
        </p>
        <p className="text-sm text-[var(--color-text-muted)]">
          {size}
        </p>
      </div>
    </>
  );
}

export function ExtractButton({
  loading,
  loadingLabel,
  onExtract,
}: {
  loading: boolean;
  loadingLabel: string;
  onExtract: () => void;
}) {
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onExtract();
      }}
      disabled={loading}
      className={`${PRIMARY_PILL} disabled:opacity-50 flex items-center gap-2`}
    >
      {loading ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>{loadingLabel}</span>
        </>
      ) : (
        <>
          <FileText className="w-5 h-5" />
          <span>Extract Text</span>
        </>
      )}
    </button>
  );
}

/** Soft outlined pill that clears the selected upload once its text is extracted. */
export function ClearButton({ label, onClear }: { label: string; onClear: () => void }) {
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onClear();
      }}
      className="px-8 py-3 bg-[var(--color-primary-soft)] text-[var(--color-primary-dark)] border border-[var(--color-primary)] rounded-full hover:bg-[var(--color-primary)] hover:text-white transition-all duration-300 shadow-md hover:shadow-lg font-semibold text-base flex items-center gap-2"
    >
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
      <span>{label}</span>
    </button>
  );
}

/** Red error box; `className` sets the top margin, which differs between the tabs and the form footer. */
export function ErrorCallout({
  title,
  message,
  details,
  className = "mt-4",
}: {
  title: string;
  message: string;
  details?: string | null;
  className?: string;
}) {
  return (
    <div className={`${className} p-5 bg-red-50 border-2 border-red-200 rounded-[16px] flex items-start gap-4`}>
      <div className="p-2 bg-red-100 rounded-full">
        <AlertTriangle className="w-5 h-5 text-red-500" />
      </div>
      <div>
        <p className="font-semibold text-red-700 mb-1">{title}</p>
        <p className="text-red-600">{message}</p>
        {details && (
          <p className="text-sm text-red-500 mt-2">{details}</p>
        )}
      </div>
    </div>
  );
}

/** Bordered panel that holds extracted or transcribed text and the buttons below it. */
export function ExtractedTextPanel({ children }: { children: ReactNode }) {
  return (
    <div className="mt-8 p-8 bg-[#fdf8f3] border-2 border-[var(--color-primary)] rounded-[20px] shadow-md">
      {children}
    </div>
  );
}

export function ExtractedTextBody({ text, scrollable = false }: { text: string; scrollable?: boolean }) {
  return (
    <div
      className={`text-center mb-8 whitespace-pre-wrap p-8 bg-white rounded-[16px] border border-[var(--color-border-subtle)]${scrollable ? ' max-h-[400px] overflow-y-auto' : ''}`}
      style={EXTRACTED_TEXT_STYLE}
    >
      {text}
    </div>
  );
}

export function IdentifyChandasButton({
  loading,
  onIdentify,
  fullWidth = false,
}: {
  loading: boolean;
  onIdentify: () => void;
  fullWidth?: boolean;
}) {
  return (
    <button
      onClick={onIdentify}
      disabled={loading}
      className={`identify-btn h-[52px] px-8 text-base${fullWidth ? ' w-full' : ''}`}
    >
      {loading ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Analyzing...</span>
        </>
      ) : (
        <>
          <Sparkles className="w-5 h-5" />
          <span>Identify Chandas</span>
        </>
      )}
    </button>
  );
}
