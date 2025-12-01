// API Types for Sanskrit Meter Identification System

// Scheme option for transliteration
export interface SchemeOption {
  value: string;
  label: string;
}

// Example verse from API
export interface Example {
  meter: string;
  lines: string[];
  text?: string;
}

// OCR availability info
export interface OCRAvailability {
  tesseract: boolean;
  cloud_vision: boolean;
}

// OCR Extract response (text only, no analysis)
export interface OCRExtractResponse {
  success: boolean;
  text?: string;
  error?: string;
}

// API Info response
export interface APIInfoResponse {
  success: boolean;
  name?: string;
  version?: string;
  ocr_available?: OCRAvailability;
}

// Schemes response
export interface SchemesResponse {
  success: boolean;
  schemes?: SchemeOption[];
  error?: string;
}

// Examples response
export interface ExamplesResponse {
  success: boolean;
  examples?: Example[];
  error?: string;
}

// Fuzzy match result
export interface FuzzyMatch {
  display_chanda: string;
  similarity: number;
}

// Analysis result for a single line
export interface AnalysisResult {
  found: boolean;
  display_chanda?: string;
  display_chanda_primary?: string;
  display_syllables?: string[];
  display_lg?: string[];
  display_gana?: string;
  fuzzy?: FuzzyMatch[];
}

// Line result item
export interface LineResult {
  line: string;
  result: AnalysisResult;
}

// Verse result item
export interface VerseResult {
  verse?: string[];
  chanda?: [string[], number];
}

// Result container
export interface MeterResult {
  line?: LineResult[];
  verse?: VerseResult[];
}

// Summary count
export interface SummaryCount {
  line?: number;
  match_line?: number;
}

// Summary line match
export interface SummaryLineMatch {
  chanda?: Record<string, number>;
}

// Summary line
export interface SummaryLine {
  match?: SummaryLineMatch;
}

// Summary object
export interface Summary {
  count?: SummaryCount;
  line?: SummaryLine;
}

// Input info
export interface InputInfo {
  text?: string;
  mode?: string;
  output_scheme?: string;
}

// Identification response (text, image, file)
export interface IdentifyResponse {
  success: boolean;
  result?: MeterResult;
  result_path?: string;
  summary?: Summary;
  summary_formatted?: string;
  input?: InputInfo;
  ocr_text?: string;
  file_text?: string;
  error?: string;
}

// API request types
export interface IdentifyTextRequest {
  text: string;
  mode?: 'line' | 'verse';
  output_scheme?: string;
  enable_sandhi?: boolean;
}

export type AnalysisMode = 'line' | 'verse';

// View type for navigation
export type ViewType = 'home' | 'examples' | 'about';

// Input tab type
export type InputTab = 'text' | 'image' | 'file';
