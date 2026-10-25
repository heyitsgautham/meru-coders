import type { AnalysisMode, IdentificationMode, IdentifyResponse } from '../../types/api';

/** The form always sends whole verses and keeps the input script. */
export const ANALYSIS_MODE: AnalysisMode = 'verse';
export const OUTPUT_SCRIPT = '';

export type InputTab = 'text' | 'image' | 'file' | 'voice';

export const INPUT_TABS: InputTab[] = ['text', 'image', 'file', 'voice'];

export const ACTIVE_TAB_STORAGE_KEY = 'chanda_activeTab';

export const MODE_INFO: Record<IdentificationMode, { label: string; description: string }> = {
  auto: {
    label: 'Auto Detect',
    description: 'Automatically chooses the best identification method based on text characteristics',
  },
  vedic: {
    label: 'Vedic Mode',
    description: 'Optimized for Vedic meters (Gayatri, Trishtubh, Jagati) using syllable-count detection',
  },
  classical: {
    label: 'Classical Mode',
    description: 'For classical Sanskrit meters using L-G pattern matching (Anushtubh, Vasantatilaka)',
  },
  dandaka: {
    label: 'Daṇḍaka / Stotra',
    description: 'For Daṇḍaka verses (long flowing compounds) and unmetrical Tantric Stotras like Rājaśyāmalā',
  },
};

/** Saved tab from a previous visit, falling back to the text tab for missing or unknown values. */
export function readSavedTab(storage: Pick<Storage, 'getItem'>): InputTab {
  const saved = storage.getItem(ACTIVE_TAB_STORAGE_KEY);
  return INPUT_TABS.includes(saved as InputTab) ? (saved as InputTab) : 'text';
}

/** True when the first analysed line found a meter, which is when Pingala Acharya speaks. */
export function foundMeter(response: IdentifyResponse | null | undefined): boolean {
  return Boolean(response?.success && response?.result?.line?.[0]?.result?.found);
}
