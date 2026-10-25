import { Edit3, Image, Mic, Upload } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { IdentificationMode } from "../../types/api";
import { MODE_INFO } from "./analysisModes";
import type { InputTab } from "./analysisModes";

const TABS: { id: InputTab; label: string; Icon: LucideIcon }[] = [
  { id: "text", label: "Text Input", Icon: Edit3 },
  { id: "image", label: "Image OCR", Icon: Image },
  { id: "file", label: "File Upload", Icon: Upload },
  { id: "voice", label: "Voice Input", Icon: Mic },
];

/** The four input methods shown above the form body. */
export function InputTabBar({ active, onSelect }: { active: InputTab; onSelect: (tab: InputTab) => void }) {
  return (
    <div className="flex items-stretch gap-2.5" style={{ marginBottom: '40px' }}>
      {TABS.map(({ id, label, Icon }) => (
        <button
          key={id}
          onClick={() => onSelect(id)}
          className={`tab-button flex-1 border transition-all duration-300 ${active === id
            ? "border-[var(--color-primary)] bg-[var(--color-primary-soft)] text-[var(--color-primary-dark)] shadow-[0_0_0_1px_rgba(255,153,51,0.35)]"
            : "border-[var(--color-border-subtle)] bg-white text-[var(--color-text-main)] hover:border-[var(--color-accent-gold)] hover:bg-[var(--color-primary-soft)]"
            }`}
        >
          <Icon className="w-3.5 h-3.5" />
          <span className="text-sm font-medium">{label}</span>
        </button>
      ))}
    </div>
  );
}

/** Segmented control for the identification mode; shown on the text tab only. */
export function ModeSelector({
  mode,
  onSelect,
}: {
  mode: IdentificationMode;
  onSelect: (mode: IdentificationMode) => void;
}) {
  return (
    <div className="mt-8 flex flex-col items-center">
      <div className="inline-flex rounded-xl border-2 border-[var(--color-border-subtle)] p-1.5 bg-[#faf7f4] shadow-sm">
        {(Object.keys(MODE_INFO) as IdentificationMode[]).map((option) => (
          <button
            key={option}
            onClick={() => onSelect(option)}
            className={`px-8 py-3.5 rounded-lg text-lg font-semibold transition-all duration-200 ${mode === option
              ? "bg-white text-[var(--color-primary-dark)] shadow-md border-2 border-[var(--color-primary-light)]"
              : "text-[var(--color-text-muted)] hover:text-[var(--color-text-main)] hover:bg-white/50"
              }`}
          >
            {MODE_INFO[option].label}
          </button>
        ))}
      </div>
    </div>
  );
}
