// API Service for Sanskrit Meter Identification System
// Handles all communication with the backend REST API

import type {
  SchemeOption,
  SchemesResponse,
  ExamplesResponse,
  APIInfoResponse,
  IdentifyResponse,
  AnalysisMode,
  OCREngine,
} from '../types/api';

// Get API URL from environment or use default
const getAPIBaseURL = (): string => {
  // Check for Vite environment variable
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // Check if we're in production (deployed on Cloud Run)
  if (typeof window !== 'undefined' && 
      window.location.hostname !== 'localhost' && 
      window.location.hostname !== '127.0.0.1') {
    // In production - check for runtime config
    const win = window as typeof window & { CONFIG?: { API_URL?: string } };
    if (win.CONFIG?.API_URL) {
      return win.CONFIG.API_URL;
    }
    // Fallback for production
    console.error('Production config not found! Defaulting to localhost.');
    return 'http://localhost:5000/api';
  }
  
  // Local development
  return 'http://localhost:5000/api';
};

const API_BASE_URL = getAPIBaseURL();

console.log('API Base URL:', API_BASE_URL);

/**
 * Make an API request
 */
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
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
  outputScheme: string = ''
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
      enable_sandhi: false,
    }),
  });
}

/**
 * Identify meter from image
 */
export async function identifyFromImage(
  file: File,
  ocrEngine: OCREngine = 'tesseract',
  mode: AnalysisMode = 'line',
  outputScheme: string = ''
): Promise<IdentifyResponse> {
  const formData = new FormData();
  formData.append('image_file', file);
  formData.append('ocr_engine', ocrEngine);
  formData.append('text_mode', mode);
  formData.append('output_scheme', outputScheme || '');
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
  outputScheme: string = ''
): Promise<IdentifyResponse> {
  const formData = new FormData();
  formData.append('text_file', file);
  formData.append('text_mode', mode);
  formData.append('output_scheme', outputScheme || '');
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
  return `${API_BASE_URL}/download/${filename}`;
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
