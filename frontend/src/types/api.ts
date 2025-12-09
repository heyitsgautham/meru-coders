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

// Audio transcription response (text only, no analysis)
export interface AudioExtractResponse {
  success: boolean;
  text?: string;
  decoder_used?: string;
  error?: string;
}

// File info from extraction
export interface FileInfo {
  filename: string;
  file_type: 'docx' | 'txt';
  page_count: number;
  encoding?: string;
}

// File extraction response (for DOCX, TXT)
export interface FileExtractResponse {
  success: boolean;
  text?: string;
  file_info?: FileInfo;
  warnings?: string[];  // Warnings like CID encoding issues
  error?: string;
  error_code?: string;
  details?: string;
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

// Meter information from database
export interface MeterInfo {
  name?: string;
  expected_pattern?: string;
  expected_syllables?: number;
  expected_matras?: number;
  gana_notation?: string;
  meter_type?: 'vedic' | 'sama' | 'ardhasama' | 'vishama';
  yati?: string;
  padas?: Record<string, {
    pattern: string;
    syllables: number;
    matras: number;
    gana: string;
  }>;
}

// Pattern validation result
export interface PatternValidation {
  is_valid?: boolean | null;
  expected_pattern?: string | null;
  actual_pattern?: string | null;
  match_percentage?: number | null;
  mismatches?: Array<[number | string, string, string]>;
}

// Confidence reason from backend
export interface ConfidenceReason {
  match_type: string;
  confidence: number;
  level: 'very_high' | 'high' | 'medium' | 'low' | 'very_low';
  reason: string;
  technical_details?: {
    match_type_raw?: string;
    base_match_type?: string;
    base_score?: number;
    description?: string;
    pattern?: string;
    pattern_length?: number;
    syllable_count?: number;
    num_padas?: number;
    syllables_per_pada?: number;
    similarity_percentage?: number;
    levenshtein_distance?: number;
    vedic_range?: { low: number; high: number };
    vedic_peak?: number;
    distance_from_peak?: number;
    [key: string]: unknown;
  };
}

// Confidence scores map (meter_name -> [score, match_type])
export type ConfidenceScores = Record<string, [number, string]>;

// Confidence reasons map (meter_name -> ConfidenceReason)
export type ConfidenceReasons = Record<string, ConfidenceReason>;

// Analysis result for a single line
export interface AnalysisResult {
  found: boolean;
  display_chanda?: string;
  display_chanda_primary?: string;
  display_syllables?: string[];
  display_lg?: string[];
  display_gana?: string;
  fuzzy?: FuzzyMatch[];
  // Validation fields for handling invalid input (e.g., English text)
  is_valid_input?: boolean;
  validation_error?: string;
  is_padya?: boolean;
  padya_reason?: string;
  prose_message?: string;
  // Pattern validation fields (new)
  meter_info?: MeterInfo | null;
  pattern_validation?: PatternValidation | null;
  // Confidence scoring fields
  confidence_scores?: ConfidenceScores;
  confidence_reasons?: ConfidenceReasons;
  primary_confidence_reason?: ConfidenceReason;
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
  effective_mode?: string;  // The actual mode used (vedic/classical) when auto-detect is chosen
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
  text_mode?: string;
  output_scheme?: string;
  identification_mode?: string;
  enable_sandhi?: boolean;
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
  identification_mode?: IdentificationMode;
  output_scheme?: string;
  enable_sandhi?: boolean;
}

export type AnalysisMode = 'line' | 'verse';

// Identification mode for Vedic vs Classical detection
export type IdentificationMode = 'auto' | 'vedic' | 'classical';

// View type for navigation
export type ViewType = 'home' | 'splitview' | 'examples' | 'datasets' | 'about' | 'community';

// Input tab type
export type InputTab = 'text' | 'image' | 'file';

// Dataset types
export interface DatasetInfo {
  id: string;
  name: string;
  description: string;
  source: string;
  sourceReference: string;
  rowCount: number;
  dataType: 'verses' | 'meter_definitions';
  hasSloka: boolean;
  slokaColumn: string | null;
  chandasColumn: string | null;
  patternColumn: string | null;
  patternType?: 'lg_pattern' | 'syllable_count' | 'matra_count';
  isMerged?: boolean;
  uniqueChandas: string[];
}

export interface DatasetsListResponse {
  success: boolean;
  datasets?: DatasetInfo[];
  sources?: string[];
  sourceDescriptions?: Record<string, string>;
  error?: string;
}

export interface DatasetRow {
  sloka: string | null;
  chandas: string | null;
  pattern: string | null;
  source: string;
  category?: string;
  raw: Record<string, string>;
}

export interface DatasetResponse {
  success: boolean;
  datasetId?: string;
  name?: string;
  description?: string;
  source?: string;
  sourceReference?: string;
  dataType?: 'verses' | 'meter_definitions';
  patternType?: 'lg_pattern' | 'syllable_count' | 'matra_count';
  columns?: string[];
  slokaColumn?: string | null;
  chandasColumn?: string | null;
  patternColumn?: string | null;
  rows?: DatasetRow[];
  totalCount?: number;
  limit?: number;
  offset?: number;
  hasMore?: boolean;
  error?: string;
}

// Sloka Search types
export interface SlokaSearchMatch {
  original_text: string;
  dataset_id: string;
  dataset_name: string;
  chandas: string;
  source: string;
  similarity: number;
  is_exact_match: boolean;
}

export interface SlokaSearchResponse {
  success: boolean;
  query?: string;
  query_normalized?: string;
  matches?: SlokaSearchMatch[];
  match_count?: number;
  has_exact_match?: boolean;
  best_similarity?: number;
  diff_hints?: string[];
  total_slokas_indexed?: number;
  error?: string;
}

export interface SlokaDifference {
  type: 'replace' | 'missing' | 'extra';
  position: number;
  end_position: number;
  your_text: string;
  correct_text: string;
  description: string;
}

export interface HighlightedSegment {
  text: string;
  isError: boolean;
}

export interface SlokaValidateResponse {
  success: boolean;
  found?: boolean;
  is_valid?: boolean;
  similarity?: number;
  similarity_percentage?: number;
  original_text?: string;
  your_text?: string;
  highlighted_segments?: HighlightedSegment[];
  chandas?: string;
  dataset_name?: string;
  source?: string;
  differences?: SlokaDifference[];
  difference_count?: number;
  message?: string;
  error?: string;
}
