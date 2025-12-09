// API Service for Sanskrit Meter Identification System
// Handles all communication with the backend REST API

import type {
  SchemeOption,
  SchemesResponse,
  ExamplesResponse,
  APIInfoResponse,
  IdentifyResponse,
  AnalysisMode,
  IdentificationMode,
  OCRExtractResponse,
  AudioExtractResponse,
  FileExtractResponse,
  DatasetsListResponse,
  DatasetResponse,
  SlokaSearchResponse,
  SlokaValidateResponse,
} from '../types/api';

// Get API URL from environment or use default
const getAPIBaseURL = (): string => {
  // Check for Vite environment variable
  if (import.meta.env.VITE_API_URL) {
    console.log('[API] Using VITE_API_URL:', import.meta.env.VITE_API_URL);
    return import.meta.env.VITE_API_URL;
  }

  // Check if we're in a browser
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const port = window.location.port;

    console.log('[API] Detected hostname:', hostname, 'port:', port);

    // Check for runtime config first (for production/Cloud Run)
    const win = window as typeof window & { CONFIG?: { API_URL?: string } };
    if (win.CONFIG?.API_URL) {
      console.log('[API] Using runtime CONFIG:', win.CONFIG.API_URL);
      return win.CONFIG.API_URL;
    }

    // Local development - localhost or 127.0.0.1
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      const url = 'http://localhost:5000/api';
      console.log('[API] localhost detected, using:', url);
      return url;
    }

    // Any other hostname (local network IPs, custom domains, etc.)
    // Use the same hostname to reach the backend on port 5000
    const url = `http://${hostname}:5000/api`;
    console.log('[API] Network/custom host detected, using:', url);
    return url;
  }

  // SSR/Node.js fallback
  console.log('[API] SSR fallback, using localhost');
  return 'http://localhost:5000/api';
};

// Lazy-evaluated API URL - computed on first access in the browser
let _cachedAPIBaseURL: string | null = null;

export const getAPIURL = (): string => {
  if (_cachedAPIBaseURL === null) {
    _cachedAPIBaseURL = getAPIBaseURL();
    console.log('[API] Computed API URL:', _cachedAPIBaseURL);
  }
  return _cachedAPIBaseURL;
};

// DEPRECATED: Use getAPIURL() instead - this is only for logging
// API_BASE_URL is kept for backward compat but should not be used for requests
export const API_BASE_URL = 'DYNAMIC'; // Placeholder - actual URL computed at runtime via getAPIURL()

// Get base URL without /api suffix for constructing full URLs  
const getServerURL = () => getAPIURL().replace(/\/api$/, '');

/**
 * Make an API request
 */
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  // Always get fresh URL at runtime
  const baseUrl = getAPIURL();
  const url = `${baseUrl}${endpoint}`;

  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('authToken') : null;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Request failed');
    }

    return data as T;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

/**
 * Identify meter from text
 */
export async function identifyFromText(
  text: string,
  mode: AnalysisMode = 'line',
  outputScheme: string = '',
  identificationMode: IdentificationMode = 'auto'
): Promise<IdentifyResponse> {
  return request<IdentifyResponse>('/identify/text', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      text_mode: mode,
      output_scheme: outputScheme || null,
      identification_mode: identificationMode,
      enable_sandhi: false,
    }),
  });
}

/**
 * Identify Dandaka verses and Rajashyamala Stotram
 */
export async function identifyDandaka(text: string): Promise<IdentifyResponse> {
  return request<IdentifyResponse>('/identify/dandaka', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
    }),
  });
}

/**
 * Extract text from image using OCR (no meter analysis)
 */
export async function extractTextFromImage(file: File): Promise<OCRExtractResponse> {
  const formData = new FormData();
  formData.append('image_file', file);

  return request<OCRExtractResponse>('/ocr/extract', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Extract text from document file (DOCX, TXT) - no meter analysis
 */
export async function extractTextFromFile(file: File): Promise<FileExtractResponse> {
  const formData = new FormData();
  formData.append('file', file);

  return request<FileExtractResponse>('/file/extract', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Extract text from audio using IndicConformer ASR (no meter analysis)
 */
export async function extractTextFromAudio(file: File): Promise<AudioExtractResponse> {
  const formData = new FormData();
  formData.append('audio_file', file);

  return request<AudioExtractResponse>('/audio/transcribe', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Identify meter from image (OCR + analysis in one step)
 */
export async function identifyFromImage(
  file: File,
  mode: AnalysisMode = 'line',
  outputScheme: string = '',
  identificationMode: IdentificationMode = 'auto'
): Promise<IdentifyResponse> {
  const formData = new FormData();
  formData.append('image_file', file);
  formData.append('text_mode', mode);
  formData.append('output_scheme', outputScheme || '');
  formData.append('identification_mode', identificationMode);
  formData.append('enable_sandhi', 'false');

  return request<IdentifyResponse>('/identify/image', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Identify meter from file
 */
export async function identifyFromFile(
  file: File,
  mode: AnalysisMode = 'line',
  outputScheme: string = '',
  identificationMode: IdentificationMode = 'auto'
): Promise<IdentifyResponse> {
  const formData = new FormData();
  formData.append('text_file', file);
  formData.append('text_mode', mode);
  formData.append('output_scheme', outputScheme || '');
  formData.append('identification_mode', identificationMode);
  formData.append('enable_sandhi', 'false');

  return request<IdentifyResponse>('/identify/file', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Get available transliteration schemes
 */
export async function getSchemes(): Promise<SchemesResponse> {
  return request<SchemesResponse>('/schemes');
}

/**
 * Get example verses
 */
export async function getExamples(): Promise<ExamplesResponse> {
  return request<ExamplesResponse>('/examples');
}

/**
 * Get API info
 */
export async function getAPIInfo(): Promise<APIInfoResponse> {
  return request<APIInfoResponse>('/info');
}

/**
 * Get download URL for result file
 */
export function getDownloadURL(filename: string): string {
  return `${getAPIURL()}/download/${filename}`;
}

/**
 * Default schemes if API fails
 */
export function getDefaultSchemes(): SchemeOption[] {
  return [
    { value: '', label: 'Match Input' },
    { value: 'devanagari', label: 'Devanagari (देवनागरी)' },
    { value: 'iast', label: 'IAST (International)' },
    { value: 'itrans', label: 'ITRANS' },
    { value: 'velthuis', label: 'Velthuis' },
    { value: 'slp1', label: 'SLP1' },
    { value: 'wx', label: 'WX Notation' },
  ];
}

/**
 * Get list of available datasets
 */
export async function getDatasets(): Promise<DatasetsListResponse> {
  return request<DatasetsListResponse>('/datasets');
}

/**
 * Get dataset contents with pagination and filtering
 */
export async function getDataset(
  datasetId: string,
  options: {
    limit?: number;
    offset?: number;
    chandas?: string;
  } = {}
): Promise<DatasetResponse> {
  const params = new URLSearchParams();
  if (options.limit) params.set('limit', options.limit.toString());
  if (options.offset) params.set('offset', options.offset.toString());
  if (options.chandas) params.set('chandas', options.chandas);

  const queryString = params.toString();
  const endpoint = `/datasets/${datasetId}${queryString ? `?${queryString}` : ''}`;

  return request<DatasetResponse>(endpoint);
}

/**
 * Get approved user contributions for datasets page
 */
export async function getApprovedContributions(
  options: {
    limit?: number;
    offset?: number;
    type?: 'verse' | 'meter_definition';
  } = {}
): Promise<{ success: boolean; contributions: any[]; count: number; error?: string }> {
  const params = new URLSearchParams();
  if (options.limit) params.set('limit', options.limit.toString());
  if (options.offset) params.set('offset', options.offset.toString());
  if (options.type) params.set('type', options.type);

  const queryString = params.toString();
  const endpoint = `/contributions/approved${queryString ? `?${queryString}` : ''}`;

  return request(endpoint);
}

/**
 * Generate text-to-speech audio for Sanskrit text
 */
export async function generateTTS(
  text: string,
  voice: 'male' | 'female' = 'male'
): Promise<{ success: boolean; audio_url?: string; filename?: string; error?: string }> {
  const response = await request<{ success: boolean; audio_url?: string; filename?: string; error?: string }>('/tts/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      voice,
    }),
  });

  // Convert relative audio URL to absolute URL
  // Backend returns: /api/tts/audio/filename.mp3
  // We need: http://hostname:5000/api/tts/audio/filename.mp3
  if (response.success && response.audio_url) {
    // Use getServerURL() (without /api) since backend URL already includes /api
    response.audio_url = `${getServerURL()}${response.audio_url}`;
    console.log('TTS Audio URL converted to:', response.audio_url);
  }

  return response;
}

/**
 * Get TTS audio URL
 */
export function getTTSAudioURL(filename: string): string {
  return `${getAPIURL()}/tts/audio/${filename}`;
}

/**
 * Get user's own contributions
 */
export async function getMyContributions(): Promise<{ success: boolean; contributions: any[]; error?: string }> {
  return request('/contributions/my-contributions');
}

/**
 * Search for a sloka in the datasets to find matches
 */
export async function searchSloka(
  text: string,
  options: {
    threshold?: number;
    limit?: number;
  } = {}
): Promise<SlokaSearchResponse> {
  return request<SlokaSearchResponse>('/sloka/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      threshold: options.threshold ?? 0.7,
      limit: options.limit ?? 10,
    }),
  });
}

/**
 * Validate a sloka and get detailed difference analysis
 */
export async function validateSloka(text: string): Promise<SlokaValidateResponse> {
  return request<SlokaValidateResponse>('/sloka/validate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });
}
